#!/usr/bin/env python3
"""
train_soul.py — Upload outputs a Higgsfield + train Soul + actualiza registry.

Workflow:
  1. Validate batch (ejecuta validate_batch.py)
  2. Upload cada PNG en OUTPUTS/ a Higgsfield (captura upload_id)
  3. higgsfield soul-id create con todos los upload_ids
  4. Polling (higgsfield soul-id wait)
  5. Update batch.json con soul_id + cost + tiempo
  6. Append fila a _SOUL_REGISTRY.md (skill home)

Uso:
    python3 train_soul.py {batch_dir} --dry-run        # solo valida
    python3 train_soul.py {batch_dir}                  # ejecuta upload + train

Pre-requisitos:
    higgsfield CLI instalado y autenticado (`higgsfield auth token` debe responder)
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REGISTRY = SKILL_DIR / "_SOUL_REGISTRY.md"


def run_cli(cmd: list[str]) -> tuple[int, str, str]:
    """Run command, return (returncode, stdout, stderr)."""
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def check_higgsfield() -> None:
    code, out, err = run_cli(["higgsfield", "auth", "token"])
    if code != 0:
        sys.exit(f"❌ Higgsfield CLI no responde. Verifica `higgsfield auth login`.\n{err}")


def upload_outputs(batch_dir: Path, batch: dict) -> list[str]:
    """Upload cada PNG en OUTPUTS/ no-dropped. Returns list of upload_ids."""
    upload_ids = []
    for pr in batch["prompts"]:
        if pr["status"] == "dropped":
            continue
        out = batch_dir / pr["output_filename"]
        if not out.exists():
            print(f"   ⏭️  skip #{pr['num']:02d} (no descargado)")
            continue
        print(f"   📤 upload #{pr['num']:02d} {pr['slug']}...", end=" ", flush=True)
        code, stdout, stderr = run_cli(["higgsfield", "upload", "create", "--file", str(out)])
        if code != 0:
            print(f"FAIL: {stderr[:200]}")
            sys.exit(f"❌ Upload falló para {out.name}")
        # Parse upload_id from output (assume `upload_id: XXX` or JSON-ish)
        upload_id = None
        for line in stdout.splitlines():
            if "upload_id" in line.lower() or "id:" in line.lower():
                # crude extraction; adjust if higgsfield CLI format differs
                parts = line.replace(":", " ").replace('"', " ").replace(",", " ").split()
                for i, t in enumerate(parts):
                    if t.lower() in ("upload_id", "id") and i + 1 < len(parts):
                        upload_id = parts[i + 1]
                        break
                if upload_id:
                    break
        if not upload_id:
            print(f"FAIL: no se pudo parsear upload_id\nstdout:\n{stdout}")
            sys.exit("❌ Parsing upload_id falló. Verifica formato del CLI.")
        print(f"✓ {upload_id}")
        upload_ids.append(upload_id)
    return upload_ids


def train_soul(batch: dict, upload_ids: list[str]) -> tuple[str, dict]:
    """Run higgsfield soul-id create + wait. Returns (soul_id, training_meta)."""
    name = batch["subject_name"]
    model_flag = "--soul-2" if batch["soul_model"] == "soul-2" else "--soul-cinematic"

    cmd = ["higgsfield", "soul-id", "create", "--name", name, model_flag]
    for uid in upload_ids:
        cmd.extend(["--image", uid])

    print(f"\n   🧠 higgsfield soul-id create --name {name} {model_flag} (con {len(upload_ids)} imágenes)")
    started = datetime.now()
    code, stdout, stderr = run_cli(cmd)
    if code != 0:
        sys.exit(f"❌ soul-id create falló:\n{stderr}")

    # Parse soul_id + cost from stdout
    soul_id, cost = None, None
    for line in stdout.splitlines():
        low = line.lower()
        if "soul_id" in low or "soul id" in low:
            for tok in line.replace(":", " ").replace('"', " ").split():
                if tok.startswith("soul_") or (len(tok) > 8 and "-" in tok):
                    soul_id = tok
                    break
        if "credit" in low or "cost" in low:
            for tok in line.split():
                if tok.replace(".", "", 1).isdigit():
                    cost = float(tok)
                    break

    if not soul_id:
        print(f"\n⚠️  No se pudo parsear soul_id automáticamente. stdout:\n{stdout}")
        soul_id = input("Pega el soul_id manualmente: ").strip()

    # Wait for training
    print(f"   ⏳ esperando training (5-15 min)...")
    code, _, _ = run_cli(["higgsfield", "soul-id", "wait", soul_id])
    completed = datetime.now()

    return soul_id, {
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "cost_credits": cost,
        "elapsed_seconds": int((completed - started).total_seconds())
    }


def update_registry(batch: dict) -> None:
    """Append row to _SOUL_REGISTRY.md."""
    if not REGISTRY.exists():
        REGISTRY.write_text(
            "# _SOUL_REGISTRY — Catálogo de Souls entrenados en Higgsfield\n\n"
            "| Cliente | Sujeto | Tipo | Soul ID | Modelo | Fecha | Costo | Fidelidad | Batch path |\n"
            "|---|---|---|---|---|---|---|---|---|\n",
            encoding="utf-8"
        )

    row = (
        f"| {batch['client']} "
        f"| {batch['subject_name']} "
        f"| {batch['subject_type']} "
        f"| `{batch['training']['soul_id']}` "
        f"| {batch['soul_model']} "
        f"| {batch['training']['completed_at'][:10]} "
        f"| {batch['training']['cost_credits'] or '—'} "
        f"| {batch['training']['fidelity_score'] or '—'} "
        f"| `{batch['batch_id']}` |\n"
    )
    with REGISTRY.open("a", encoding="utf-8") as f:
        f.write(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    batch_dir = Path(args.batch_dir).expanduser().resolve()

    bj = batch_dir / "batch.json"
    if not bj.exists():
        sys.exit(f"❌ batch.json no encontrado en {batch_dir}")

    # Validate first
    print("🔍 Validando batch...")
    validate_path = SCRIPT_DIR / "validate_batch.py"
    code = subprocess.run(["/usr/bin/python3", str(validate_path), str(batch_dir)]).returncode
    if code == 1:
        sys.exit("❌ Batch tiene errores bloqueantes. Resolvé antes de entrenar.")
    if code == 2:
        confirm = input("\n⚠️  Hay warnings. Continuar con training? [y/N]: ").strip().lower()
        if confirm != "y":
            sys.exit("Abortado.")

    if args.dry_run:
        print("✅ dry-run completo. Skip upload + train.")
        return

    # Higgsfield CLI check
    print("\n🔌 Verificando higgsfield CLI...")
    check_higgsfield()
    print("   ✓ autenticado")

    batch = json.loads(bj.read_text(encoding="utf-8"))

    # Upload
    print(f"\n📤 Upload de outputs a Higgsfield...")
    upload_ids = upload_outputs(batch_dir, batch)

    if len(upload_ids) < 5:
        sys.exit(f"❌ Solo {len(upload_ids)} uploads exitosos. Mínimo 5.")

    # Train
    soul_id, meta = train_soul(batch, upload_ids)

    # Update batch.json
    batch["training"]["soul_id"] = soul_id
    batch["training"].update(meta)
    bj.write_text(json.dumps(batch, indent=2, ensure_ascii=False), encoding="utf-8")

    # Update registry
    update_registry(batch)

    print(f"\n✅ Soul entrenado: {soul_id}")
    print(f"   Costo: {meta.get('cost_credits') or '—'} créditos")
    print(f"   Tiempo: {meta.get('elapsed_seconds', 0) // 60} min")
    print(f"   Registry: {REGISTRY}")
    print(f"\nPara test gen:")
    print(f"   higgsfield generate create text2image_soul_v2 \\")
    print(f"     --prompt \"{batch['subject_name']} on a marble surface, golden hour\" \\")
    print(f"     --soul-id {soul_id}")


if __name__ == "__main__":
    main()
