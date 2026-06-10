#!/usr/bin/env python3
"""
F24 — Monitor de tracking (Capa 1, Japan-proof).

Revisa el sitio en vivo de Ferre24 y confirma que siguen instalados los tags
de medicion que la campana de Google Ads necesita. El gtag de GA4 vive INLINE
en el tema de Shopify y ya se borro solo una vez (GA4 ciego 08->10 jun 2026
mientras la campana gastaba). Este monitor convierte "ciego varios dias" en
"avisado el mismo dia".

Que valida (en cada URL de PAGES_TO_CHECK):
  - GA4 gtag           -> G-VZB6X2YWT0
  - Google Ads tag     -> AW-18195593805
  - Numero WhatsApp     -> 523317903630   (el evento GA4 Whatsapp_click filtra
                                            por este numero; si cambia, el
                                            tracking muere en silencio)

Si falta CUALQUIERA en CUALQUIER pagina, manda un correo de alerta y termina
con exit code 1 (visible en GitHub Actions). Si todo esta bien, exit 0.

Uso:
  python3 f24_tracking_monitor.py            # revisa y alerta por correo si falla
  python3 f24_tracking_monitor.py --no-email # solo imprime el estado (test local)

Correo: usa Gmail SMTP. Variables de entorno:
  SPEKGEN_GMAIL_APP_PASSWORD  (requerida para enviar; = secret GMAIL_APP_PASSWORD)
  GMAIL_USER                  (opcional, default spekgen.ai@gmail.com)
  ALERT_TO                    (opcional, default gibran.alonzo0506@gmail.com)
"""

import os
import sys
import smtplib
import urllib.request
from email.mime.text import MIMEText
from datetime import datetime, timezone

# --- Que revisar -----------------------------------------------------------
PAGES_TO_CHECK = [
    "https://ferre24.com.mx/",
    "https://ferre24.com.mx/pages/energia-construccion",
]

REQUIRED_TOKENS = {
    "GA4 gtag (G-VZB6X2YWT0)": "G-VZB6X2YWT0",
    "Google Ads tag (AW-18195593805)": "AW-18195593805",
    "WhatsApp num (523317903630)": "523317903630",
}

ALERT_TO = os.environ.get("ALERT_TO", "gibran.alonzo0506@gmail.com")
GMAIL_USER = os.environ.get("GMAIL_USER", "spekgen.ai@gmail.com")
GMAIL_PASS = os.environ.get("SPEKGEN_GMAIL_APP_PASSWORD", "")

UA = {"User-Agent": "Mozilla/5.0 (SPEKGEN F24 tracking monitor)"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def check():
    """Devuelve (ok, lineas_de_reporte, fallas)."""
    report = []
    failures = []
    for url in PAGES_TO_CHECK:
        try:
            html = fetch(url)
        except Exception as e:  # noqa: BLE001
            report.append(f"[ERROR] No se pudo cargar {url}: {e}")
            failures.append(f"{url} -> no carga ({e})")
            continue
        for label, token in REQUIRED_TOKENS.items():
            if token in html:
                report.append(f"[OK]   {url}  ->  {label}")
            else:
                report.append(f"[FALTA] {url}  ->  {label}")
                failures.append(f"{url} -> FALTA {label}")
    return (len(failures) == 0, report, failures)


def send_alert(failures):
    if not GMAIL_PASS:
        print("[WARN] SPEKGEN_GMAIL_APP_PASSWORD no seteada; no se envia correo.")
        return False
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = (
        "ALERTA — el tracking de Ferre24 tiene un hueco.\n\n"
        "Una o mas etiquetas de medicion NO estan en el sitio. Mientras falten, "
        "Google Ads / GA4 puede estar gastando sin registrar conversiones.\n\n"
        "Fallas detectadas:\n  - " + "\n  - ".join(failures) + "\n\n"
        "Causa mas probable: una edicion o republicado del tema de Shopify borro "
        "el gtag inline. Fix: reinsertar el snippet antes de </head> y verificar "
        "que el sitio contenga G-VZB6X2YWT0.\n\n"
        f"Revisado: {stamp}\n"
        "Monitor: F24 - 16 GOOGLE ADS/05_MONITORING/f24_tracking_monitor.py\n"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "[F24] ALERTA tracking caido en ferre24.com.mx"
    msg["From"] = GMAIL_USER
    msg["To"] = ALERT_TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.sendmail(GMAIL_USER, [ALERT_TO], msg.as_string())
    print(f"[ALERT] Correo enviado a {ALERT_TO}")
    return True


def main():
    no_email = "--no-email" in sys.argv
    ok, report, failures = check()
    print("\n".join(report))
    print("-" * 50)
    if ok:
        print("[RESULTADO] Todo el tracking presente. OK.")
        sys.exit(0)
    print(f"[RESULTADO] {len(failures)} falla(s) de tracking.")
    if not no_email:
        send_alert(failures)
    sys.exit(1)


if __name__ == "__main__":
    main()
