#!/usr/bin/env python3
"""
validate_batch.py v3 — Valida batch.json + (opcional) pricing pre-flight.

Uso:
    python3 validate_batch.py {BATCH_DIR}
    python3 validate_batch.py {BATCH_DIR} --pricing-check
    python3 validate_batch.py {BATCH_DIR} --pricing-check --client LF
    python3 validate_batch.py {BATCH_DIR} --strict-v3

Detecta shape automáticamente:
  - v3 (dict con 'batch_id' + 'entries')  → validación nueva
  - v2 legacy (top-level array)           → validación back-compat

Pricing pre-flight (--pricing-check):
  1. Lee _buckets/{CLIENT}.json para shop_url + pricing_mechanic
  2. Pull live {shop_url}/products.json
  3. Compara cada precio en ad_copy/landing_url contra catálogo
  4. Aplica regla pack_2_discount_pct / pack_4_discount_pct si aplica
  5. Flag stock False
  6. Output: 0/N discrepancias + propuesta de fix

Exit 0 si OK, 1 si errores.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).parent.parent  # .../factory-batch/

# ============ V3 schema ============

CLIENTS_VALID = {"GR", "LF", "HC", "MG", "GIBRAN", "CROSS"}
ASPECTS_VALID = {"1:1", "4:5", "9:16", "1.91:1"}
AD_CODE_V3_PATTERN = re.compile(r"^[A-Z]{2}-[0-9]{3}_[A-Z0-9_]+$")  # LF-058_KIT_TRIO_LUPITA_RUTINA_AM
POST_ID_PATTERN = re.compile(r"^(MG|HC|GR|LF|GIBRAN)-[0-9]{3}[A-Z]?$")

ADS_REQUIRED_V3 = {
    "ad_code", "client", "format", "product",
    "concept_angle", "entity_id_signature", "aspect_ratio",
    "objective", "hook_text_on_image", "gemini_prompt",
    "ad_copy", "expected_outcome", "status",
}
ADS_REQUIRED_V2_LEGACY = {
    "ad_code", "client", "product", "format", "concept_angle",
    "entity_id_signature", "aspect_ratio", "objective",
    "hook_text_on_image", "gemini_prompt", "attachments",
    "ad_copy", "expected_outcome",
}

CONTENT_REQUIRED = {
    "post_id", "client", "pillar", "format", "funnel", "title",
    "concept_style", "publish_date", "publish_time",
    "hook", "slides", "caption", "cta_keyword",
}


def load_buckets(client: str) -> Optional[dict]:
    p = SKILL_DIR / "_buckets" / f"{client}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def detect_shape(data) -> str:
    """Returns 'v3' | 'v2' | 'content' | 'unknown'."""
    if isinstance(data, dict) and "batch_id" in data and "entries" in data:
        first = data["entries"][0] if data["entries"] else {}
        return "v3" if "ad_code" in first else ("content" if "post_id" in first else "v3")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            if "ad_code" in first:
                return "v2"
            if "post_id" in first:
                return "content_legacy"
    return "unknown"


# ============ V3 ads validation ============

def validate_ads_v3(batch_dir: Path, batch: dict, buckets_cfg: Optional[dict]) -> list[str]:
    errors = []
    entries = batch.get("entries", [])
    valid_buckets = set(buckets_cfg["buckets"].keys()) if buckets_cfg else None

    seen_codes = set()
    for i, ad in enumerate(entries):
        prefix = f"[ad {i}]"
        if not isinstance(ad, dict):
            errors.append(f"{prefix} debe ser objeto")
            continue

        missing = ADS_REQUIRED_V3 - set(ad.keys())
        if missing:
            errors.append(f"{prefix} campos faltantes: {sorted(missing)}")
            continue

        code = ad["ad_code"]
        prefix = f"[{code}]"
        if code in seen_codes:
            errors.append(f"{prefix} ad_code duplicado")
        seen_codes.add(code)

        if not AD_CODE_V3_PATTERN.match(code):
            errors.append(f"{prefix} ad_code no sigue patrón v3 {{CLIENT}}-{{NNN}}_DESCRIPTOR (ej. LF-058_KIT_TRIO_LUPITA)")

        if ad["client"] not in CLIENTS_VALID:
            errors.append(f"{prefix} client inválido: {ad['client']}")

        # Normalize format: strip parenthetical comments e.g. "OFFER (sin Lupita)" → "OFFER"
        format_norm = re.sub(r"\s*\(.*?\)\s*", "", ad["format"]).strip()
        if valid_buckets and format_norm not in valid_buckets:
            errors.append(f"{prefix} format/bucket inválido para cliente: '{ad['format']}' (normalizado: '{format_norm}'; válidos: {sorted(valid_buckets)})")

        if ad["aspect_ratio"] not in ASPECTS_VALID:
            errors.append(f"{prefix} aspect_ratio inválido: {ad['aspect_ratio']}")

        # ad_copy required fields
        ac = ad.get("ad_copy", {})
        for k in ("primary_text", "headline", "cta_type", "landing_url"):
            if not ac.get(k):
                errors.append(f"{prefix} ad_copy.{k} vacío")

        # extra_attachments paths exist if specified
        for att in ad.get("extra_attachments", []):
            if not (batch_dir / att).exists():
                errors.append(f"{prefix} attachment no existe: {att}")

        # Status valid
        valid_status = {"DRAFT", "READY_FOR_UPLOAD", "UPLOADED_PAUSED", "ACTIVE", "PAUSED", "DROPPED"}
        if ad.get("status") not in valid_status:
            errors.append(f"{prefix} status inválido: {ad.get('status')} (válidos: {sorted(valid_status)})")

        # If status=READY_FOR_UPLOAD or UPLOADED → final_image_path must exist
        if ad.get("status") in {"READY_FOR_UPLOAD", "UPLOADED_PAUSED", "ACTIVE", "PAUSED"}:
            img = ad.get("final_image_path")
            if not img:
                errors.append(f"{prefix} status={ad['status']} requiere final_image_path")
            elif not (batch_dir / img).exists():
                errors.append(f"{prefix} final_image_path no existe: {img}")

    return errors


# ============ V2 legacy ads validation ============

def validate_ads_v2_legacy(batch_dir: Path, ads: list) -> list[str]:
    errors = []
    seen_codes = set()
    AD_CODE_V2_PATTERN = re.compile(r"^(GR|LF|HC|MG)-AD-[0-9]{3}[A-Z]?(_[A-Z0-9_]+)+$")
    for i, ad in enumerate(ads):
        prefix = f"[ad {i}]"
        if not isinstance(ad, dict):
            errors.append(f"{prefix} debe ser objeto")
            continue
        missing = ADS_REQUIRED_V2_LEGACY - set(ad.keys())
        if missing:
            errors.append(f"{prefix} (v2 legacy) campos faltantes: {sorted(missing)}")
            continue
        code = ad["ad_code"]
        prefix = f"[{code}]"
        if code in seen_codes:
            errors.append(f"{prefix} duplicado")
        seen_codes.add(code)
        if not AD_CODE_V2_PATTERN.match(code):
            errors.append(f"{prefix} ad_code v2 pattern fail")
    return errors


# ============ Pricing pre-flight ============

def fetch_live_catalog(shop_url: str) -> dict:
    """Returns dict: handle → variant info."""
    import urllib.request
    url = f"{shop_url.rstrip('/')}/products.json?limit=250"
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.loads(r.read())
    catalog = {}
    for p in data.get("products", []):
        v = p["variants"][0] if p.get("variants") else {}
        catalog[p["handle"]] = {
            "title": p["title"],
            "price": float(v.get("price", 0)),
            "compare_at_price": float(v["compare_at_price"]) if v.get("compare_at_price") else None,
            "available": all(vv.get("available", False) for vv in p.get("variants", [])),
        }
    return catalog


PRICE_PATTERN = re.compile(r"\$([\d,]+(?:\.\d{1,2})?)")
HANDLE_FROM_URL = re.compile(r"/products/([a-z0-9-]+)")
# Detect "savings" context: $X preceded by "ahorr*" or "save" within 30 chars
SAVINGS_CONTEXT = re.compile(r"(ahorr[ao]s?|save|descuento)\D{0,30}\$([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)


def extract_prices_from_ad(ad: dict) -> dict:
    """Extract claimed prices vs savings amounts from ad_copy."""
    ac = ad.get("ad_copy", {})
    blob = " ".join([
        ac.get("headline", ""),
        ac.get("description", ""),
        ac.get("primary_text", ""),
        ad.get("hook_text_on_image", ""),
        ad.get("product", ""),
    ])
    # First find savings amounts to exclude from price list
    savings = set()
    for m in SAVINGS_CONTEXT.finditer(blob):
        try:
            savings.add(float(m.group(2).replace(",", "")))
        except ValueError:
            pass
    # All $X amounts
    all_amounts = []
    for m in PRICE_PATTERN.finditer(blob):
        try:
            all_amounts.append(float(m.group(1).replace(",", "")))
        except ValueError:
            pass
    # Prices = amounts NOT in savings set
    prices = sorted(set(a for a in all_amounts if a not in savings), reverse=True)

    handle_match = HANDLE_FROM_URL.search(ac.get("landing_url", ""))
    handle = handle_match.group(1) if handle_match else None
    return {"prices": prices, "savings": sorted(savings, reverse=True), "handle": handle}


def pricing_check(batch: dict, buckets_cfg: dict) -> list[str]:
    """Validate every ad's prices vs live catalog using pack mechanic."""
    issues = []
    shop_url = buckets_cfg["shop_url"]
    pack_2_pct = buckets_cfg["pricing_mechanic"]["pack_2_discount_pct"] / 100
    pack_4_pct = buckets_cfg["pricing_mechanic"]["pack_4_discount_pct"] / 100
    out_of_stock = set(buckets_cfg.get("out_of_stock_excluded", []))

    print(f"[pricing] Pulling live catalog: {shop_url}")
    catalog = fetch_live_catalog(shop_url)
    print(f"[pricing] Catalog: {len(catalog)} products. Mechanic: Pack 2 -{pack_2_pct*100:.0f}% / Pack 4 -{pack_4_pct*100:.0f}%")

    entries = batch.get("entries", [])
    for ad in entries:
        if ad.get("status") == "DROPPED":
            continue
        code = ad["ad_code"]
        product = ad.get("product", "")
        extracted = extract_prices_from_ad(ad)
        prices_in_ad = extracted["prices"]
        savings_in_ad = extracted["savings"]
        handle = extracted["handle"]

        # Check stock by product name (heuristic)
        for oos in out_of_stock:
            if oos.lower() in product.lower():
                issues.append(f"[{code}] PRODUCTO AGOTADO en catálogo live: '{oos}' aparece en product='{product}' — no usar")
                break

        if not handle:
            issues.append(f"[{code}] No pude extraer handle de landing_url — saltando price check")
            continue
        if handle not in catalog:
            issues.append(f"[{code}] handle '{handle}' NO existe en catálogo live")
            continue

        live = catalog[handle]
        if not live["available"]:
            issues.append(f"[{code}] '{live['title']}' está agotado en Shopify (available=False)")

        if not prices_in_ad:
            continue  # no prices in ad, OK

        single = live["price"]
        valid_targets = {round(single, 2)}
        if buckets_cfg["pricing_mechanic"].get("kits_have_fixed_price") and "kit" in product.lower():
            # Kit: only single price + maybe compare_at
            if live["compare_at_price"]:
                valid_targets.add(round(live["compare_at_price"], 2))
        else:
            # Non-kit: pack 2 + pack 4 valid
            valid_targets.add(round(single * 2 * (1 - pack_2_pct), 2))
            valid_targets.add(round(single * 4 * (1 - pack_4_pct), 2))
            valid_targets.add(round(single * 2, 2))  # original 2x for compare_at story
            valid_targets.add(round(single * 4, 2))  # original 4x for compare_at story
            if live["compare_at_price"]:
                valid_targets.add(round(live["compare_at_price"], 2))

        for p in prices_in_ad:
            # Allow 1% tolerance
            matched = any(abs(p - t) / max(t, 1) < 0.01 for t in valid_targets)
            if not matched:
                fix_options = ", ".join(f"${t:,.2f}" for t in sorted(valid_targets, reverse=True))
                issues.append(f"[{code}] Precio ${p:,.2f} en ad NO cuadra con catálogo. Single=${single:.2f}. Válidos: {fix_options}")

        # Validate savings amounts: should equal single * pct (for pack mechanic)
        if not (buckets_cfg["pricing_mechanic"].get("kits_have_fixed_price") and "kit" in product.lower()):
            valid_savings = {
                round(single * 2 * pack_2_pct, 2),  # Pack 2 savings
                round(single * 4 * pack_4_pct, 2),  # Pack 4 savings
            }
            if live["compare_at_price"]:
                valid_savings.add(round(live["compare_at_price"] - single, 2))
            for s in savings_in_ad:
                matched = any(abs(s - t) / max(t, 1) < 0.02 for t in valid_savings)
                if not matched:
                    sopts = ", ".join(f"${t:,.2f}" for t in sorted(valid_savings, reverse=True))
                    issues.append(f"[{code}] Ahorro ${s:,.2f} no cuadra con mecánica Pack. Válidos: {sopts}")

    return issues


# ============ Content validation (v2 legacy, mantengo) ============

def validate_content(batch_dir: Path, posts: list) -> list[str]:
    errors = []
    seen_ids = set()
    for i, post in enumerate(posts):
        prefix = f"[post {i}]"
        if not isinstance(post, dict):
            errors.append(f"{prefix} debe ser objeto")
            continue
        missing = CONTENT_REQUIRED - set(post.keys())
        if missing:
            errors.append(f"{prefix} campos faltantes: {sorted(missing)}")
            continue
        pid = post["post_id"]
        prefix = f"[{pid}]"
        if pid in seen_ids:
            errors.append(f"{prefix} duplicado")
        seen_ids.add(pid)
        if not POST_ID_PATTERN.match(pid):
            errors.append(f"{prefix} post_id pattern fail")
    return errors


# ============ Main ============

def find_batch_json(batch_dir: Path) -> Optional[Path]:
    for candidate in ("batch.json", "ads_batch.json"):
        p = batch_dir / candidate
        if p.exists():
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    ap.add_argument("--pricing-check", action="store_true", help="Pull live catalog y valida precios contra _buckets/{CLIENT}.json")
    ap.add_argument("--client", help="Override client (auto-detected from batch.json normally)")
    ap.add_argument("--strict-v3", action="store_true", help="Reject v2 legacy shape")
    args = ap.parse_args()

    batch_dir = Path(args.batch_dir).expanduser().resolve()
    json_path = find_batch_json(batch_dir)
    if not json_path:
        print(f"❌ No batch.json en {batch_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido: {e}", file=sys.stderr)
        sys.exit(1)

    shape = detect_shape(data)
    print(f"[validate] Shape detectada: {shape}")
    errors = []

    if shape == "v3":
        client = args.client or data.get("client")
        if not client:
            errors.append("client missing en batch.json (required for v3)")
        buckets_cfg = load_buckets(client) if client else None
        if not buckets_cfg and client and client != "CROSS":
            errors.append(f"_buckets/{client}.json no existe — crear antes de validar v3 strict")
        errors += validate_ads_v3(batch_dir, data, buckets_cfg)
        if args.pricing_check and buckets_cfg:
            print(f"\n[pricing-check] Iniciando para client={client}...")
            pricing_issues = pricing_check(data, buckets_cfg)
            if pricing_issues:
                print(f"\n[pricing-check] {len(pricing_issues)} discrepancias:")
                for p in pricing_issues:
                    print(f"  ⚠ {p}")
                errors += [f"PRICING: {p}" for p in pricing_issues]
            else:
                print("[pricing-check] ✅ 0 discrepancias")
    elif shape == "v2":
        if args.strict_v3:
            errors.append("v2 legacy shape rejected (--strict-v3)")
        else:
            print("[validate] ⚠ v2 legacy — usa shape vieja, considera migrar a v3")
            errors += validate_ads_v2_legacy(batch_dir, data)
    elif shape in ("content", "content_legacy"):
        posts = data.get("entries", data) if isinstance(data, dict) else data
        errors += validate_content(batch_dir, posts)
    else:
        errors.append("Shape no detectable (esperado: v3 dict con batch_id+entries, v2 array con ad_code, o content array con post_id)")

    if errors:
        print(f"\n[validate] ❌ {len(errors)} errores:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"\n[validate] ✅ OK — batch {batch_dir.name} válido")


if __name__ == "__main__":
    main()
