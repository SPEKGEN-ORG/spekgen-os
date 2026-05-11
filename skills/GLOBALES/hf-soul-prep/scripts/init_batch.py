#!/usr/bin/env python3
"""
init_batch.py — Inicializa un batch de Soul Training para Higgsfield.

Crea estructura completa:
  {batch_dir}/
    batch.json                          # source of truth
    _SOUL_INFO.md                       # metadata humana
    REFERENCE/                          # references compartidas (vacio, copiar a mano)
    ATTACHMENTS/                        # per-prompt copies (vacio hasta primer dashboard)
    OUTPUTS/                            # PNGs descargados aqui
    PROMPTS.md                          # backup legible

Uso:
    python3 init_batch.py {batch_dir} --type product --specs specs.json
    python3 init_batch.py {batch_dir} --type person  --specs specs.json
    python3 init_batch.py {batch_dir} --type product --interactive    # asks for specs in CLI

Specs JSON example (product):
    {
      "subject_name": "ArtriDog",
      "client": "HC",
      "soul_model": "soul-2",
      "placeholders": {
        "PRODUCT_NAME": "ArtriDog",
        "BRAND_NAME": "Healthy Chuchos",
        "CONTAINER_TYPE": "white HDPE plastic jar with white ribbed screw cap",
        "CONTAINER_SIZE": "225g, 9cm tall x 10cm diameter",
        "COLOR_PALETTE": "teal #20838A, coral #F4A57C, navy #1F2A5C, white",
        "KEY_VISUALS": "...",
        "TAGLINE": "Suplemento nutricional",
        "SIZE_LABEL_TEXT": "cont. neto 225 g",
        "INGREDIENT_LIST": "...",
        "LIFESTYLE_PET": "Bernese Mountain Dog"
      }
    }
"""
import argparse
import json
import sys
import shutil
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"


def load_template(subject_type: str) -> dict:
    """Load PROMPT_PACK_{type}.json template."""
    name = f"PROMPT_PACK_{subject_type.upper()}.json"
    path = TEMPLATES_DIR / name
    if not path.exists():
        sys.exit(f"❌ Template no encontrado: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def substitute(text: str, values: dict) -> str:
    """Replace {PLACEHOLDER} tokens with values from dict."""
    out = text
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def build_batch(batch_dir: Path, subject_type: str, specs: dict) -> dict:
    """Build batch.json from template + specs. Does NOT write to disk yet."""
    template = load_template(subject_type)

    placeholders = specs.get("placeholders", {})
    missing = [k for k in template["placeholders_required"] if k not in placeholders]
    if missing:
        sys.exit(f"❌ Placeholders faltantes en specs: {missing}")

    # Build identity lock
    identity_lock = substitute(template["identity_lock_template"], placeholders)

    # Build prompts (substitute identity lock + placeholders)
    prompts = []
    for p in template["prompts"]:
        full_prompt = p["prompt"].replace("{IDENTITY_LOCK}", identity_lock)
        full_prompt = substitute(full_prompt, placeholders)

        slug = p["slug"]
        num = p["num"]
        prompt_dir = f"ATTACHMENTS/{num:02d}_{slug}"
        out_filename = f"OUTPUTS/{num:02d}_{slug}.png"

        prompts.append({
            "num": num,
            "slug": slug,
            "title": p["title"],
            "subtitle": p.get("subtitle", ""),
            "prompt": full_prompt,
            "attachments": [],   # populated when references are dropped
            "output_filename": out_filename,
            "status": "pending",  # pending | completed | dropped
            "score": None,
            "notes": ""
        })

    today = date.today().isoformat()
    subject_name = specs.get("subject_name", "UNKNOWN")
    client = specs.get("client", "?")
    soul_model = specs.get("soul_model", "soul-2")

    batch = {
        "batch_id": f"{subject_name.upper()}_{client}_{today}",
        "subject_name": subject_name,
        "subject_type": subject_type,
        "client": client,
        "soul_model": soul_model,
        "created_at": today,
        "training": {
            "soul_id": None,
            "started_at": None,
            "completed_at": None,
            "cost_credits": None,
            "fidelity_score": None,
            "fidelity_notes": ""
        },
        "subject_specs": placeholders,
        "identity_lock": identity_lock,
        "global_references": [],
        "rubric": template.get("rubric", []),
        "min_pass_rate": template.get("min_pass_rate", ""),
        "prompts": prompts
    }
    return batch


def write_soul_info(batch_dir: Path, batch: dict) -> None:
    """Write _SOUL_INFO.md (human-readable metadata)."""
    p = batch_dir / "_SOUL_INFO.md"
    specs = batch["subject_specs"]
    md = [
        f"# _SOUL_INFO — {batch['subject_name']} ({batch['client']})\n",
        "## Metadata batch\n",
        f"- **Batch ID:** {batch['batch_id']}",
        f"- **Cliente:** {batch['client']}",
        f"- **Sujeto:** {batch['subject_name']} ({batch['subject_type']})",
        f"- **Modelo Higgsfield:** {batch['soul_model']}",
        f"- **Fecha init:** {batch['created_at']}",
        f"- **Fecha train:** _(pending)_\n",
        "## Identity Lock spec\n",
    ]
    for k, v in specs.items():
        md.append(f"- **{k}:** {v}")
    md.append("\n## Outputs status\n")
    md.append("| # | Slug | Status | Score | Notas |")
    md.append("|---|---|---|---|---|")
    for p_ in batch["prompts"]:
        md.append(f"| {p_['num']:02d} | `{p_['slug']}` | {p_['status']} | {p_.get('score') or '—'} | {p_.get('notes') or '—'} |")
    md.append("\n## Soul training\n")
    md.append(f"- **Soul ID:** {batch['training']['soul_id'] or '—'}")
    md.append(f"- **Costo training:** {batch['training']['cost_credits'] or '—'} créditos")
    md.append(f"- **Fidelidad test:** {batch['training']['fidelity_score'] or '—'}/10")
    md.append("\n## Lecciones aprendidas\n_(append post-train)_\n")
    p.write_text("\n".join(md), encoding="utf-8")


def write_prompts_md(batch_dir: Path, batch: dict) -> None:
    """Write PROMPTS.md (legible backup of all 8 prompts after substitution)."""
    p = batch_dir / "PROMPTS.md"
    md = [
        f"# PROMPTS — {batch['batch_id']}\n",
        f"**Sujeto:** {batch['subject_name']} · **Cliente:** {batch['client']} · **Modelo:** {batch['soul_model']}\n",
        "> Backup legible. La fuente operativa es `dashboard.html` (correr `python3 scripts/serve_dashboard.py {batch_dir}`).\n",
        "## Identity Lock\n```\n" + batch["identity_lock"] + "\n```\n",
    ]
    for pr in batch["prompts"]:
        md.append(f"---\n\n## {pr['num']:02d} — {pr['title']}")
        if pr.get("subtitle"):
            md.append(f"_{pr['subtitle']}_")
        md.append(f"\n**Output:** `{pr['output_filename']}`\n")
        md.append(f"**Attachments folder:** `ATTACHMENTS/{pr['num']:02d}_{pr['slug']}/`\n")
        md.append("```\n" + pr["prompt"] + "\n```\n")
    p.write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir", help="Carpeta donde crear el batch")
    ap.add_argument("--type", choices=["product", "person"], required=True)
    ap.add_argument("--specs", help="Path a specs.json con subject_name, client, soul_model, placeholders")
    ap.add_argument("--force", action="store_true", help="Overwrite existing batch.json")
    args = ap.parse_args()

    batch_dir = Path(args.batch_dir).expanduser().resolve()
    batch_dir.mkdir(parents=True, exist_ok=True)

    batch_json = batch_dir / "batch.json"
    if batch_json.exists() and not args.force:
        sys.exit(f"❌ batch.json ya existe en {batch_dir}. Usa --force para sobrescribir.")

    if not args.specs:
        sys.exit("❌ --specs es obligatorio (path a specs.json). Ver header del script para schema.")

    specs_path = Path(args.specs).expanduser().resolve()
    if not specs_path.exists():
        sys.exit(f"❌ specs no encontrado: {specs_path}")
    specs = json.loads(specs_path.read_text(encoding="utf-8"))

    batch = build_batch(batch_dir, args.type, specs)

    # Create subdirs
    (batch_dir / "REFERENCE").mkdir(exist_ok=True)
    (batch_dir / "ATTACHMENTS").mkdir(exist_ok=True)
    (batch_dir / "OUTPUTS").mkdir(exist_ok=True)
    for pr in batch["prompts"]:
        (batch_dir / f"ATTACHMENTS/{pr['num']:02d}_{pr['slug']}").mkdir(parents=True, exist_ok=True)

    # Write files
    batch_json.write_text(json.dumps(batch, indent=2, ensure_ascii=False), encoding="utf-8")
    write_soul_info(batch_dir, batch)
    write_prompts_md(batch_dir, batch)

    print(f"✅ Batch inicializado: {batch_dir}")
    print(f"   batch.json:        {batch_json}")
    print(f"   _SOUL_INFO.md:     {batch_dir / '_SOUL_INFO.md'}")
    print(f"   PROMPTS.md:        {batch_dir / 'PROMPTS.md'}")
    print()
    print("Próximos pasos:")
    print(f"  1. Copiar reference image(s) del sujeto a {batch_dir / 'REFERENCE'}/")
    print(f"  2. python3 {SCRIPT_DIR / 'serve_dashboard.py'} \"{batch_dir}\"")
    print(f"     ↳ levanta server :8767, abre browser, sincroniza ATTACHMENTS/ y muestra dashboard")


if __name__ == "__main__":
    main()
