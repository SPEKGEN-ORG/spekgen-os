#!/usr/bin/env python3
"""yt-insights orchestrator.

Usage:
    run.py extract <URL>
    run.py finalize <slug>
"""
import os
import sys
import argparse
import json
import subprocess
from pathlib import Path
from datetime import date


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

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from _extract import extract_transcript_and_metadata, slug_from_title
from _render_pdf import render_insights_pdf, render_briefs_pdf, render_recap_pdf
from _master_index import append_to_master_index
from _obsidian import write_obsidian_note

VAULT = drive_root() / "SPK - SPEKGEN AGENCY" / "SPK - 18. YT VAULT"
OBSIDIAN = drive_root() / "_OBSIDIAN" / "04 - YT INSIGHTS"


def cmd_extract(url: str, mode: str):
    today = date.today().isoformat()
    folder, meta = extract_transcript_and_metadata(url, VAULT / "videos", today, mode=mode)
    print(f"OK_EXTRACT")
    print(f"folder={folder}")
    print(f"slug={folder.name}")
    print(f"title={meta['title']}")
    print(f"duration_seconds={meta['duration_seconds']}")
    print(f"chapters={json.dumps(meta.get('chapters', []))}")


def cmd_finalize(slug: str):
    folder = VAULT / "videos" / slug
    if not folder.exists():
        print(f"ERROR: folder not found: {folder}", file=sys.stderr)
        sys.exit(1)
    meta = json.loads((folder / "metadata.json").read_text())

    print(f"[1/4] Rendering insights.pdf...")
    insights_md = (folder / "insights.md").read_text()
    insights_pdf = render_insights_pdf(insights_md, folder / "insights.pdf", meta)

    print(f"[2/4] Rendering content_briefs.pdf...")
    briefs_md = (folder / "content_briefs.md").read_text()
    briefs_pdf = render_briefs_pdf(briefs_md, folder / "content_briefs.pdf", meta)

    print(f"[3/4] Rendering _RECAP.pdf...")
    recap_pdf = render_recap_pdf(insights_md, briefs_md, folder / "_RECAP.pdf", meta)

    print(f"[4/4] Updating master index + Obsidian note...")
    append_to_master_index(VAULT / "MASTER_INDEX.xlsx", folder, meta, insights_md, briefs_md)
    write_obsidian_note(OBSIDIAN, folder, meta, insights_md, briefs_md)

    print(f"OK_FINALIZE")
    print(f"recap_pdf={recap_pdf}")
    print(f"insights_pdf={insights_pdf}")
    print(f"briefs_pdf={briefs_pdf}")
    subprocess.run(["open", "-R", str(recap_pdf)])


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ext = sub.add_parser("extract")
    p_ext.add_argument("url")
    p_ext.add_argument("--mode", choices=["fail", "overwrite", "version"], default="fail",
                       help="What to do if folder exists. fail (default) → exit 3 with FOLDER_EXISTS")

    p_fin = sub.add_parser("finalize")
    p_fin.add_argument("slug")

    args = parser.parse_args()
    if args.cmd == "extract":
        cmd_extract(args.url, args.mode)
    elif args.cmd == "finalize":
        cmd_finalize(args.slug)


if __name__ == "__main__":
    main()
