#!/usr/bin/env python3
"""Cerebro: redacta un BORRADOR de respuesta por cada comentario/DM pendiente.
Claude Haiku + knowledge del cliente. NO publica nada — escribe draft a social_inbox.

Reglas duras: precios/links SOLO verbatim del catálogo; si no está -> deriva a DM.
Respuestas cortas (comentario público). Español impecable. F24 = siempre borrador.

Uso:
  python3 social_brain.py --client F24            # redacta borradores de F24
  python3 social_brain.py --client all --limit 20
  python3 social_brain.py --client F24 --dry-run  # imprime, no escribe
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import secrets, store  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = "claude-haiku-4-5-20251001"
KNOWLEDGE_BUDGET = 14000  # chars
AUTO_MAX_AGE_DAYS = 45    # no auto-responder comentarios más viejos que esto
AUTO_MIN_CONFIDENCE = 0.8
AUTO_CATEGORIES = {"question", "intent"}  # solo intención clara de venta/duda

# Guardarraíl: NO auto-publicar respuestas con claims que no podemos verificar en vivo
# (precios, números, promos). Esas van a revisión humana. Auto = solo redirect-a-DM limpio.
_RISKY_RE = re.compile(
    r"\d|hot\s*sale|buen\s*fin|descuent|gratis|%|oferta|promoci|vence|hasta el|"
    r"\b\dx\d\b|3x2|2x1|bogo|cup[oó]n|env[ií]o\s+gratis",
    re.IGNORECASE,
)


def _risky_for_auto(text):
    return bool(_RISKY_RE.search(text or ""))


def load_config():
    with open(os.path.join(HERE, "clients.json")) as f:
        return json.load(f)


def resolve_path(p):
    if p.startswith("~"):
        return os.path.expanduser(p)
    if p.startswith("/"):
        return p
    return os.path.join(secrets.DRIVE, p)


def load_knowledge(path):
    full = resolve_path(path)
    if not os.path.exists(full):
        return ""
    chunks = []
    if os.path.isdir(full):
        for root, _, files in os.walk(full):
            for fn in sorted(files):
                if fn.lower().endswith((".md", ".txt", ".json")):
                    try:
                        chunks.append(open(os.path.join(root, fn)).read())
                    except Exception:
                        pass
    else:
        chunks.append(open(full).read())
    text = "\n\n".join(chunks)
    return text[:KNOWLEDGE_BUDGET]


SYSTEM_TMPL = """Eres el community manager de {name}. Respondes comentarios PÚBLICOS en \
Instagram y Facebook. Tu trabajo: contestar de forma breve, cálida y profesional, en español \
impecable (con ñ, tildes y acentos correctos).

REGLAS DURAS:
- Máximo 2 frases. Es un comentario público, no un chat largo.
- Precios, links y datos SOLO si aparecen EXACTOS en el CATÁLOGO de abajo. Cópialos verbatim. \
Si el dato NO está en el catálogo, NO lo inventes: responde amable e invita a escribir por \
mensaje directo (DM) o WhatsApp para darle el detalle.
- Para precio/compra: si tienes el dato dalo, y SIEMPRE invita a DM/WhatsApp para cerrar.
- NUNCA inventes precios, promociones, garantías ni envíos gratis.
- PROHIBIDO mencionar promociones, descuentos, "Hot Sale", Buen Fin, fechas límite o \
cualquier oferta con vigencia: pueden estar VENCIDAS. Quédate en info perenne (qué es, para \
qué sirve) + invitar a DM. Si el precio del catálogo es estable, puedes darlo; las ofertas no.
- Español de MÉXICO, trato de "tú": "escríbenos", "te interesa", "te cotizamos". \
NUNCA uses voseo ("vos", "escribís", "tenés", "querés").
- Tono de {name}. Máximo 1 emoji, opcional.
- Si es queja, reclamo o algo delicado: responde con empatía, deriva a DM, y marca needs_human=true.
- No reveles que eres un bot ni menciones "catálogo interno".

Devuelve SOLO un JSON válido, sin texto extra:
{{"action":"reply|skip|escalate","draft":"<respuesta lista para publicar>","confidence":0.0,\
"needs_human":false,"reason":"<motivo corto>"}}
- action="skip" si el comentario no amerita respuesta (spam, solo emoji que se te coló).
- action="escalate" si necesita un humano sí o sí (queja seria, caso legal).
- confidence = qué tan seguro estás de que el borrador es correcto y publicable (0 a 1).

=== CATÁLOGO / INFO DE {name} ===
{knowledge}
"""

USER_TMPL = """Comentario público en {channel}{ad}.
Autor: {author}
Texto: "{body}"

Redacta la respuesta pública."""


def call_claude(system, user, api_key):
    body = {
        "model": MODEL,
        "max_tokens": 400,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        method="POST",
        data=json.dumps(body).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.load(r)
    text = "".join(b.get("text", "") for b in resp.get("content", []))
    return _parse_json(text)


def _parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default="all")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conf = load_config()
    api_key = secrets.anthropic_key()
    if not api_key:
        sys.exit("Falta ANTHROPIC_API_KEY")

    targets = list(conf["clients"]) if args.client == "all" else [args.client.upper()]
    know_cache = {}
    done = 0

    for code in targets:
        cfg = conf["clients"].get(code)
        if not cfg:
            continue
        rows = [r for r in store.fetch(status="pending", client=code)
                if r["type"] == "comment"]   # DMs se manejan en Fase 3
        if not rows:
            continue
        if code not in know_cache:
            know_cache[code] = load_knowledge(cfg.get("knowledge", "")) if cfg.get("knowledge") else ""
        system = SYSTEM_TMPL.format(name=cfg["name"], knowledge=know_cache[code] or "(sin catálogo)")
        print(f"\n=== {code} ({cfg['name']}) — {len(rows)} pendientes ===")

        for r in rows[:args.limit]:
            ad = f" (anuncio: {r['ad_name']})" if r.get("ad_name") else ""
            user = USER_TMPL.format(channel=r["channel"], ad=ad,
                                    author=r.get("author") or "cliente", body=r.get("body") or "")
            try:
                out = call_claude(system, user, api_key)
            except Exception as e:
                print(f"  ERR {r['external_id']}: {e}")
                continue

            action = out.get("action", "reply")
            draft = (out.get("draft") or "").strip()
            conf_score = out.get("confidence")
            needs_human = out.get("needs_human", False)
            category = (r.get("meta") or {}).get("category")
            age = r.get("age_days") or 0

            # ¿califica para auto-publicar? (delegación con guardarraíles)
            auto = (
                cfg.get("comment_mode") == "auto"
                and action == "reply" and draft
                and (conf_score or 0) >= AUTO_MIN_CONFIDENCE
                and not needs_human
                and category in AUTO_CATEGORIES
                and age <= AUTO_MAX_AGE_DAYS
                and not _risky_for_auto(draft)   # sin precios/promos/números sin verificar
            )
            if action == "reply":
                status = "approved" if auto else "drafted"
            else:
                status = {"skip": "skipped", "escalate": "escalated"}.get(action, "drafted")

            tag = "AUTO→publica" if auto else ("revisar" if status == "drafted" else status)
            print(f"  [{tag}] {(r.get('body') or '')[:38]!r}  (conf={conf_score}, cat={category}, {age}d)")
            print(f"      -> {draft!r}")

            if args.dry_run:
                continue

            store.update(r["external_id"], {
                "draft": draft if action == "reply" else None,
                "confidence": conf_score,
                "status": status,
                "acted_by": "auto" if auto else None,
                "meta": {**(r.get("meta") or {}),
                         "needs_human": needs_human,
                         "brain_reason": out.get("reason")},
            })
            done += 1

    print(f"\nBorradores escritos: {done}" + ("  [DRY-RUN]" if args.dry_run else ""))


if __name__ == "__main__":
    main()
