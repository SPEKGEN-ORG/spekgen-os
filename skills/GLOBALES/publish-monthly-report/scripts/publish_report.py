#!/usr/bin/env python3
"""
publish_report.py — Renderea el template Jinja2 del reporte mensual y publica
a Shopify (spekgen.com) con URL limpia via redirect.

Reutiliza `shopify_client.py` de `_CONTENT_HUB_SHOPIFY/` y los patrones de
`_publish_prospect.py` (versionado de handle por hash, rename .grid -> .spk-grid,
CHROME_HIDER_CSS para ocultar tema Horizon).

Uso:
    python3 publish_report.py \\
        --context contexts/hc_2026-03.json \\
        --template monthly_report.html.j2 \\
        --handle hc-reporte-marzo-abril \\
        --title "Healthy Chuchos · Reporte Marzo-Abril 2026"
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"
REPORTS_DIR = SKILL_DIR / "reports"

# Reuse shopify_client + publish_prospect helpers
AGENCY_DIR = SKILL_DIR.parent.parent.parent  # SPK - SPEKGEN AGENCY/
sys.path.insert(0, str(AGENCY_DIR / "_CONTENT_HUB_SHOPIFY"))
sys.path.insert(0, str(AGENCY_DIR / "PROSPECTOS"))
sys.path.insert(0, str(AGENCY_DIR / "PROSPECTOS" / "mockup_factory"))

from shopify_client import ShopifyClient  # noqa: E402
from _publish_prospect import (  # noqa: E402
    CHROME_HIDER_CSS,
    rename_colliding_classes,
    extract_body_with_head,
    upsert_page,
    upsert_redirect,
    delete_stale_versions,
)

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("ERROR: jinja2 no instalado. `pip3 install jinja2`")
    sys.exit(1)


def render(template_name: str, context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


def publish(context_path: Path, template_name: str, handle_base: str, title: str,
            dry_run: bool = False) -> None:
    print(f"\n[1/5] Loading context {context_path.name}")
    context = json.loads(context_path.read_text())

    print(f"\n[2/5] Rendering template {template_name}")
    html = render(template_name, context)
    print(f"    ✓ rendered ({len(html) / 1024:.0f} KB)")

    # Save local HTML snapshot for QA
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    local_out = REPORTS_DIR / f"{handle_base}.html"
    local_out.write_text(html)
    print(f"    saved local copy → {local_out}")

    if dry_run:
        print("\n[DRY_RUN] Skipping Shopify publish.")
        print(f"    Open local: file://{local_out}")
        return

    print("\n[3/5] Prepping HTML for Shopify (Horizon namespace fixes)")
    html = rename_colliding_classes(html)
    body = CHROME_HIDER_CSS + extract_body_with_head(html)
    print(f"    body size: {len(body) / 1024:.0f} KB")

    print("\n[4/5] Auth Shopify...")
    sc = ShopifyClient()
    info = sc.graphql("{ shop { name primaryDomain { url } } }")
    print(f"    ✓ {info['shop']['name']} ({info['shop']['primaryDomain']['url']})")

    print("\n[5/5] Creating/updating Shopify page + redirect")
    body_hash = hashlib.sha256(body.encode()).hexdigest()[:6]
    versioned_handle = f"{handle_base}-v{body_hash}"
    upsert_page(sc, versioned_handle, title, body)
    upsert_redirect(sc, f"/{handle_base}", f"/pages/{versioned_handle}")

    print("\n    Cleaning stale versions...")
    delete_stale_versions(sc, handle_base, versioned_handle)
    # Remove legacy unversioned handle if it exists
    data = sc.get(f"/pages.json?handle={handle_base}&limit=1")
    if data.get("pages"):
        sc.delete(f"/pages/{data['pages'][0]['id']}.json")
        print(f"    🗑  deleted legacy unversioned handle={handle_base}")

    print("\n" + "=" * 64)
    print(f"DONE — reporte publicado:")
    print(f"  https://spekgen.com/{handle_base}")
    print("=" * 64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", required=True,
                    help="Ruta al JSON con el context dict del reporte")
    ap.add_argument("--template", default="monthly_report.html.j2")
    ap.add_argument("--handle", required=True,
                    help="Handle público limpio (ej. hc-reporte-marzo-abril)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="Solo renderea local sin publicar")
    args = ap.parse_args()

    context_path = Path(args.context).resolve()
    if not context_path.exists():
        # fallback: relative to skill dir
        context_path = (SKILL_DIR / args.context).resolve()
    if not context_path.exists():
        print(f"ERROR: context no existe: {args.context}")
        sys.exit(1)

    publish(
        context_path=context_path,
        template_name=args.template,
        handle_base=args.handle.lower().strip().strip("/"),
        title=args.title,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
