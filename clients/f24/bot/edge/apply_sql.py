#!/usr/bin/env python3
"""apply_sql.py — corre un archivo .sql de _sql/ contra el Postgres de Supabase.

Usa la Management API (POST /v1/projects/{ref}/database/query) con el PAT
SUPABASE_ACCESS_TOKEN, igual que deploy_f24_edge.py. No necesita CLI ni psql.

  python apply_sql.py 001_qa_calls.sql          # aplica
  python apply_sql.py --query "select 1"        # consulta suelta (para verificar)

Hasta hoy las tablas de este proyecto se creaban a mano en el dashboard y no
quedaba rastro en el repo. Los archivos de _sql/ son la fuente de verdad.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
F24_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROJECT_REF = "wjlwpfaogjpeqgyxxnwa"
API = "https://api.supabase.com"


def load_token() -> str:
    tok = os.environ.get("SUPABASE_ACCESS_TOKEN")
    if tok:
        return tok
    envp = os.path.join(F24_ROOT, ".env")
    if os.path.exists(envp):
        for line in open(envp, encoding="utf-8"):
            line = line.strip()
            if line.startswith("SUPABASE_ACCESS_TOKEN=") and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("FALTA SUPABASE_ACCESS_TOKEN (env o clients/f24/.env)")


def run_sql(sql: str, token: str) -> list | dict:
    req = urllib.request.Request(
        f"{API}/v1/projects/{PROJECT_REF}/database/query",
        data=json.dumps({"query": sql}).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SpekgenDeploy/1.0 (+curl/8.4)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else []
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:600]
        raise SystemExit(f"HTTP {e.code} de Supabase:\n{detail}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="archivo dentro de _sql/")
    ap.add_argument("--query", help="SQL suelto en vez de un archivo")
    args = ap.parse_args()

    token = load_token()
    if args.query:
        sql, label = args.query, "(query suelta)"
    elif args.file:
        path = args.file if os.path.isabs(args.file) else os.path.join(HERE, "_sql", args.file)
        if not os.path.exists(path):
            raise SystemExit(f"no existe {path}")
        sql, label = open(path, encoding="utf-8").read(), os.path.basename(path)
    else:
        raise SystemExit("dame un archivo o --query")

    print(f"[apply_sql] {label} → proyecto {PROJECT_REF} ({len(sql)} bytes)")
    out = run_sql(sql, token)
    print(f"[apply_sql] OK. Respuesta: {json.dumps(out, ensure_ascii=False)[:500]}")


if __name__ == "__main__":
    main()
