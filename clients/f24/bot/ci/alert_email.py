#!/usr/bin/env python3
"""alert_email.py — manda un correo de alerta del pipeline del bot F24 (Gmail SMTP).

Molde recortado de skills/GLOBALES/cross-client-intel/scripts/send_email.py (sin adjunto PDF).
Pensado para fallas del pipeline: deploy roto, rollback ejecutado, bot caído en el monitor.

ENV:
  SPEKGEN_GMAIL_APP_PASSWORD   app password de Gmail (= secret GMAIL_APP_PASSWORD en CI)
  GMAIL_USER                   remitente (default spekgen.ai@gmail.com)
  BOT_ALERT_RECIPIENTS         destinatarios separados por coma (Gibran + Pedro). Fallback: ALERT_TO

Uso:
  python3 ci/alert_email.py --subject "..." --body "texto plano o html simple"
  echo "cuerpo" | python3 ci/alert_email.py --subject "..."        # cuerpo por stdin
"""
from __future__ import annotations

import argparse
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", default=None, help="cuerpo; si se omite se lee de stdin")
    args = ap.parse_args()

    sender = os.environ.get("GMAIL_USER", "spekgen.ai@gmail.com")
    password = os.environ.get("SPEKGEN_GMAIL_APP_PASSWORD") or os.environ.get("GMAIL_APP_PASSWORD")
    raw_recipients = os.environ.get("BOT_ALERT_RECIPIENTS") or os.environ.get(
        "ALERT_TO", "gibran.alonzo0506@gmail.com"
    )
    recipients = [r.strip() for r in raw_recipients.split(",") if r.strip()]

    if not password:
        print("ERROR: falta SPEKGEN_GMAIL_APP_PASSWORD / GMAIL_APP_PASSWORD", file=sys.stderr)
        return 1
    if not recipients:
        print("ERROR: no hay destinatarios (BOT_ALERT_RECIPIENTS / ALERT_TO)", file=sys.stderr)
        return 1

    body_text = args.body if args.body is not None else sys.stdin.read()
    body_text = body_text.strip() or "(sin cuerpo)"

    html = f"""
    <html><body style="font-family:-apple-system,Arial,sans-serif;max-width:640px;color:#1a1a1a;">
      <h2 style="color:#c0392b;margin-bottom:4px;">Alerta — Pipeline Bot F24</h2>
      <pre style="white-space:pre-wrap;font-family:ui-monospace,Menlo,monospace;font-size:13px;
                  background:#f6f6f6;border:1px solid #e2e2e2;border-radius:6px;padding:12px;">{body_text}</pre>
      <p style="color:#888;font-size:12px;">Auto-generado por GitHub Actions · repo SPEKGEN-ORG/spekgen-os</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = args.subject
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(html, "html"))

    print(f"Enviando alerta a {recipients} via smtp.gmail.com:587...", file=sys.stderr)
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls()
        s.login(sender, password)
        s.sendmail(sender, recipients, msg.as_string())
    print("Alerta enviada.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
