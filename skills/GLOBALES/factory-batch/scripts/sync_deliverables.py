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
import argparse, json, os, shutil, sys
from pathlib import Path


def drive_root() -> Path:
    """Resuelve '01. CLIENTS OFFICIAL' sin hardcodear la cuenta de Drive.

    Orden: SPEKGEN_ROOT env -> ascenso de directorios -> glob del Drive montado.
    Truena fuerte si no lo encuentra (nada de defaults silenciosos).
    """
    env = os.environ.get("SPEKGEN_ROOT")
    if env:
        return Path(env)
    anchor = "01. CLIENTS OFFICIAL"
    for parent in Path(__file__).resolve().parents:
        if parent.name == anchor:
            return parent
    for gd in sorted((Path.home() / "Library" / "CloudStorage").glob("GoogleDrive-*")):
        for md in sorted(gd.glob("My Drive*")):
            cand = md / anchor
            # Hay mounts viejos de Drive que conservan un "01. CLIENTS OFFICIAL"
            # husk (uno trae solo F24). Exigimos un marcador de la raiz viva
            # para no leer/escribir datos rancios en silencio.
            if (cand / "SPK - SPEKGEN AGENCY").is_dir():
                return cand
    raise RuntimeError(
        f"No encontre '{anchor}'. Set SPEKGEN_ROOT=/ruta/absoluta al directorio."
    )


# SPEKGEN_DELIVERABLES cuelga de "My Drive", NO de "01. CLIENTS OFFICIAL"
DELIVERABLES_ROOT = drive_root().parent / "SPEKGEN_DELIVERABLES"

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
