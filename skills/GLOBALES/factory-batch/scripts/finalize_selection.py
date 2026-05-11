#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finalize_selection.py — Marca variantes ganadoras, mueve descartadas a BORRADOR/.
Detecta automáticamente content (slides + S{N}=v{V}) vs ads (entries + {AD_CODE}=v{V}).

Uso content:
    python3 finalize_selection.py /path/to/HC-033 --pick S1=v1 S2=v1 S3=v2 S4=v1 S5=v1 S6=v2 S7=v2

Uso ads:
    python3 finalize_selection.py /path/to/BATCH_HC_2026-04-29-v1 --pick HC-AD-001_PS_S_TEST=v1 HC-AD-002_OFFER_2PACK=v2 ...

Acciones:
    1. Lee batch.json
    2. Para cada slide/ad: la variante ganadora se queda en FINAL/, las demás se mueven a BORRADOR/
    3. Actualiza batch.json:
       - content: winning_variants {"1":"v1", ...} + status SELECTED
       - ads: cada entry.winning_variant + entry.status SELECTED + batch.status SELECTED
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
from typing import Dict, List

def parse_picks_content(picks: List[str]) -> Dict[int, str]:
    """S1=v1 S2=v1 ... → {1: 'v1', 2: 'v1', ...}"""
    out = {}
    for p in picks:
        if "=" not in p:
            sys.exit(f"Pick mal formado: {p}. Usar S1=v1")
        k, v = p.split("=", 1)
        if not k.upper().startswith("S"):
            sys.exit(f"(content) Pick debe empezar con S: {p}")
        try:
            slide_num = int(k[1:])
        except ValueError:
            sys.exit(f"Slide num invalido en {p}")
        if not v.startswith("v"):
            sys.exit(f"Variant debe empezar con v: {p}")
        out[slide_num] = v
    return out

def parse_picks_ads(picks: List[str]) -> Dict[str, str]:
    """{AD_CODE}=v1 ... → {AD_CODE: 'v1', ...}"""
    out = {}
    for p in picks:
        if "=" not in p:
            sys.exit(f"Pick mal formado: {p}. Usar AD-CODE=v1")
        k, v = p.rsplit("=", 1)
        if not v.startswith("v"):
            sys.exit(f"Variant debe empezar con v: {p}")
        out[k.strip()] = v
    return out

# ── CONTENT ───────────────────────────────────────────────────────────────────
def finalize_content(bd: Path, data: dict, picks: List[str]):
    post_id = data["post_id"]
    pick_map = parse_picks_content(picks)

    final = bd / "FINAL"
    borrador = bd / "BORRADOR"
    borrador.mkdir(exist_ok=True)

    moved = kept = 0
    for img in sorted(final.glob(f"{post_id}_S*_v*.jpg")):
        stem = img.stem
        parts = stem.split("_")
        slide_part = parts[-2]
        variant = parts[-1]
        try:
            slide_num = int(slide_part[1:])
        except ValueError:
            continue
        winner = pick_map.get(slide_num)
        if winner == variant:
            print(f"  KEEP   S{slide_num} {variant}")
            kept += 1
        else:
            shutil.move(str(img), str(borrador / img.name))
            print(f"  MOVE   S{slide_num} {variant} → BORRADOR/")
            moved += 1

    data["winning_variants"] = {str(k): v for k, v in pick_map.items()}
    if data.get("status") == "DRAFT":
        data["status"] = "SELECTED"

    print(f"\nDone (content). kept={kept}, moved={moved}.")
    return data

# ── ADS ───────────────────────────────────────────────────────────────────────
def finalize_ads(bd: Path, data: dict, picks: List[str]):
    pick_map = parse_picks_ads(picks)

    final = bd / "FINAL"
    borrador = bd / "BORRADOR"
    borrador.mkdir(exist_ok=True)

    # Indexar entries por ad_code para update rápido
    entries_by_code = {e["ad_code"]: e for e in data.get("entries", [])}

    # Validar que todos los picks tengan entry correspondiente
    unknown = [code for code in pick_map if code not in entries_by_code]
    if unknown:
        print(f"  [WARN] picks sin entry en batch.json: {unknown}")

    moved = kept = 0
    # Iteramos por todas las imágenes en FINAL/ que coincidan con algún ad_code
    for img in sorted(final.glob("*_v*.jpg")):
        stem = img.stem  # HC-AD-001_PS_S_TEST_v1
        # Encontrar match con algún ad_code (el que sea prefix de stem)
        matched_code = None
        matched_variant = None
        for code in entries_by_code:
            if stem.startswith(code + "_v"):
                matched_code = code
                matched_variant = stem[len(code) + 1:]  # "v1" / "v2"
                break
        if not matched_code:
            print(f"  [SKIP] {img.name} no matchea ningún ad_code en batch")
            continue

        winner = pick_map.get(matched_code)
        if winner == matched_variant:
            print(f"  KEEP   {matched_code} {matched_variant}")
            kept += 1
        elif winner is None:
            # No se hizo pick para este ad_code → dejar todas las variantes en FINAL
            print(f"  HOLD   {matched_code} {matched_variant} (sin pick)")
        else:
            shutil.move(str(img), str(borrador / img.name))
            print(f"  MOVE   {matched_code} {matched_variant} → BORRADOR/")
            moved += 1

    # Actualizar entries con winning_variant + status
    for code, variant in pick_map.items():
        if code in entries_by_code:
            entries_by_code[code]["winning_variant"] = variant
            entries_by_code[code]["status"] = "SELECTED"

    if data.get("status") == "DRAFT":
        data["status"] = "SELECTED"

    print(f"\nDone (ads). kept={kept}, moved={moved}.")
    return data

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    ap.add_argument("--pick", nargs="+", required=True,
                    help="content: S1=v1 S2=v1 ... | ads: HC-AD-001_*=v1 HC-AD-002_*=v2 ...")
    args = ap.parse_args()

    bd = Path(args.batch_dir).resolve()
    bj = bd / "batch.json"
    if not bj.exists():
        sys.exit(f"No existe {bj}")
    data = json.loads(bj.read_text())

    is_ads = data.get("type") == "ads" or "entries" in data
    is_content = "slides" in data or data.get("type") == "content"

    if is_ads:
        data = finalize_ads(bd, data, args.pick)
    elif is_content:
        data = finalize_content(bd, data, args.pick)
    else:
        sys.exit("Schema no reconocido. Necesita 'slides' o 'entries' en batch.json")

    bj.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"batch.json actualizado: status={data.get('status')}")

if __name__ == "__main__":
    main()
