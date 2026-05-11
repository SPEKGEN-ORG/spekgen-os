#!/usr/bin/env python3
"""
sync_intel_email.py — Polls spekgen.ai@gmail.com IMAP, downloads PDF
attachments from "[SPEKGEN] Cross-Client Intel" emails into the Drive
folder `SPK - 15. FACTORY/_intel/`. Idempotent: skips files that already
exist locally.

Lives next to the cross-client-intel skill but is meant to be run as a
recurring job (launchd, cron) so emails sent by the GH Actions workflow
land in `_intel/` automatically without requiring Drive API auth.

ENV (from `SPK - SPEKGEN AGENCY/.env`):
  SPEKGEN_GMAIL_APP_PASSWORD   IMAP password for spekgen.ai@gmail.com

CLI:
  python3 sync_intel_email.py [--days 7] [--mailbox '"[Gmail]/Sent Mail"']
"""
from __future__ import annotations
import argparse
import email
import imaplib
import os
import re
import sys
from datetime import datetime, timedelta
from email.header import decode_header
from pathlib import Path

ROOT = Path("/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL")
ENV_PATH = ROOT / "SPK - SPEKGEN AGENCY/.env"
INTEL_DIR = ROOT / "SPK - SPEKGEN AGENCY/SPK - 15. FACTORY/_intel"

SENDER = "spekgen.ai@gmail.com"
SUBJECT_PREFIX = "[SPEKGEN] Cross-Client Intel"


def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def decode_filename(name: str) -> str:
    parts = decode_header(name)
    out = ""
    for txt, enc in parts:
        if isinstance(txt, bytes):
            out += txt.decode(enc or "utf-8", errors="replace")
        else:
            out += txt
    return out


def safe_filename(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._\- ]+", "_", name)
    return name[:200] or "report.pdf"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7,
                    help="Window de bsqueda (default 7d)")
    ap.add_argument("--mailbox", default='"[Gmail]/Sent Mail"',
                    help="IMAP mailbox a leer (default Sent)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    env = load_env(ENV_PATH)
    pwd = env.get("SPEKGEN_GMAIL_APP_PASSWORD") or os.environ.get("SPEKGEN_GMAIL_APP_PASSWORD")
    if not pwd:
        print("ERROR: SPEKGEN_GMAIL_APP_PASSWORD no encontrado en .env ni en env", file=sys.stderr)
        sys.exit(1)
    pwd = pwd.replace(" ", "")  # IMAP no acepta espacios

    INTEL_DIR.mkdir(parents=True, exist_ok=True)
    since = (datetime.utcnow() - timedelta(days=args.days)).strftime("%d-%b-%Y")
    if args.verbose:
        print(f"[sync] connecting as {SENDER}, mailbox {args.mailbox}, since {since}")

    M = imaplib.IMAP4_SSL("imap.gmail.com")
    M.login(SENDER, pwd)
    typ, _ = M.select(args.mailbox, readonly=True)
    if typ != "OK":
        print(f"ERROR: select {args.mailbox} fall: {typ}", file=sys.stderr)
        sys.exit(1)

    # Buscar emails con el subject prefix en la ventana
    typ, data = M.search(None, f'(SINCE {since} SUBJECT "{SUBJECT_PREFIX}")')
    if typ != "OK":
        print(f"ERROR: search fall: {typ}", file=sys.stderr)
        sys.exit(1)

    ids = data[0].split()
    if args.verbose:
        print(f"[sync] {len(ids)} emails encontrados")

    saved = 0
    skipped = 0
    for msg_id in ids:
        typ, msg_data = M.fetch(msg_id, "(RFC822)")
        if typ != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        for part in msg.walk():
            if part.get_content_maintype() != "application":
                continue
            ct = part.get_content_type()
            if ct != "application/pdf":
                continue
            raw_name = part.get_filename()
            if not raw_name:
                continue
            name = safe_filename(decode_filename(raw_name))
            target = INTEL_DIR / name
            if target.exists():
                skipped += 1
                if args.verbose:
                    print(f"[sync]    skip (existe): {name}")
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            target.write_bytes(payload)
            saved += 1
            print(f"[sync] OK saved {name} ({len(payload):,} bytes)")

    M.logout()
    print(f"[sync] done. saved={saved} skipped={skipped} total_emails={len(ids)}")


if __name__ == "__main__":
    main()
