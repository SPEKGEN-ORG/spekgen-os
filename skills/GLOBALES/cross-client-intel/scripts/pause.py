#!/usr/bin/env python3
"""
pause.py — Pausa los ads que estan en el plan generado por run.py.
Requiere confirmacion interactiva antes de pegarle a Meta API.

Uso:
    python3 pause.py                # lee pause_plan_latest.json, pide y/n
    python3 pause.py --yes          # skip confirmation (scripted)
    python3 pause.py --plan FILE    # usar plan distinto

Escribe log en pause_log_{YYYYMMDD_HHMM}.json con el resultado de cada PAUSE.
"""
from __future__ import annotations
import argparse
import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path("/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL")
PLAN_DIR = ROOT / "SPK - SPEKGEN AGENCY/SPK - 00. COMMAND CENTER/03. HERRAMIENTAS/_cross_client_intel"

ENV_PATHS = {
    "GR": ROOT / "GR - GREENRAY/.env",
    "HC": ROOT / "HC - HEALTHY CHUCHOS/.env",
    "LF": ROOT / "LF - LO FITNESS/.env",
}


def load_env(p: Path) -> dict:
    env = {}
    if not p.exists():
        return env
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def pause_ad(ad_id: str, token: str) -> dict:
    url = f"https://graph.facebook.com/v21.0/{ad_id}"
    data = urllib.parse.urlencode({"status": "PAUSED", "access_token": token}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"ok": True, "body": json.loads(r.read().decode())}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "body": e.read().decode()}
    except Exception as e:
        return {"ok": False, "body": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="No preguntar confirmacion")
    ap.add_argument("--plan", type=str, default=str(PLAN_DIR / "pause_plan_latest.json"))
    args = ap.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"ERROR: plan no existe: {plan_path}", file=sys.stderr)
        print("Corre primero: python3 run.py", file=sys.stderr)
        sys.exit(1)

    plan = json.loads(plan_path.read_text())
    pauses = plan.get("pauses", [])
    if not pauses:
        print("No hay ads en el plan para pausar. Nada que hacer.")
        return

    print(f"\nPlan cargado: {plan_path}")
    print(f"Generado: {plan.get('generated_at', 'unknown')}")
    print(f"Ads a pausar: {len(pauses)}\n")
    print(f"{'#':<3} {'CLI':<4} {'AD_ID':<20} {'PRODUCTO':<12} {'SPEND':>8} {'CPA':>8}  AD_NAME")
    print("-" * 100)
    for i, p in enumerate(pauses, 1):
        cpa = f"${p['cpa']:.0f}" if p.get("cpa") else "   —"
        print(f"{i:<3} {p['client']:<4} {p['ad_id']:<20} {p.get('product','—'):<12} "
              f"${p['spend']:>6.0f} {cpa:>8}  {p['ad_name']}")
    print()

    if not args.yes:
        resp = input("Confirmar PAUSAR todos estos ads en Meta? [y/N]: ").strip().lower()
        if resp != "y":
            print("Cancelado.")
            return

    # Cache tokens per client
    token_cache: dict[str, str] = {}

    def get_token(client: str) -> str | None:
        if client in token_cache:
            return token_cache[client]
        env = load_env(ENV_PATHS[client])
        tok = env.get("META_TOKEN") or env.get("META_ACCESS_TOKEN")
        if tok:
            token_cache[client] = tok
        return tok

    results = []
    for p in pauses:
        tok = get_token(p["client"])
        if not tok:
            print(f"[SKIP] {p['client']} {p['ad_id']}: no token en .env")
            results.append({**p, "ok": False, "body": "no token"})
            continue
        res = pause_ad(p["ad_id"], tok)
        mark = "OK" if res["ok"] else "ERR"
        print(f"[{mark}] {p['client']} {p['ad_id']} {p['ad_name']}: {res}")
        results.append({**p, **res})

    log_path = PLAN_DIR / f"pause_log_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    log_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nlog -> {log_path}")
    ok_count = sum(1 for r in results if r.get("ok"))
    print(f"Resultado: {ok_count}/{len(results)} pausados con exito.")


if __name__ == "__main__":
    main()
