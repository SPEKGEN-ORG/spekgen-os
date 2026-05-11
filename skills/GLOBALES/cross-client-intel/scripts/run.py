#!/usr/bin/env python3
"""
run.py — Orquesta todo el flujo del skill cross-client-intel:
  1. Corre cross_client_pull.py (subprocess) -> captura stdout JSON
  2. Corre detect_actions.run() sobre el pull
  3. Renderiza HTML + PDF en _cross_client_intel/
  4. Escribe pause_plan_{FECHA}.json para que pause.py lo consuma luego
  5. `open` del PDF + `open -R` para revelar en Finder

CLI:
    python3 run.py [--days 14] [--no-open] [--out-dir PATH]
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Resolve paths from this script's location
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import detect_actions  # noqa: E402
import render_report  # noqa: E402

ROOT = Path("/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL")
DEFAULT_OUT = ROOT / "SPK - SPEKGEN AGENCY/SPK - 15. FACTORY/_intel"
PULL_SCRIPT = ROOT / "SPK - SPEKGEN AGENCY/SPK - 00. COMMAND CENTER/03. HERRAMIENTAS/_cross_client_intel/cross_client_pull.py"


def run_pull(days: int) -> dict:
    if not PULL_SCRIPT.exists():
        raise FileNotFoundError(f"cross_client_pull.py no encontrado en {PULL_SCRIPT}")
    proc = subprocess.run(
        ["python3", str(PULL_SCRIPT), "--days", str(days)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"cross_client_pull.py exited {proc.returncode}")
    # stderr contains progress, stdout contains JSON
    sys.stderr.write(proc.stderr)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"pull did not return valid JSON: {e}\nstdout head: {proc.stdout[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--no-open", action="store_true", help="No abrir el PDF al terminar")
    ap.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"[1/4] Pulling Meta API ultimos {args.days} dias para GR+HC+LF...", file=sys.stderr)
    pull = run_pull(args.days)

    # Save raw pull (timestamped)
    pull_path = out_dir / f"pull_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    pull_path.write_text(json.dumps(pull, indent=2, default=str))
    print(f"      raw -> {pull_path}", file=sys.stderr)

    print("[2/4] Aplicando reglas de deteccion (pauses, winners, replicacion)...", file=sys.stderr)
    actions = detect_actions.run(pull)
    actions_path = out_dir / f"actions_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    actions_path.write_text(json.dumps(actions, indent=2, default=str))
    print(f"      pauses detectados: {len(actions['pauses'])}", file=sys.stderr)
    print(f"      winners detectados: {len(actions['winners'])}", file=sys.stderr)
    print(f"      replicaciones sugeridas: {len(actions['replication_plan'])}", file=sys.stderr)

    # Pause plan file — consumed by pause.py (always overwritten to latest)
    plan_path = out_dir / f"pause_plan_{date_str}.json"
    plan_path.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(),
        "pauses": actions["pauses"],
    }, indent=2, default=str))
    # Also write a "latest" pointer that pause.py always looks for first
    (out_dir / "pause_plan_latest.json").write_text(plan_path.read_text())
    print(f"      plan -> {plan_path}", file=sys.stderr)

    print("[3/4] Renderizando HTML + PDF...", file=sys.stderr)
    html_path, pdf_path = render_report.render(pull, actions, out_dir, date_str, days=args.days)
    print(f"      HTML -> {html_path}", file=sys.stderr)
    print(f"      PDF  -> {pdf_path}", file=sys.stderr)

    if not args.no_open:
        print("[4/4] Abriendo PDF y revelando en Finder...", file=sys.stderr)
        subprocess.run(["open", str(pdf_path)], check=False)
        subprocess.run(["open", "-R", str(pdf_path)], check=False)
    else:
        print("[4/4] --no-open activo; saltando apertura.", file=sys.stderr)

    print("\nListo.", file=sys.stderr)
    print(f"PDF: {pdf_path}")
    print(f"HTML: {html_path}")
    print(f"Pauses pendientes de confirmar: {len(actions['pauses'])}")
    if actions["pauses"]:
        print("Para ejecutar las pausas: python3 scripts/pause.py")


if __name__ == "__main__":
    main()
