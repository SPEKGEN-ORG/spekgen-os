#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_deliverables.py — Copia los PDFs del batch al Drive folder de deliverables del cliente.

Detecta automáticamente content (post_id) vs ads (batch_id).

Uso:
    python3 sync_deliverables.py /path/to/batch_dir

Destino:
    Mi unidad/SPEKGEN_DELIVERABLES/{CLIENT}/{YYYY-MM}/{batch_id_or_post_id}_*.pdf

Para ads cross-client: copia a SPEKGEN_DELIVERABLES/CROSS/{YYYY-MM}/.
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path

DELIVERABLES_ROOT = Path(
    "/Users/gibranalonzo/Library/CloudStorage/"
    "GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/"
    "SPEKGEN_DELIVERABLES"
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    args = ap.parse_args()

    bd = Path(args.batch_dir).resolve()
    bj = bd / "batch.json"
    if not bj.exists():
        sys.exit(f"No existe {bj}")
    data = json.loads(bj.read_text())

    is_ads = data.get("type") == "ads" or "entries" in data
    is_content = "slides" in data or data.get("type") == "content"

    # Identificador a usar para naming
    if is_ads:
        identifier = data.get("batch_id") or bd.name
        # client en ads puede ser CROSS — eso va a SPEKGEN_DELIVERABLES/CROSS/
        client = (data.get("client") or "CROSS").upper()
        # yyyy_mm: del campo created
        yyyy_mm = (data.get("created") or "")[:7]
    elif is_content:
        identifier = data["post_id"]
        client = (data.get("client") or "UNKNOWN").upper()
        yyyy_mm = (data.get("publish_date") or data.get("created") or "")[:7]
    else:
        sys.exit("Schema no reconocido en batch.json")

    if not yyyy_mm:
        from datetime import date
        yyyy_mm = date.today().strftime("%Y-%m")

    dst_dir = DELIVERABLES_ROOT / client / yyyy_mm
    dst_dir.mkdir(parents=True, exist_ok=True)

    src_dir = bd / "_DELIVERABLES"
    if not src_dir.exists():
        sys.exit(f"No existe _DELIVERABLES/ en {bd}. Corre build_recap_pdf.py primero.")

    pdfs = list(src_dir.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No hay PDFs en {src_dir}")

    print(f"\nSincronizando {len(pdfs)} PDFs de {identifier} a Drive…")
    print(f"  Destino: {dst_dir}\n")
    for pdf in pdfs:
        dst = dst_dir / pdf.name
        shutil.copy2(pdf, dst)
        print(f"  ✓ {pdf.name}")

    print(f"\nLink open: open '{dst_dir}'")
    print(f"Listo. Avisa al cliente por WhatsApp/email manualmente.")

if __name__ == "__main__":
    main()
