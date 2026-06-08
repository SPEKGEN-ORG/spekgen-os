#!/usr/bin/env python3
"""Sincroniza el INVENTARIO de Ferre24 desde el Sheet a Shopify + al knowledge del bot.

SOURCE OF TRUTH: Sheet INVENTARIO F24 (1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U),
pestaña "📦 STOCK Y PROMOS", columnas: SKU (A), Stock disponible (F), ¿Disponible? (G).

Para cada SKU que exista en Shopify (por SKU en la variante):
  - Asegura inventoryItem.tracked = true  y  inventoryPolicy = DENY
    (así Shopify marca "agotado" y deja de venderse cuando llega a 0).
  - Setea la cantidad on-hand en la única location = Stock del Sheet
    (0 si ¿Disponible? = No, sin importar el número).
Y escribe F24_BOT_KNOWLEDGE/inventory.json {SKU: {qty, available}} para que el bot
sepa si HAY o NO un producto (no para decir cantidades exactas al cliente).

Dry-run por defecto; --apply para escribir. Tolerante: SKUs sin match se reportan y omiten.

    /usr/bin/python3 sync_f24_inventory.py            # preview
    /usr/bin/python3 sync_f24_inventory.py --apply
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
F24_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(F24_ROOT / "F24 - 04. WEBSITE (1)" / "01. LIVE BUILD" / "scripts"))
OUT_DIR = SCRIPT_DIR / "F24_BOT_KNOWLEDGE"
INV_JSON = OUT_DIR / "inventory.json"

SHEET_ID = "1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U"
STOCK_TAB = "📦 STOCK Y PROMOS"
SA_REL = "HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/config/spekgen_service_account.json"


def find_sa():
    envp = os.environ.get("GOOGLE_SA_PATH")
    if envp and Path(envp).exists():
        return envp
    for p in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        c = p / SA_REL
        if c.exists():
            return str(c)
    raise SystemExit("No encontré el service account.")


def read_stock():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        find_sa(), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"{STOCK_TAB}!A2:G").execute().get("values", [])
    out = []
    for r in vals:
        if not r or not str(r[0]).strip():
            continue
        r = (list(r) + [""] * 7)[:7]
        sku = str(r[0]).strip()
        stock_raw = str(r[5]).strip()
        disp = str(r[6]).strip().lower()
        # desired qty: 0 si ¿Disponible?=No; si hay número usa el número; si no hay dato → None (omitir)
        if disp in ("no", "false"):
            qty = 0
        elif stock_raw == "":
            qty = None
        else:
            try:
                qty = max(0, int(float(stock_raw.replace(",", ""))))
            except ValueError:
                qty = None
        out.append({"sku": sku, "qty": qty, "disp": disp})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    dry = not args.apply
    import shopify_client as sc

    print("DRY-RUN (preview)" if dry else "APPLY (escribe a Shopify + inventory.json)")
    rows = read_stock()
    have_data = [r for r in rows if r["qty"] is not None]
    print(f"STOCK Y PROMOS: {len(rows)} filas | con dato de inventario: {len(have_data)}\n")

    loc = sc.graphql("{ locations(first:1){ edges{ node{ id name } } } }")["locations"]["edges"][0]["node"]
    LOC = loc["id"]
    print(f"Location: {loc['name']} ({LOC})\n")

    inv_knowledge, changes, unmatched = {}, [], []
    track_fix = policy_fix = qty_fix = 0

    for r in have_data:
        sku = r["sku"]
        d = sc.graphql(
            'query($q:String!){productVariants(first:1,query:$q){edges{node{id inventoryPolicy inventoryQuantity inventoryItem{id tracked} product{id}}}}}',
            {"q": f'sku:"{sku}"'})
        e = d["productVariants"]["edges"]
        if not e:
            unmatched.append(sku)
            continue
        n = e[0]["node"]
        want_qty = r["qty"]
        cur_qty = n.get("inventoryQuantity") or 0
        tracked = n["inventoryItem"]["tracked"]
        policy = n["inventoryPolicy"]
        need_track = not tracked
        need_policy = policy != "DENY"
        need_qty = cur_qty != want_qty
        if need_track: track_fix += 1
        if need_policy: policy_fix += 1
        if need_qty: qty_fix += 1
        inv_knowledge[sku.upper()] = {"qty": want_qty, "available": want_qty > 0}
        if need_track or need_policy or need_qty:
            changes.append({
                "sku": sku, "pid": n["product"]["id"], "vid": n["id"],
                "inv_item": n["inventoryItem"]["id"],
                "want_qty": want_qty, "cur_qty": cur_qty,
                "need_track": need_track, "need_policy": need_policy, "need_qty": need_qty,
            })

    print(f"Matchean en Shopify: {len(inv_knowledge)} | SIN match (omitidos): {len(unmatched)}")
    print(f"Cambios a aplicar: tracking→on={track_fix} | policy→DENY={policy_fix} | cantidad={qty_fix}")
    agotados = [s for s, v in inv_knowledge.items() if not v["available"]]
    print(f"Quedarían AGOTADOS (qty 0): {len(agotados)} → {agotados[:12]}{'...' if len(agotados)>12 else ''}")
    if unmatched:
        print(f"\nSIN match (primeros 15): {unmatched[:15]}")

    if dry:
        print("\n(DRY-RUN: no se escribió nada. Corre con --apply.)")
        return

    for c in changes:
        if c["need_track"]:
            sc.graphql('mutation($id:ID!){inventoryItemUpdate(id:$id,input:{tracked:true}){userErrors{message}}}',
                       {"id": c["inv_item"]})
        if c["need_policy"]:
            sc.graphql("""mutation($pid:ID!,$vars:[ProductVariantsBulkInput!]!){
                productVariantsBulkUpdate(productId:$pid,variants:$vars){userErrors{message}}}""",
                {"pid": c["pid"], "vars": [{"id": c["vid"], "inventoryPolicy": "DENY"}]})
        if c["need_qty"] or c["need_track"]:
            sc.graphql("""mutation($in:InventorySetOnHandQuantitiesInput!){
                inventorySetOnHandQuantities(input:$in){userErrors{message}}}""",
                {"in": {"reason": "correction",
                        "setQuantities": [{"inventoryItemId": c["inv_item"], "locationId": LOC, "quantity": c["want_qty"]}]}})
        print(f"  ✓ {c['sku']}: qty {c['cur_qty']}→{c['want_qty']}"
              + (" +track" if c["need_track"] else "") + (" +DENY" if c["need_policy"] else ""))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INV_JSON.write_text(json.dumps({"source": f"{SHEET_ID}/{STOCK_TAB}", "inventory": inv_knowledge},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ {INV_JSON.name} ({len(inv_knowledge)} SKUs) + {len(changes)} variantes actualizadas en Shopify.")


if __name__ == "__main__":
    main()
