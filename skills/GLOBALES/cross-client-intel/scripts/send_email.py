#!/usr/bin/env python3
"""
send_email.py — Envia el PDF del reporte cross-client por Gmail SMTP.

ENV:
  SPEKGEN_GMAIL_SENDER         (ej. spekgen.ai@gmail.com)
  SPEKGEN_GMAIL_APP_PASSWORD   (app password Gmail, 16 chars sin espacios)
  REPORT_RECIPIENT             (ej. gibran.alonzo0506@gmail.com)
  PDF_PATH                     (path absoluto al PDF a adjuntar)
  PDF_NAME                     (nombre del adjunto en el email)

SMTP usa puerto 587 STARTTLS (no 465, que esta bloqueado en algunos runners).
"""
from __future__ import annotations
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path


def main():
    sender = os.environ.get("SPEKGEN_GMAIL_SENDER")
    password = os.environ.get("SPEKGEN_GMAIL_APP_PASSWORD")
    recipient = os.environ.get("REPORT_RECIPIENT", "gibran.alonzo0506@gmail.com")
    pdf_path = os.environ.get("PDF_PATH")
    pdf_name = os.environ.get("PDF_NAME") or (Path(pdf_path).name if pdf_path else "report.pdf")

    missing = [k for k, v in {
        "SPEKGEN_GMAIL_SENDER": sender,
        "SPEKGEN_GMAIL_APP_PASSWORD": password,
        "PDF_PATH": pdf_path,
    }.items() if not v]
    if missing:
        print(f"ERROR: faltan env vars: {missing}", file=sys.stderr)
        sys.exit(1)

    if not Path(pdf_path).exists():
        print(f"ERROR: PDF no existe en {pdf_path}", file=sys.stderr)
        sys.exit(1)

    subject = f"[SPEKGEN] Cross-Client Intel — {datetime.now().strftime('%Y-%m-%d')}"
    html_body = f"""
    <html><body style="font-family:-apple-system,Arial,sans-serif;max-width:640px;color:#222;">
      <h2 style="color:#7c3aed;margin-bottom:4px;">Cross-Client Meta Ads Intel</h2>
      <p style="color:#666;margin-top:0;">{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC · Auto-generado por GitHub Actions</p>
      <p>Gibran, aqui esta el analisis de las 3 cuentas de la red (GR + HC + LF), ventana 14 dias.</p>
      <p>Revisa el PDF adjunto. Secciones importantes:</p>
      <ol>
        <li><b>Snapshot por cuenta</b> — spend, compras, ROAS consolidado</li>
        <li><b>Ads para PAUSAR</b> — el monto en riesgo y el porque. Confirmar manualmente con <code>python3 pause.py</code></li>
        <li><b>Winners cross-client</b> — ads con ROAS >= 2 listos a escalar/replicar</li>
        <li><b>Plan de replicacion</b> — que formato portar de un cliente a otro</li>
        <li><b>Senales</b> — preguntas abiertas para el siguiente pull</li>
      </ol>
      <p>Este reporte se genera automatico cada 3 dias. Proximo: {(datetime.now().date()).isoformat()} + 3 dias.</p>
      <p style="color:#888;font-size:12px;">Skill: /cross-client-intel · Workflow: cross-client-intel.yml</p>
    </body></html>
    """

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=pdf_name)
        msg.attach(part)

    print(f"Sending to {recipient} via smtp.gmail.com:587 (STARTTLS)...", file=sys.stderr)
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls()
        s.login(sender, password)
        s.sendmail(sender, [recipient], msg.as_string())
    print("Email sent.", file=sys.stderr)


if __name__ == "__main__":
    main()
