#!/usr/bin/env python3
"""Genera y guarda SOLO la llave de firma HMAC (approve_secret) en social_secrets.
Es una llave de firma benigna — NO un credential de Meta. Se genera sola y no se imprime.
Idempotente: si ya existe, no la regenera (para no invalidar links ya enviados)."""
import json
import os
import secrets as pysecrets
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import secrets  # noqa: E402


def _rest(method, path, body=None, prefer=None):
    url_base, sb_key = secrets.supabase()
    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}",
               "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{url_base}/rest/v1/{path}", method=method, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read().decode()
        return json.loads(txt) if txt else []


def main():
    existing = _rest("GET", "social_secrets?key=eq.approve_secret&select=key")
    if existing:
        print("approve_secret ya existe — no se regenera.")
        return
    value = pysecrets.token_hex(24)
    _rest("POST", "social_secrets", body=[{"key": "approve_secret", "value": value}],
          prefer="resolution=merge-duplicates")
    print("approve_secret generado y guardado en social_secrets (no se imprime).")


if __name__ == "__main__":
    main()
