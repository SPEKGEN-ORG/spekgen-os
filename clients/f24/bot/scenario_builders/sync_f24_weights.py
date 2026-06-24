#!/usr/bin/env python3
"""Sincroniza el PESO REAL por SKU desde el Google Sheet INVENTARIO F24 a Shopify.

SOURCE OF TRUTH: Sheet "INVENTARIO F24" (1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U),
pestaña "📦 STOCK Y PROMOS", columna R "Peso real (kg)". El equipo de F24 llena/corrige el
peso ahí (donde ya trabajan); este script lo empuja a Shopify (variant weight). El motor de
guía `f24-generate-guide` usa ese peso para cotizar y generar la guía correcta.

Por qué este flujo: Shopify trae pesos a veces mal importados (ej. navajas en "5kg"). El
equipo corrige los sospechosos en el sheet; aquí se propagan a la fuente (Shopify) y de ahí
al envío. Las dimensiones las maneja el motor por perfiles de categoría (Shopify no las guarda).

    /usr/bin/python3 sync_f24_weights.py            # dry-run (preview del diff)
    /usr/bin/python3 sync_f24_weights.py --apply     # aplica a Shopify

Solo toca SKUs con "Peso real (kg)" lleno y distinto del de Shopify. Filas vacías = se ignoran
(quedan con lo que ya tenga Shopify + la red de seguridad del motor).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
F24_ROOT = SCRIPT_DIR.parent.parent  # .../F24- FERRE24
_ws = sorted(F24_ROOT.glob("F24 - 04. WEBSITE*/01. LIVE BUILD/scripts/shopify_client.py"))
SHOPIFY_SCRIPTS = _ws[0].parent if _ws else (F24_ROOT / "F24 - 04. WEBSITE" / "01. LIVE BUILD" / "scripts")
sys.path.insert(0, str(SHOPIFY_SCRIPTS))

SHEET_ID = "1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U"
STOCK_TAB = "📦 STOCK Y PROMOS"
COL_SKU = 0   # A
COL_PESO = 17  # R (0-indexed)

SA_REL = "HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/config/spekgen_service_account.json"


def find_sa() -> Path | None:
    envp = os.environ.get("GOOGLE_SA_PATH")
    if envp and Path(envp).exists():
        return Path(envp)
    for p in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        c = p / SA_REL
        if c.exists():
            return c
    return None


def parse_kg(s):
    s = str(s or "").strip().replace("kg", "").replace(",", ".").strip()
    if not s:
        return None
    try:
        kg = round(float(s), 3)
        return kg if kg > 0 else None
    except ValueError:
        return None


def read_sheet_weights() -> list[dict]:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    sa = find_sa()
    if not sa:
        raise SystemExit("No encontré el service account de Sheets.")
    creds = service_account.Credentials.from_service_account_file(
        str(sa), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"{STOCK_TAB}!A2:R").execute().get("values", [])
    out = []
    for r in vals:
        r = (r + [""] * 18)[:18]
        sku = str(r[COL_SKU]).strip()
        kg = parse_kg(r[COL_PESO])
        if sku and kg is not None:
            out.append({"sku": sku, "kg": kg})
    return out


def sku_variant(sc, sku: str):
    q = sku.replace('"', '\\"')
    d = sc.graphql(
        'query($q:String!){ productVariants(first:1, query:$q){ edges{ node{ id '
        'product{ id title } inventoryItem{ id measurement{ weight{ value unit } } } } } } }',
        variables={"q": f"sku:{q}"})
    edges = (d.get("productVariants", {}) or {}).get("edges", [])
    if not edges:
        return None
    n = edges[0]["node"]
    w = (((n.get("inventoryItem") or {}).get("measurement") or {}).get("weight") or {})
    return {
        "variant_gid": n["id"],
        "product_gid": n["product"]["id"],
        "title": n["product"].get("title", ""),
        "weight_value": w.get("value"),
        "weight_unit": w.get("unit"),
    }


def set_variant_weight(sc, product_gid: str, variant_gid: str, kg: float):
    """productVariantsBulkUpdate con inventoryItem.measurement.weight (KILOGRAMS)."""
    var = {"id": variant_gid, "inventoryItem": {"measurement": {"weight": {"value": kg, "unit": "KILOGRAMS"}}}}
    d = sc.graphql(
        """mutation($pid:ID!,$vars:[ProductVariantsBulkInput!]!){
             productVariantsBulkUpdate(productId:$pid, variants:$vars){
               productVariants{ id inventoryItem{ measurement{ weight{ value unit } } } }
               userErrors{ field message }
             }
           }""",
        variables={"pid": product_gid, "vars": [var]})
    errs = (d.get("productVariantsBulkUpdate", {}) or {}).get("userErrors", [])
    if errs:
        raise RuntimeError(f"Shopify userErrors {variant_gid}: {errs}")
    return d["productVariantsBulkUpdate"]["productVariants"][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Aplica a Shopify. Sin esto = dry-run.")
    args = ap.parse_args()
    dry = not args.apply

    print("DRY-RUN (preview)" if dry else "APPLY (escribe peso a Shopify)")
    print(f"Source of truth: Sheet INVENTARIO F24 / '{STOCK_TAB}' col R\n")

    rows = read_sheet_weights()
    print(f"SKUs con 'Peso real (kg)' lleno en el sheet: {len(rows)}\n")

    import shopify_client as sc  # noqa
    print(f"Shopify: {sc.SHOP}\n")
    print(f"{'SKU':<16}{'sheet kg':>10}{'shopify kg':>12}  acción")
    print("-" * 60)
    changes = []
    for r in sorted(rows, key=lambda x: x["sku"]):
        v = sku_variant(sc, r["sku"])
        if not v:
            print(f"{r['sku']:<16}{r['kg']:>10}{'—':>12}  (no está en Shopify)")
            continue
        cur = v["weight_value"]
        same = (cur is not None) and abs(float(cur) - r["kg"]) < 0.001
        action = "ya está" if same else "SET peso"
        print(f"{r['sku']:<16}{r['kg']:>10}{(cur if cur is not None else '—'):>12}  {action}")
        if not same:
            changes.append((r["sku"], v["product_gid"], v["variant_gid"], r["kg"]))

    print(f"\nResumen: {len(rows)} con peso en sheet | {len(changes)} a actualizar en Shopify.")
    if dry:
        print("\n(DRY-RUN: no se escribió nada. Corre con --apply para aplicar.)")
        return
    for sku, pgid, vgid, kg in changes:
        res = set_variant_weight(sc, pgid, vgid, kg)
        w = (((res.get("inventoryItem") or {}).get("measurement") or {}).get("weight") or {})
        print(f"  ✓ {sku}: peso -> {w.get('value')} {w.get('unit')}")
    print(f"\n✅ {len(changes)} pesos sincronizados a Shopify.")


if __name__ == "__main__":
    main()
