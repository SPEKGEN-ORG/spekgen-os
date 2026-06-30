#!/usr/bin/env python3
"""f24_followup_metrics.py — Monitor de desempeño de los follow-ups de re-engagement de Ferre24.

Mide, por ETAPA y VARIANTE de mensaje de seguimiento:
  - sent          : cuántas veces se envió ese mensaje (outbound que matchea la firma)
  - seen          : cuántos quedaron en "read" (visto azul de WhatsApp) → SEEN RATE
  - replied       : a cuántos el cliente respondió DESPUÉS del follow-up → REPLY RATE
  - reactivated   : contactos distintos que estaban callados y volvieron a escribir tras un follow-up

Base para el A/B test de plantillas: compara variantes vieja vs nueva por su reply rate real.

Japan-proof: sólo stdlib (urllib/smtplib), corre en GitHub Actions. Token GHL de F24_GHL_API_KEY
(secret en CI) o GHL_API_KEY, o --env-file <ruta .env>. Output: JSON + HTML dashboard (+ email opcional).

Uso:
  python3 metrics/f24_followup_metrics.py
  python3 metrics/f24_followup_metrics.py --days 30 --out metrics/out --email
  python3 metrics/f24_followup_metrics.py --env-file "/ruta/F24- FERRE24/.env"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import smtplib
import sys
import urllib.error
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GHL_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"
LOCATION_ID = "HNuSoIl2aCXP2DXEdMVZ"  # Ferre24
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")  # anti Cloudflare 1010

REPLY_WINDOW_DAYS = 7  # ventana tras un follow-up para contar una respuesta como reactivación

# Firmas de cada mensaje de seguimiento. Matcheamos por substring estable. Incluye copy VIEJO y NUEVO
# (post v2.6) para no perder histórico — cada variante se etiqueta para el A/B. stage = etapa del ladder.
SIGNATURES = [
    # Etapa 2 (2h, fase libre)
    ("etapa2", "2h·v_old_A", "¿Te quedó alguna duda sobre specs"),
    ("etapa2", "2h·v_old_B", "A veces la decisión no es fácil"),
    ("etapa2", "2h·v_old_C", "Por si te lo preguntas: tenemos meses"),
    ("etapa2", "2h·v_new_A", "¿Te pude ayudar con lo que buscabas"),
    ("etapa2", "2h·v_new_B", "Si estás entre varias opciones te ayudo a compararlas"),
    ("etapa2", "2h·v_new_C", "Quedé al pendiente de tu cotización"),
    # Etapa 3 (~22.5h, fase libre)
    ("etapa3", "22h·v_old_A", "quedamos a media conversación"),
    ("etapa3", "22h·v_old_B", "Quedamos a medias con tu cotización"),
    ("etapa3", "22h·v_old_C", "nos quedamos sin cerrar tu consulta"),
    ("etapa3", "22h·v_new_A", "Te escribo para retomar"),
    ("etapa3", "22h·v_new_B", "No quise dejarte sin respuesta"),
    ("etapa3", "22h·v_new_C", "¿Cómo vas con lo del equipo que platicamos"),
    # Plantillas Meta (post-24h)
    ("d3", "d3·plantilla", "Quedó pendiente tu consulta con Ferre24"),
    ("d8", "d8·plantilla", "Por si no lo viste cuando platicamos"),
    ("d18", "d18·plantilla", "ha pasado un tiempo desde tu última consulta"),
]
STAGE_ORDER = ["etapa2", "etapa3", "d3", "d8", "d18"]


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _read_env_file(path: str, key: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None


def get_token(env_file: str | None) -> str:
    tok = os.environ.get("F24_GHL_API_KEY") or os.environ.get("GHL_API_KEY")
    if not tok and env_file:
        tok = _read_env_file(env_file, "GHL_API_KEY")
    if not tok:
        log("ERROR: falta el token GHL (F24_GHL_API_KEY / GHL_API_KEY / --env-file).")
        sys.exit(2)
    return tok


def ghl_get(path: str, token: str, query: dict | None = None):
    url = GHL_BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Version", GHL_VERSION)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return e.code, parsed
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}


def parse_ts(val) -> float:
    """GHL devuelve dateAdded ISO (a veces epoch ms). Devuelve epoch segundos (0 si no parsea)."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val) / 1000.0 if val > 1e11 else float(val)
    s = str(val).strip()
    if s.isdigit():
        n = float(s)
        return n / 1000.0 if n > 1e11 else n
    try:
        s = s.replace("Z", "+00:00")
        return dt.datetime.fromisoformat(s).timestamp()
    except Exception:
        return 0.0


def fetch_all_conversations(token: str) -> list[dict]:
    """Pagina conversations/search por cursor (lastMessageDate descendente)."""
    out, cursor, seen_ids = [], None, set()
    for _ in range(50):  # tope duro de páginas (universo F24 es chico)
        q = {"locationId": LOCATION_ID, "limit": 100}
        if cursor:
            q["startAfterDate"] = int(cursor)
        st, data = ghl_get("/conversations/search", token, query=q)
        if st != 200:
            log(f"WARN conversations/search HTTP {st}: {json.dumps(data)[:200]}")
            break
        convs = data.get("conversations") or []
        fresh = [c for c in convs if c.get("id") not in seen_ids]
        if not fresh:
            break
        for c in fresh:
            seen_ids.add(c.get("id"))
        out.extend(fresh)
        if len(convs) < 100:
            break
        cursor = min(c.get("lastMessageDate") or 0 for c in fresh)
        if not cursor:
            break
    return out


def fetch_messages(token: str, conv_id: str) -> list[dict]:
    st, data = ghl_get(f"/conversations/{conv_id}/messages", token)
    if st != 200:
        return []
    msgs = (data.get("messages") or {}).get("messages") or []
    # orden ascendente por tiempo
    return sorted(msgs, key=lambda m: parse_ts(m.get("dateAdded")))


def classify(body: str):
    """Devuelve (stage, variant) si el body matchea una firma de follow-up, si no None."""
    if not body:
        return None
    for stage, variant, sig in SIGNATURES:
        if sig in body:
            return stage, variant
    return None


def analyze(token: str, days: int) -> dict:
    cutoff = dt.datetime.now(dt.timezone.utc).timestamp() - days * 86400
    convs = fetch_all_conversations(token)
    log(f"Conversaciones F24: {len(convs)}")

    # acumuladores
    by_variant: dict[str, dict] = {}
    by_stage: dict[str, dict] = {}
    reactivated_contacts: set[str] = set()
    total_followups = 0

    def slot(d, key):
        return d.setdefault(key, {"sent": 0, "seen": 0, "replied": 0})

    for conv in convs:
        conv_id = conv.get("id")
        contact_id = conv.get("contactId") or conv.get("contact_id")
        if not conv_id:
            continue
        msgs = fetch_messages(token, conv_id)
        if not msgs:
            continue
        # índice de inbounds (para detectar respuesta tras un follow-up)
        inbound_ts = [parse_ts(m.get("dateAdded")) for m in msgs
                      if m.get("direction") == "inbound" and (m.get("body") or "").strip()]
        for m in msgs:
            if m.get("direction") != "outbound":
                continue
            ts = parse_ts(m.get("dateAdded"))
            if ts < cutoff:
                continue
            hit = classify(m.get("body") or "")
            if not hit:
                continue
            stage, variant = hit
            total_followups += 1
            sv, ss = slot(by_variant, variant), slot(by_stage, stage)
            sv["sent"] += 1
            ss["sent"] += 1
            status = (m.get("status") or "").lower()
            if status == "read":
                sv["seen"] += 1
                ss["seen"] += 1
            # ¿respondió dentro de la ventana tras este follow-up?
            replied = any(ts < it <= ts + REPLY_WINDOW_DAYS * 86400 for it in inbound_ts)
            if replied:
                sv["replied"] += 1
                ss["replied"] += 1
                if contact_id:
                    reactivated_contacts.add(contact_id)

    def rate(n, d):
        return round(100.0 * n / d, 1) if d else 0.0

    def finalize(d):
        for k, v in d.items():
            v["seen_rate"] = rate(v["seen"], v["sent"])
            v["reply_rate"] = rate(v["replied"], v["sent"])
        return d

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window_days": days,
        "conversations_scanned": len(convs),
        "followups_sent": total_followups,
        "reactivated_contacts": len(reactivated_contacts),
        "by_stage": finalize(by_stage),
        "by_variant": finalize(by_variant),
    }


# ---------- Render ----------
def render_html(rep: dict) -> str:
    def rows_stage():
        out = []
        for st in STAGE_ORDER:
            v = rep["by_stage"].get(st)
            if not v:
                continue
            out.append(
                f"<tr><td>{st}</td><td>{v['sent']}</td><td>{v['seen']}</td>"
                f"<td class='pct'>{v['seen_rate']}%</td><td>{v['replied']}</td>"
                f"<td class='pct hi'>{v['reply_rate']}%</td></tr>")
        return "".join(out)

    def rows_variant():
        out = []
        # agrupa por stage para legibilidad
        for st in STAGE_ORDER:
            vs = [(k, val) for k, val in rep["by_variant"].items() if _stage_of(k) == st]
            for k, val in sorted(vs):
                tag = "nuevo" if "_new_" in k else ("viejo" if "_old_" in k else "meta")
                out.append(
                    f"<tr><td>{k} <span class='tag {tag}'>{tag}</span></td><td>{val['sent']}</td>"
                    f"<td>{val['seen']}</td><td class='pct'>{val['seen_rate']}%</td>"
                    f"<td>{val['replied']}</td><td class='pct hi'>{val['reply_rate']}%</td></tr>")
        return "".join(out)

    return f"""<!doctype html><html lang=es><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Ferre24 · Follow-up Metrics</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0e0e12;color:#e8e8ee;font-family:-apple-system,Segoe UI,Roboto,sans-serif;padding:28px}}
h1{{font-size:20px;margin:0 0 4px}}.sub{{color:#9a9aa8;font-size:13px;margin-bottom:22px}}
.kpis{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:26px}}
.kpi{{background:#16161d;border:1px solid #26263a;border-radius:12px;padding:14px 18px;min-width:150px}}
.kpi .n{{font-size:26px;font-weight:700;color:#ff7a45}}.kpi .l{{font-size:12px;color:#9a9aa8;margin-top:2px}}
h2{{font-size:14px;color:#c9c9d6;margin:24px 0 8px;text-transform:uppercase;letter-spacing:.5px}}
table{{width:100%;border-collapse:collapse;background:#16161d;border-radius:10px;overflow:hidden;font-size:13px}}
th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid #23232f}}
th{{background:#1c1c26;color:#9a9aa8;font-weight:600;font-size:11px;text-transform:uppercase}}
.pct{{font-weight:700}}.hi{{color:#5fd08a}}
.tag{{font-size:10px;padding:1px 6px;border-radius:6px;margin-left:6px}}
.tag.nuevo{{background:#1d3a26;color:#5fd08a}}.tag.viejo{{background:#3a2a1d;color:#e0a060}}.tag.meta{{background:#26263a;color:#9a9aff}}
</style></head><body>
<h1>Ferre24 · Desempeño de Follow-ups</h1>
<div class=sub>Ventana: últimos {rep['window_days']} días · generado {rep['generated_at'][:16].replace('T',' ')} UTC</div>
<div class=kpis>
<div class=kpi><div class=n>{rep['followups_sent']}</div><div class=l>Follow-ups enviados</div></div>
<div class=kpi><div class=n>{rep['reactivated_contacts']}</div><div class=l>Contactos reactivados</div></div>
<div class=kpi><div class=n>{rep['conversations_scanned']}</div><div class=l>Conversaciones escaneadas</div></div>
</div>
<h2>Por etapa</h2>
<table><tr><th>Etapa</th><th>Enviados</th><th>Vistos</th><th>Seen rate</th><th>Respondieron</th><th>Reply rate</th></tr>{rows_stage()}</table>
<h2>Por variante (A/B)</h2>
<table><tr><th>Variante</th><th>Enviados</th><th>Vistos</th><th>Seen rate</th><th>Respondieron</th><th>Reply rate</th></tr>{rows_variant()}</table>
<div class=sub style="margin-top:22px">Reply rate = % de envíos a los que el cliente respondió dentro de {REPLY_WINDOW_DAYS} días. La señal clave para el A/B: compara variantes <b>nuevo</b> vs <b>viejo</b> de la misma etapa.</div>
</body></html>"""


def _stage_of(variant_key: str) -> str:
    if variant_key.startswith("2h"):
        return "etapa2"
    if variant_key.startswith("22h"):
        return "etapa3"
    return variant_key.split("·")[0]


def send_email(html: str, rep: dict) -> None:
    user = os.environ.get("GMAIL_USER") or "gibran.alonzo0506@gmail.com"
    pw = os.environ.get("SPEKGEN_GMAIL_APP_PASSWORD") or os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("F24_METRICS_RECIPIENTS") or "gibran.alonzo0506@gmail.com"
    if not pw:
        log("Sin GMAIL_APP_PASSWORD → no se envía email (ok en local).")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (f"Ferre24 Follow-ups · {rep['reactivated_contacts']} reactivados · "
                      f"{rep['followups_sent']} enviados ({rep['window_days']}d)")
    msg["From"] = user
    msg["To"] = to
    msg.attach(MIMEText("Reporte de desempeño de follow-ups F24 (ver HTML).", "plain"))
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
            s.login(user, pw)
            s.sendmail(user, [a.strip() for a in to.split(",")], msg.as_string())
        log(f"Email enviado a {to}")
    except Exception as e:  # noqa: BLE001
        log(f"WARN no se pudo enviar email: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--out", default="metrics/out")
    ap.add_argument("--email", action="store_true")
    ap.add_argument("--env-file", default=None)
    args = ap.parse_args()

    token = get_token(args.env_file)
    rep = analyze(token, args.days)

    os.makedirs(args.out, exist_ok=True)
    stamp = rep["generated_at"][:10]
    json_path = os.path.join(args.out, f"followup_metrics_{stamp}.json")
    html_path = os.path.join(args.out, f"followup_metrics_{stamp}.html")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    html = render_html(rep)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    log(f"\n=== Ferre24 Follow-ups ({args.days}d) ===")
    log(f"Enviados: {rep['followups_sent']} · Reactivados: {rep['reactivated_contacts']}")
    for st in STAGE_ORDER:
        v = rep["by_stage"].get(st)
        if v:
            log(f"  {st:7} sent={v['sent']:3} seen={v['seen_rate']:5}% reply={v['reply_rate']:5}%")
    log(f"JSON: {json_path}\nHTML: {html_path}")

    if args.email:
        send_email(html, rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
