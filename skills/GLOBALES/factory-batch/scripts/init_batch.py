#!/usr/bin/env python3
"""
init_batch.py v2 — Crea batch en client subfolder dentro de SPK - 15. FACTORY/.

Uso:
    # content (single post HC, MG, etc.)
    python3 init_batch.py --type content --client HC --post-id HC-033

    # ads (batch multi-ad)
    python3 init_batch.py --type ads --client HC                # default fecha hoy
    python3 init_batch.py --type ads --client CROSS --date 2026-05-01

    # pdp (batch per-producto)
    python3 init_batch.py --type pdp --client HC --product OMEGADOG

    # prospect
    python3 init_batch.py --type prospect --name ENLACE

Estructura output:
    content/{CLIENT}/{YYYY-MM}/{POST_ID}/         ← single post
    ads/{CLIENT}/{YYYY-MM}/BATCH_{CLIENT}_{date}-v{N}/
    pdps/{CLIENT}/{PRODUCT}/{YYYY-MM}/BATCH_{date}-v{N}/
    prospects/{NAME}/

Cada batch tiene skeleton:
    batch.json             ← Claude llena con metadata + slides + prompts
    ATTACHMENTS/           ← logos, productos, references
    COVER_VARIANTS/        ← solo content/pdp; 3 variantes Web UI fase 3
    FINAL/                 ← outputs finales (ganadores)
    BORRADOR/              ← variantes descartadas
    _DELIVERABLES/         ← PDFs whiteboard + deck post-selection
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

FACTORY = Path(
    "/Users/gibranalonzo/Library/CloudStorage/"
    "GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/"
    "01. CLIENTS OFFICIAL/SPK - SPEKGEN AGENCY/"
    "SPK - 15. FACTORY"
)

VALID_TYPES = {"content", "ads", "pdp", "prospect"}
VALID_CLIENTS = {"HC", "LF", "GR", "MG", "GIBRAN", "CROSS"}


def next_version(parent: Path, stem: str) -> int:
    if not parent.exists():
        return 1
    existing = list(parent.glob(f"{stem}-v*"))
    nums = []
    for p in existing:
        try:
            nums.append(int(p.name.rsplit("-v", 1)[-1]))
        except ValueError:
            continue
    return (max(nums) + 1) if nums else 1


def build_path(args, date_str: str) -> tuple[Path, str]:
    """Retorna (batch_dir, batch_id_descriptivo)."""
    yyyy_mm = date_str[:7]  # 2026-04

    if args.type == "content":
        if not args.client or not args.post_id:
            sys.exit("[init] --client y --post-id requeridos para --type content")
        client = args.client.upper()
        post_id = args.post_id.upper()
        bd = FACTORY / "content" / client / yyyy_mm / post_id
        return bd, post_id

    if args.type == "ads":
        client = (args.client or "CROSS").upper()
        parent = FACTORY / "ads" / client / yyyy_mm
        stem = f"BATCH_{client}_{date_str}"
        v = next_version(parent, stem)
        bd = parent / f"{stem}-v{v}"
        return bd, f"{stem}-v{v}"

    if args.type == "pdp":
        if not args.client or not args.product:
            sys.exit("[init] --client y --product requeridos para --type pdp")
        client = args.client.upper()
        product = args.product.upper().replace(" ", "")
        parent = FACTORY / "pdps" / client / product / yyyy_mm
        stem = f"BATCH_{date_str}"
        v = next_version(parent, stem)
        bd = parent / f"{stem}-v{v}"
        return bd, f"{client}-{product}-{date_str}-v{v}"

    if args.type == "prospect":
        if not args.name:
            sys.exit("[init] --name requerido para --type prospect")
        name = args.name.upper().replace(" ", "_")
        bd = FACTORY / "prospects" / name
        return bd, name

    sys.exit(f"[init] type invalido: {args.type}")


def build_skeleton_batch_json(args, batch_id: str, date_str: str) -> dict:
    if args.type == "content":
        return {
            "post_id": args.post_id.upper(),
            "client": args.client.upper(),
            "type": "content",
            "pillar": None,
            "format": None,
            "funnel": None,
            "series": None,
            "series_iter": None,
            "title": None,
            "concept_style": None,
            "product": None,
            "publish_date": None,
            "publish_time": None,
            "aspect_ratio": "4:5",
            "hook": None,
            "slides": [],
            "caption": None,
            "cta_keyword": None,
            "hashtags": [],
            "compliance_check": [],
            "model_used": "gemini-3-pro-image-preview",
            "winning_variants": None,
            "status": "DRAFT",
            "published_url": None,
            "created": date_str,
        }
    if args.type == "ads":
        return {
            "batch_id": batch_id,
            "type": "ads",
            "client": (args.client or "CROSS").upper(),
            "campaign": None,
            "model_used": "gemini-3-pro-image-preview",
            "created": date_str,
            "version": "v1",
            "status": "DRAFT",
            "compliance_check": [],
            "entries": [],
        }

    # pdp / prospect → array genérico
    return {
        "batch_id": batch_id,
        "type": args.type,
        "client": (args.client or "CROSS").upper() if args.type != "prospect" else None,
        "created": date_str,
        "entries": [],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=sorted(VALID_TYPES))
    ap.add_argument("--client", help="HC|LF|GR|MG|GIBRAN|CROSS")
    ap.add_argument("--post-id", help="ej. HC-033 (solo --type content)")
    ap.add_argument("--product", help="slug producto (solo --type pdp)")
    ap.add_argument("--name", help="nombre prospect (solo --type prospect)")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    args = ap.parse_args()

    if args.client and args.client.upper() not in VALID_CLIENTS:
        sys.exit(f"[init] client invalido: {args.client}")

    batch_dir, batch_id = build_path(args, args.date)

    if batch_dir.exists():
        print(f"[init] batch ya existe: {batch_dir}")
        sys.exit(0)

    batch_dir.mkdir(parents=True)

    # Skeleton subfolders
    subfolders = ["ATTACHMENTS", "FINAL", "BORRADOR", "_DELIVERABLES"]
    if args.type in ("content", "pdp"):
        subfolders.insert(0, "COVER_VARIANTS")
    for sub in subfolders:
        (batch_dir / sub).mkdir()

    # batch.json skeleton
    skeleton = build_skeleton_batch_json(args, batch_id, args.date)
    (batch_dir / "batch.json").write_text(
        json.dumps(skeleton, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"[init] batch creado: {batch_dir}")
    print(f"[init] batch_id: {batch_id}")
    print(f"[init] skeleton subfolders: {', '.join(subfolders)}")
    print()
    print("[init] siguientes pasos:")

    client_pf = (args.client or "?").upper()
    if args.type == "ads":
        print(f"       1. Pre-flight read OBLIGATORIO:")
        print(f"          • _brand_rules/{client_pf}.md")
        print(f"          • _learnings/{client_pf}/ADS/_MASTER.md")
        print(f"          • _prompts/{client_pf}/ADS/_MASTER.md")
        print(f"          • _intel/CROSS_CLIENT_INSIGHTS_*.pdf (último)")
        print(f"          • Dashboard gsheet del cliente (métricas 7-14d)")
        print(f"       2. Claude propone mix (N ads por formato/producto). Gibran aprueba.")
        print(f"       3. Claude llena batch.json `entries[]` con los 13 campos del schema.")
        print(f"          Ver: _templates/ad_entry.json (template) + ads_batch.schema.json")
        print(f"       4. Copiar attachments a ATTACHMENTS/{{ad_code}}/ (por ad) o ATTACHMENTS/ (compartidos)")
        print(f"       5. python3 generate_images.py \"{batch_dir}\"")
        print(f"          → 2 variantes por ad. Output: FINAL/{{ad_code}}_v1.jpg + _v2.jpg")
        print(f"       6. python3 finalize_selection.py \"{batch_dir}\" --pick HC-AD-001_*=v1 HC-AD-002_*=v2 ...")
        print(f"       7. python3 build_recap_pdf.py \"{batch_dir}\" → matriz formato×cliente")
        print(f"       8. python3 sync_deliverables.py \"{batch_dir}\" → Drive")
        print(f"       9. /spekgen-meta-ads-upload (skill aparte) para subir a Meta")
    else:
        print(f"       1. Pre-flight read: _brand_rules/{client_pf}.md +")
        print(f"          _learnings/{client_pf}/IMAGE_GEN/_MASTER.md +")
        print(f"          _prompts/{client_pf}/_MASTER.md")
        print(f"       2. Claude llena batch.json con metadata + slides + prompts")
        print(f"       3. Copiar attachments a ATTACHMENTS/")
        if args.type in ("content", "pdp"):
            print(f"       4a. (Si chassis nuevo) Claude da 3 prompts cover, Gibran")
            print(f"           genera en gemini.google.com, descarga a COVER_VARIANTS/")
            print(f"       4b. (Si chassis aprobado) skip cover variants, usar S1 ref")
        print(f"       5. (Web UI) Generar imágenes manualmente en gemini.google.com")
        print(f"       6. python3 generate_dashboard.py \"{batch_dir}\" → re-genera UI")
        print(f"       7. python3 build_recap_pdf.py \"{batch_dir}\" --format both")

    # v3: auto-llamar generate_dashboard.py al final si batch.json tiene entries
    print()
    try:
        import subprocess
        bj = Path(batch_dir) / "batch.json"
        if bj.exists():
            data = json.loads(bj.read_text(encoding="utf-8"))
            has_entries = bool(data.get("entries")) or bool(data.get("slides"))
            if has_entries and args.type == "ads":
                script = Path(__file__).parent / "generate_dashboard.py"
                subprocess.run(["python3", str(script), str(batch_dir)], check=False)
            else:
                print(f"    [hint] batch.json sin entries todavía — corre `generate_dashboard.py` cuando Claude lo llene.")
    except Exception as e:
        print(f"    [hint] Auto-dashboard skip: {e}")


if __name__ == "__main__":
    main()
