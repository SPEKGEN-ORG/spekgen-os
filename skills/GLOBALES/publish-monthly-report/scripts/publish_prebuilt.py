#!/usr/bin/env python3
"""Publish a pre-built HTML report (already has gallery injected) to Shopify."""

import hashlib
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
AGENCY_DIR = SKILL_DIR.parent.parent.parent

sys.path.insert(0, str(AGENCY_DIR / "_CONTENT_HUB_SHOPIFY"))
sys.path.insert(0, str(AGENCY_DIR / "PROSPECTOS"))
sys.path.insert(0, str(AGENCY_DIR / "PROSPECTOS" / "mockup_factory"))

from shopify_client import ShopifyClient
from _publish_prospect import (
    CHROME_HIDER_CSS,
    rename_colliding_classes,
    extract_body_with_head,
    upsert_page,
    upsert_redirect,
    delete_stale_versions,
)

HTML_PATH = SKILL_DIR / "reports" / "gr-reporte-abril.html"
HANDLE_BASE = "gr-reporte-abril"
TITLE = "GREENRAY · Reporte Abril 2026"

print(f"[1/4] Leyendo HTML pre-generado ({HTML_PATH.stat().st_size // 1024} KB)")
html = HTML_PATH.read_text(encoding="utf-8")

print("[2/4] Preparando HTML para Shopify (namespace fixes + chrome hider)")
html = rename_colliding_classes(html)
body = CHROME_HIDER_CSS + extract_body_with_head(html)
print(f"    body size: {len(body) / 1024:.0f} KB")

print("[3/4] Auth Shopify...")
sc = ShopifyClient()
info = sc.graphql("{ shop { name primaryDomain { url } } }")
print(f"    ✓ {info['shop']['name']} ({info['shop']['primaryDomain']['url']})")

print("[4/4] Publicando página + redirect")
body_hash = hashlib.sha256(body.encode()).hexdigest()[:6]
versioned_handle = f"{HANDLE_BASE}-v{body_hash}"
upsert_page(sc, versioned_handle, TITLE, body)
upsert_redirect(sc, f"/{HANDLE_BASE}", f"/pages/{versioned_handle}")

print("    Limpiando versiones anteriores...")
delete_stale_versions(sc, HANDLE_BASE, versioned_handle)
data = sc.get(f"/pages.json?handle={HANDLE_BASE}&limit=1")
if data.get("pages"):
    sc.delete(f"/pages/{data['pages'][0]['id']}.json")
    print(f"    eliminado handle sin versión: {HANDLE_BASE}")

print("\n" + "=" * 64)
print(f"PUBLICADO: https://spekgen.com/{HANDLE_BASE}")
print(f"Handle versionado: {versioned_handle}")
print("=" * 64)
