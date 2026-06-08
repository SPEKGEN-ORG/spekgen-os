#!/usr/bin/env python3
"""Reconcilia las PROMOS ACTIVAS de Ferre24 desde el Google Sheet de inventario.

SOURCE OF TRUTH: Sheet "INVENTARIO F24" (1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U),
pestaña "🔥 PROMO ACTIVA". El equipo de F24 marca promos en "📦 STOCK Y PROMOS" y esa
pestaña se auto-llena. Este script la lee y:

  1. Filtra a promos VIGENTES (hoy <= Vigencia fin, formato dd/mm/yyyy).
  2. Escribe F24_BOT_KNOWLEDGE/promos_active.json (lo consume build_f24_knowledge.py
     para el knowledge del bot — precio promo + escalera MSI + elegibilidad 9/12).
  3. Sincroniza precios a Shopify SOLO en SKUs con "Precio Promo":
        variant.price = Precio Promo   ·   variant.compareAtPrice = Precio (regular)
     y revierte (price = regular, compareAt = null) los SKUs que salieron de promo,
     usando _promo_state.json para saber a qué revertir.

Por defecto corre en DRY-RUN (no escribe nada en Shopify, solo muestra el diff).
Para aplicar: --apply

    /usr/bin/python3 sync_f24_promos.py            # dry-run (preview)
    /usr/bin/python3 sync_f24_promos.py --apply     # aplica a Shopify + escribe json/state

Notas:
  - Cuenta B (9/12 MSI) = solo SKUs cuya escalera "Meses MSI" incluye 9 o 12.
  - SKUs en promo SIN "Precio Promo" = promo de solo-MSI (no se toca el precio Shopify).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
F24_ROOT = SCRIPT_DIR.parent.parent  # .../F24- FERRE24
SHOPIFY_SCRIPTS = F24_ROOT / "F24 - 04. WEBSITE (1)" / "01. LIVE BUILD" / "scripts"
sys.path.insert(0, str(SHOPIFY_SCRIPTS))

OUT_DIR = SCRIPT_DIR / "F24_BOT_KNOWLEDGE"
PROMOS_JSON = OUT_DIR / "promos_active.json"
STATE_PATH = SCRIPT_DIR / "_promo_state.json"

SHEET_ID = "1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U"
PROMO_TAB = "🔥 PROMO ACTIVA"
# Tag que marca los productos elegibles a 9/12 MSI (ruta MercadoPago Cuenta B). El edge
# function f24-process-order exige este tag para permitir payment_method=msi_promo.
MSI912_TAG = "msi-912"
# Columnas: SKU | Producto | Precio | Meses MSI | % Desc | Precio Promo | Vigencia (fin) | Estado Landing
COL = {"sku": 0, "producto": 1, "precio": 2, "msi": 3, "pct": 4, "promo": 5, "vig": 6, "landing": 7}

SA_REL = "HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/config/spekgen_service_account.json"


def find_sa() -> Path | None:
    # Cloud (GitHub Actions): el SA se escribe a un archivo y su ruta viene en GOOGLE_SA_PATH.
    envp = os.environ.get("GOOGLE_SA_PATH")
    if envp and Path(envp).exists():
        return Path(envp)
    for p in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        c = p / SA_REL
        if c.exists():
            return c
    return None


def parse_money(s: str):
    """'$3,261.92' -> 3261.92 ; '' -> None"""
    s = (s or "").strip().replace("$", "").replace(",", "")
    if not s:
        return None
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def parse_msi_ladder(s: str) -> list[int]:
    """'3, 6, 9, 12' -> [3,6,9,12]"""
    return sorted({int(x) for x in re.findall(r"\d+", s or "")})


def parse_vig(s: str):
    """'14/06/2026' -> date(2026,6,14) ; tolera ISO y vacío."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def read_promo_active() -> list[dict]:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    sa = find_sa()
    if not sa:
        raise SystemExit("No encontré el service account de Sheets.")
    creds = service_account.Credentials.from_service_account_file(
        str(sa), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"{PROMO_TAB}!A2:H").execute().get("values", [])
    today = date.today()
    rows = []
    for r in vals:
        r = (r + [""] * 8)[:8]
        sku = str(r[COL["sku"]]).strip()
        if not sku:
            continue
        ladder = parse_msi_ladder(r[COL["msi"]])
        vig = parse_vig(r[COL["vig"]])
        regular = parse_money(r[COL["precio"]])
        promo = parse_money(r[COL["promo"]])
        rows.append({
            "sku": sku,
            "sku_upper": sku.upper(),
            "producto": str(r[COL["producto"]]).strip(),
            "regular_price": regular,
            "promo_price": promo,
            "pct_desc": str(r[COL["pct"]]).strip(),
            "msi_ladder": ladder,
            "msi_max": max(ladder) if ladder else 0,
            "eligible_912": any(m in (9, 12) for m in ladder),
            "vigencia": vig.isoformat() if vig else "",
            "vigente": (vig is None) or (today <= vig),
            "estado_landing": str(r[COL["landing"]]).strip(),
        })
    return rows


# ---------------- Shopify ----------------

def sku_variant(sc, sku: str):
    """Devuelve {variant_gid, price, compare_at} del SKU, o None."""
    q = sku.replace('"', '\\"')
    d = sc.graphql(
        'query($q:String!){ productVariants(first:1, query:$q){ edges{ node{ id price compareAtPrice product{ id title } } } } }',
        variables={"q": f"sku:{q}"})
    edges = (d.get("productVariants", {}) or {}).get("edges", [])
    if not edges:
        return None
    n = edges[0]["node"]
    return {
        "variant_gid": n["id"],
        "product_gid": n["product"]["id"],
        "title": n["product"].get("title", ""),
        "price": n.get("price"),
        "compare_at": n.get("compareAtPrice"),
    }


def set_variant_price(sc, product_gid: str, variant_gid: str, price: float, compare_at):
    """productVariantsBulkUpdate: setea price y compareAtPrice (compare_at=None lo limpia)."""
    var = {"id": variant_gid, "price": f"{price:.2f}"}
    var["compareAtPrice"] = f"{compare_at:.2f}" if compare_at is not None else None
    d = sc.graphql(
        """mutation($pid:ID!,$vars:[ProductVariantsBulkInput!]!){
             productVariantsBulkUpdate(productId:$pid, variants:$vars){
               productVariants{ id price compareAtPrice }
               userErrors{ field message }
             }
           }""",
        variables={"pid": product_gid, "vars": [var]})
    errs = (d.get("productVariantsBulkUpdate", {}) or {}).get("userErrors", [])
    if errs:
        raise RuntimeError(f"Shopify userErrors {variant_gid}: {errs}")
    return d["productVariantsBulkUpdate"]["productVariants"][0]


def set_product_tag(sc, product_gid: str, tag: str, add: bool = True):
    """Agrega o quita un tag de un producto (idempotente)."""
    mut = "tagsAdd" if add else "tagsRemove"
    d = sc.graphql(
        f"mutation($id:ID!,$tags:[String!]!){{ {mut}(id:$id, tags:$tags){{ userErrors{{ message }} }} }}",
        variables={"id": product_gid, "tags": [tag]})
    errs = (d.get(mut, {}) or {}).get("userErrors", [])
    if errs:
        raise RuntimeError(f"{mut} {product_gid}: {errs}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Aplica cambios a Shopify + escribe json/state. Sin esto = dry-run.")
    args = ap.parse_args()
    dry = not args.apply

    print(f"{'DRY-RUN (preview, no escribe nada)' if dry else 'APPLY (escribe a Shopify + json/state)'}")
    print(f"Source of truth: Sheet INVENTARIO F24 / '{PROMO_TAB}'\n")

    rows = read_promo_active()
    vigentes = [r for r in rows if r["vigente"]]
    no_vig = [r for r in rows if not r["vigente"]]
    with_promo = [r for r in vigentes if r["promo_price"] is not None]
    msi_only = [r for r in vigentes if r["promo_price"] is None]
    cuenta_b = [r for r in vigentes if r["eligible_912"]]

    print(f"Filas en PROMO ACTIVA: {len(rows)}  |  vigentes: {len(vigentes)}  |  expiradas: {len(no_vig)}")
    print(f"  • con precio promo (sync Shopify): {len(with_promo)}")
    print(f"  • solo-MSI (precio sin cambio):    {len(msi_only)}")
    print(f"  • elegibles 9/12 (Cuenta B):       {len(cuenta_b)}\n")

    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}
    new_state = {}

    # cargar shopify y resolver TODA promo vigente contra Shopify (sellable = existe variante)
    import shopify_client as sc  # noqa
    print(f"Shopify: {sc.SHOP}\n")
    for r in vigentes:
        v = sku_variant(sc, r["sku"])
        r["in_shopify"] = bool(v)
        r["shopify_price"] = v["price"] if v else None
        r["variant_gid"] = v["variant_gid"] if v else None
        r["product_gid"] = v["product_gid"] if v else None

    sellable = [r for r in vigentes if r["in_shopify"]]            # el bot SOLO vende estos
    missing = [r for r in vigentes if not r["in_shopify"]]         # excluidos: aún sin PDP
    promo_sellable = [r for r in sellable if r["promo_price"] is not None]

    print(f"{'SKU':<16}{'regular':>11}{'promo':>11}{'%':>5}  {'MSI':<14}{'Shopify ahora':>16}  acción")
    print("-" * 96)
    changes = []  # (sku, product_gid, variant_gid, new_price, new_compare)
    for r in sorted(promo_sellable, key=lambda x: x["sku"]):
        ladder = ",".join(str(m) for m in r["msi_ladder"])
        cur = f"${float(r['shopify_price']):,.0f}" if r.get("shopify_price") else "—"
        want_price = r["promo_price"]
        want_cmp = r["regular_price"]
        already = (r.get("shopify_price") and abs(float(r["shopify_price"]) - want_price) < 0.01)
        action = "ya está" if already else "SET promo"
        print(f"{r['sku']:<16}{r['regular_price'] or 0:>11,.0f}{r['promo_price']:>11,.0f}{r['pct_desc']:>5}  {ladder:<14}{cur:>16}  {action}")
        new_state[r["sku_upper"]] = {"regular": want_cmp, "promo": want_price}
        if not already:
            changes.append((r["sku"], r["product_gid"], r["variant_gid"], want_price, want_cmp))

    if missing:
        print(f"\nEXCLUIDOS del bot ({len(missing)} no están en Shopify — el equipo debe subir su PDP):")
        for r in sorted(missing, key=lambda x: x["sku"]):
            print(f"  {r['sku']:<16} {r['producto'][:54]:<54} [{r['estado_landing']}]")

    # reverts: estaban en state pero ya no están en promo vendible con precio
    active_skus = {r["sku_upper"] for r in promo_sellable}
    reverts = [(sku_u, info) for sku_u, info in state.items() if sku_u not in active_skus]
    if reverts:
        print("\nREVERTIR (salieron de promo) — restaurar precio regular:")
        for sku_u, info in reverts:
            print(f"  {sku_u:<16} -> price ${info.get('regular',0):,.0f}, quitar tachado")

    print(f"\nResumen: {len(sellable)} vendibles | {len(missing)} excluidos | "
          f"{len(changes)} precio(s) a cambiar | {len(reverts)} a revertir.")

    if dry:
        print("\n(DRY-RUN: no se escribió nada. Corre con --apply para aplicar.)")
        return

    # APPLY — precios
    for sku, pgid, vgid, price, cmp in changes:
        res = set_variant_price(sc, pgid, vgid, price, cmp)
        print(f"  ✓ {sku}: price={res['price']} compareAt={res['compareAtPrice']}")
    for sku_u, info in reverts:
        v = sku_variant(sc, sku_u)
        if v:
            res = set_variant_price(sc, v["product_gid"], v["variant_gid"], float(info["regular"]), None)
            print(f"  ↩ {sku_u}: revertido a {res['price']}")

    # APPLY — tag msi-912 (gate de Cuenta B en el edge function)
    for r in sellable:
        set_product_tag(sc, r["product_gid"], MSI912_TAG, add=r["eligible_912"])
    print(f"  🏷  tag {MSI912_TAG}: +{sum(1 for r in sellable if r['eligible_912'])} / "
          f"-{sum(1 for r in sellable if not r['eligible_912'])}")
    for sku_u, _info in reverts:
        v = sku_variant(sc, sku_u)
        if v:
            set_product_tag(sc, v["product_gid"], MSI912_TAG, add=False)

    # Limpiar campos internos antes de serializar el knowledge
    def clean(r):
        return {k: v for k, v in r.items() if k not in ("product_gid", "variant_gid")}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROMOS_JSON.write_text(json.dumps({
        "source": f"{SHEET_ID}/{PROMO_TAB}",
        "generated": date.today().isoformat(),
        "note": "Solo promos VENDIBLES (existen en Shopify). El bot cotiza/vende únicamente estas.",
        "promos": [clean(r) for r in sellable],
        "excluidos_sin_pdp": [{"sku": r["sku"], "producto": r["producto"],
                                "estado_landing": r["estado_landing"]} for r in missing],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    STATE_PATH.write_text(json.dumps(new_state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ {PROMOS_JSON.name} ({len(sellable)} vendibles, {len(missing)} excluidos) + {STATE_PATH.name} escritos.")


if __name__ == "__main__":
    main()
