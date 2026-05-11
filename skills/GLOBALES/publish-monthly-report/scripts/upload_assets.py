#!/usr/bin/env python3
"""Uploads local assets to Shopify Files CDN, caches URLs in JSON.

Usage:
    python3 upload_assets.py <assets_manifest.json> [--cache cache.json]

assets_manifest.json:
    {"alias": "absolute/path/to/file.png", ...}

Output cache.json:
    {"alias": "https://cdn.shopify.com/s/files/..."}
"""
import argparse, json, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
AGENCY_DIR = SKILL_DIR.parent.parent.parent
sys.path.insert(0, str(AGENCY_DIR / "_CONTENT_HUB_SHOPIFY"))
sys.path.insert(0, str(AGENCY_DIR / "PROSPECTOS"))

from shopify_client import ShopifyClient  # noqa: E402
from _publish_prospect import upload_to_shopify_files, file_hash  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--cache", default=str(SKILL_DIR / "assets_cache.json"))
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    cache_path = Path(args.cache)
    cache = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text())

    sc = ShopifyClient()
    out = {}
    for alias, abs_path in manifest.items():
        p = Path(abs_path)
        if not p.exists():
            print(f"  ✗ MISSING: {alias} → {abs_path}")
            continue
        key = f"{alias}:{file_hash(p)}"
        if key in cache:
            out[alias] = cache[key]
            print(f"  ✓ cached   {alias}")
            continue
        print(f"  ↑ uploading {alias} ({p.name}, {p.stat().st_size // 1024} KB)")
        url = upload_to_shopify_files(sc, p, alt=alias)
        cache[key] = url
        out[alias] = url
        cache_path.write_text(json.dumps(cache, indent=2))
        print(f"    → {url}")

    urls_out = SKILL_DIR / "assets_urls.json"
    urls_out.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nWrote URLs to {urls_out}")


if __name__ == "__main__":
    main()
