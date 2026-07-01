#!/usr/bin/env python3
"""Digest diario por email: comentarios/DMs sin atender en IG/FB (status=pending o drafted).
Agrupa por cliente, ordena por antiguedad. En Fase 2 incluira borradores + links de aprobar.

Uso:
  python3 social_digest.py            # envia el digest a digest_email
  python3 social_digest.py --test     # imprime HTML a stdout, NO envia
  python3 social_digest.py --to x@y   # override destinatario
"""
import argparse
import datetime
import hashlib
import hmac
import html
import json
import os
import smtplib
import sys
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import secrets, store  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SMTP_HOST, SMTP_PORT, SMTP_USER = "smtp.gmail.com", 587, "spekgen.ai@gmail.com"

CHANNEL_LABEL = {
    "ad_comment": "Comentario en ANUNCIO", "fb_comment": "Comentario FB",
    "ig_comment": "Comentario IG", "ig_dm": "DM Instagram", "fb_dm": "DM Messenger",
}
CATEGORY_LABEL = {
    "question": "Pregunta", "intent": "Intención de compra",
    "complaint": "Queja", "other": "Revisar", "dm": "Mensaje directo",
}


def load_config():
    with open(os.path.join(HERE, "clients.json")) as f:
        return json.load(f)


def build_html(by_client, conf):
    today = datetime.date.today().isoformat()
    total = sum(len(v) for v in by_client.values())
    css = """
    body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e8e8ec;margin:0;padding:24px}
    .wrap{max-width:680px;margin:0 auto}
    h1{font-size:20px;margin:0 0 4px} .sub{color:#9aa0aa;font-size:13px;margin-bottom:24px}
    .client{background:#171a21;border:1px solid #232733;border-radius:12px;padding:16px 18px;margin-bottom:16px}
    .client h2{font-size:15px;margin:0 0 12px;color:#fff}
    .badge{display:inline-block;background:#2a2f3a;color:#cbd2e0;border-radius:20px;padding:2px 10px;font-size:12px;margin-left:6px}
    .item{border-top:1px solid #232733;padding:12px 0}
    .meta{font-size:12px;color:#8b92a0;margin-bottom:4px}
    .age{color:#ff8a8a;font-weight:600}
    .body{font-size:14px;color:#f1f3f8;margin:2px 0 6px}
    .draft{background:#10241a;border-left:3px solid #2ecc71;padding:8px 10px;border-radius:4px;font-size:13px;color:#cfeede;margin:6px 0}
    a.btn{display:inline-block;font-size:12px;text-decoration:none;border-radius:6px;padding:6px 12px;margin-right:8px}
    a.ok{background:#2ecc71;color:#062} a.skip{background:#2a2f3a;color:#cbd2e0}
    a.link{color:#7aa2ff;font-size:12px;text-decoration:none}
    .empty{color:#9aa0aa;font-size:14px}
    .foot{color:#6b7280;font-size:11px;margin-top:20px;text-align:center}
    """
    rows = [f'<div class="wrap"><h1>SPEKGEN · Bandeja social</h1>'
            f'<div class="sub">{today} — {total} pendientes en IG/FB (DMs + comentarios)</div>']
    if total == 0:
        rows.append('<div class="client"><div class="empty">Todo atendido. Sin pendientes hoy.</div></div>')
    for code, items in by_client.items():
        if not items:
            continue
        name = conf["clients"].get(code, {}).get("name", code)
        rows.append(f'<div class="client"><h2>{html.escape(name)} <span class="badge">{len(items)}</span></h2>')
        for it in items:
            ch = CHANNEL_LABEL.get(it["channel"], it["channel"])
            cat = (it.get("meta") or {}).get("category")
            cat_txt = f'<b style="color:#7aa2ff">{CATEGORY_LABEL.get(cat, "")}</b> · ' if cat else ""
            age = it.get("age_days")
            age_txt = f'<span class="age">{age} días</span>' if age is not None else "reciente"
            who = html.escape(it.get("author") or "anónimo")
            adn = f' · {html.escape(it["ad_name"])}' if it.get("ad_name") else ""
            rows.append('<div class="item">')
            rows.append(f'<div class="meta">{cat_txt}{ch} · {who} · {age_txt}{adn}</div>')
            rows.append(f'<div class="body">{html.escape(it.get("body") or "(sin texto)")}</div>')
            if it.get("draft"):
                rows.append(f'<div class="draft"><b>Borrador:</b> {html.escape(it["draft"])}</div>')
            # links de accion (Fase 2 cablea approve/skip a Make; permalink siempre util)
            actions = []
            if it.get("approve_url"):
                actions.append(f'<a class="btn ok" href="{it["approve_url"]}">Aprobar y publicar</a>')
                actions.append(f'<a class="btn skip" href="{it["skip_url"]}">Descartar</a>')
            if it.get("permalink"):
                actions.append(f'<a class="link" href="{html.escape(it["permalink"])}">Ver en Meta →</a>')
            if actions:
                rows.append('<div>' + " ".join(actions) + '</div>')
            rows.append('</div>')
        rows.append('</div>')
    rows.append('<div class="foot">SPEKGEN Social Manager · barrido automático · responde este correo no hace nada</div></div>')
    return f"<html><head><style>{css}</style></head><body>{''.join(rows)}</body></html>"


def _sign(secret, external_id, action):
    return hmac.new(secret.encode(), f"{external_id}:{action}".encode(), hashlib.sha256).hexdigest()


def _action_urls(endpoint, secret, external_id):
    if not endpoint or not secret:
        return None, None
    def link(action):
        sig = _sign(secret, external_id, action)
        qs = urllib.parse.urlencode({"id": external_id, "action": action, "sig": sig})
        return f"{endpoint}?{qs}"
    return link("approve"), link("discard")


def gather(conf):
    """Lee pendientes (pending|drafted) de Supabase, agrupa por cliente, cablea links de acción."""
    rows = store.fetch(status="pending")
    rows += store.fetch(status="drafted")
    endpoint = conf.get("approve_endpoint")
    secret = store.get_secret("approve_secret") if endpoint else None
    by_client = {}
    for r in rows:
        # solo los que tienen borrador llevan botones de aprobar/descartar
        if r.get("draft") and r.get("status") == "drafted":
            r["approve_url"], r["skip_url"] = _action_urls(endpoint, secret, r["external_id"])
        by_client.setdefault(r["client"], []).append(r)
    for code in by_client:
        by_client[code].sort(key=lambda x: (x.get("age_days") or 0), reverse=True)
    return by_client


def send(to_addr, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"SPEKGEN Social <{SMTP_USER}>"
    msg["To"] = to_addr
    msg.attach(MIMEText("Tu cliente de correo no soporta HTML.", "plain"))
    msg.attach(MIMEText(html_body, "html"))
    pw = secrets.gmail_app_password()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, pw)
        s.sendmail(SMTP_USER, [to_addr], msg.as_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="imprime HTML, no envia")
    ap.add_argument("--to", help="override destinatario")
    args = ap.parse_args()

    conf = load_config()
    by_client = gather(conf)
    total = sum(len(v) for v in by_client.values())
    html_body = build_html(by_client, conf)
    subject = f"[SPEKGEN] Bandeja social: {total} pendientes IG/FB"

    if args.test:
        out = os.path.join(HERE, "_digest_preview.html")
        with open(out, "w") as f:
            f.write(html_body)
        print(f"Pendientes: {total}. Preview escrito en {out} (NO enviado).")
        return

    to_addr = args.to or conf.get("digest_email")
    send(to_addr, subject, html_body)
    print(f"Digest enviado a {to_addr} ({total} pendientes).")


if __name__ == "__main__":
    main()
