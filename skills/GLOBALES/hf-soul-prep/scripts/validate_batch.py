#!/usr/bin/env python3
"""
validate_batch.py — Valida que el batch esté listo para Soul training.

Checks:
  1. ≥5 outputs presentes en OUTPUTS/ (rango Higgsfield 5-20, mín. 5 para calidad)
  2. Todos los outputs son PNG legibles
  3. Aspect ratio cuadrado 1:1 (recomendado, soft warn si difiere)
  4. Score promedio ≥8/10 si scores capturados

Uso:
    python3 validate_batch.py {batch_dir}

Exit codes:
    0 = batch listo
    1 = bloqueante (no se puede entrenar)
    2 = warnings (se puede entrenar pero con caveats)
"""
import argparse
import json
import sys
from pathlib import Path


def validate(batch_dir: Path) -> tuple[int, list[str], list[str]]:
    bj = batch_dir / "batch.json"
    if not bj.exists():
        return 1, ["batch.json no existe"], []

    batch = json.loads(bj.read_text(encoding="utf-8"))
    errors, warnings = [], []

    # Re-detect outputs
    completed = []
    for pr in batch["prompts"]:
        if pr["status"] == "dropped":
            continue
        out = batch_dir / pr["output_filename"]
        if out.exists():
            completed.append((pr, out))

    n = len(completed)
    if n < 5:
        errors.append(f"Solo {n} outputs descargados. Higgsfield requiere mínimo 5.")
    elif n < 8:
        warnings.append(f"{n}/8 outputs descargados. 8 es óptimo, pero {n} es viable.")

    # Try Pillow for image validation if available
    try:
        from PIL import Image
        for pr, out in completed:
            try:
                with Image.open(out) as img:
                    w, h = img.size
                    if w != h:
                        warnings.append(f"{pr['output_filename']}: aspect ratio {w}x{h}, no 1:1. Soul puede aprender distorsión.")
                    if w < 1024:
                        warnings.append(f"{pr['output_filename']}: resolución {w}x{h}, baja. Recomendado ≥1024x1024.")
            except Exception as e:
                errors.append(f"{pr['output_filename']}: no es PNG válido ({e})")
    except ImportError:
        warnings.append("Pillow no instalado, skipping validación de aspect ratio (pip3 install Pillow para activar).")

    # Score check
    scores = [float(pr["score"]) for pr in batch["prompts"] if pr.get("score") and str(pr["score"]).replace(".","",1).isdigit()]
    if scores:
        avg = sum(scores) / len(scores)
        if avg < 8.0:
            warnings.append(f"Score promedio {avg:.1f}/10 (target ≥8). Soul aprende lo que recibe.")
        below_8 = [pr for pr in batch["prompts"] if pr.get("score") and str(pr["score"]).replace(".","",1).isdigit() and float(pr["score"]) < 8]
        for pr in below_8:
            warnings.append(f"  ↳ #{pr['num']:02d} {pr['slug']}: score {pr['score']}")

    if errors:
        return 1, errors, warnings
    if warnings:
        return 2, errors, warnings
    return 0, errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    args = ap.parse_args()
    batch_dir = Path(args.batch_dir).expanduser().resolve()

    code, errors, warnings = validate(batch_dir)

    if errors:
        print("❌ ERRORES (bloquean training):")
        for e in errors:
            print(f"   • {e}")
    if warnings:
        print("⚠️  WARNINGS (procede con cautela):")
        for w in warnings:
            print(f"   • {w}")
    if not errors and not warnings:
        print("✅ Batch validado, listo para Soul training.")

    sys.exit(code)


if __name__ == "__main__":
    main()
