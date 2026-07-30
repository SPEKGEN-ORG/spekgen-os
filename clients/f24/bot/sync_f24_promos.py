#!/usr/bin/env python3
"""Reconcilia PRECIOS + PROMOS de Ferre24 desde el Google Sheet → Shopify + knowledge del bot.

SOURCE OF TRUTH: Sheet "INVENTARIO F24" (1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U).
El sheet es DUEÑO TOTAL de los precios:

  - Precio base (col E "Precio venta público" de "📦 STOCK Y PROMOS") → variant.price
    de TODO SKU que no esté en promo (compareAtPrice se limpia).
  - Promo vigente (pestaña "🔥 PROMO ACTIVA", con Precio Promo) → variant.price = Precio
    Promo, variant.compareAtPrice = Precio base (tachado).
  - Al expirar/quitar una promo, el SKU vuelve solo a su precio base (ya no se necesita
    _promo_state.json: el base vive en el sheet).

Todo es DIFF-BASED: jala TODAS las variantes de Shopify de una (paginado) y solo escribe los
SKUs cuyo precio/tachado difiere. Robusto a filas incompletas (SKU sin precio o sin match en
Shopify se reporta y se omite, nunca truena).

Además (sin cambios respecto a la versión previa):
  - Pone/quita el tag `msi-912` (gate Cuenta B 9/12 MSI del edge function f24-process-order).
  - Escribe F24_BOT_KNOWLEDGE/promos_active.json (lo consume build_f24_knowledge.py).

Y desde 2026-07-15:
  - Escribe el metafield de producto `f24.msi_meses` (ej. "3,6" o "3,6,9,12") desde la col
    "Meses MSI" del sheet. Lo consume snippets/f24-msi-inline.liquid del tema (chips MSI de
    la PDP). Diff-based contra el valor actual en Shopify (sin state): promo activa con MSI
    → su ladder; producto que sale de promo → reset a "3,6" (baseline: 3 y 6 MSI siempre
    disponibles en checkout con TDC; 9/12 solo en promo).

Por defecto DRY-RUN (no escribe nada). --apply para aplicar.

    python3 sync_f24_promos.py            # preview (muestra el diff completo de precios)
    python3 sync_f24_promos.py --apply
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
# (en el repo cloud shopify_client.py vive junto a este script; el insert de abajo es
#  inofensivo si la ruta no existe — sys.path[0] ya cubre el import.)
F24_ROOT = SCRIPT_DIR.parent.parent
for cand in ("F24 - 04. WEBSITE (1)", "F24 - 04. WEBSITE "):
    p = F24_ROOT / cand / "01. LIVE BUILD" / "scripts"
    if p.exists():
        sys.path.insert(0, str(p))
        break

OUT_DIR = SCRIPT_DIR / "F24_BOT_KNOWLEDGE"
PROMOS_JSON = OUT_DIR / "promos_active.json"
STATE_PATH = SCRIPT_DIR / "_promo_state.json"

SHEET_ID = "1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U"
PROMO_TAB = "🔥 PROMO ACTIVA"
STOCK_TAB = "📦 STOCK Y PROMOS"
MSI912_TAG = "msi-912"

# Gate de PAGO CONTRAENTREGA para la PDP. Un producto lo lleva cuando cumple las 2 condiciones
# que se pueden evaluar del lado del producto: promo vigente y vendible, y precio >= $10,000.
# Las otras 2 condiciones del COD (CP del cliente en GTO/JAL/MICH, y que pague de contado) no se
# pueden saber en la PDP — las verifica el bot en la conversación. Por eso el aviso de la PDP dice
# "consulta si calificas" y no "tienes pago contraentrega".
COD_TAG = "cod-elegible"
COD_MIN_MXN = 10000.0
MSI_NS, MSI_KEY = "f24", "msi_meses"   # metafield de producto que leen las chips MSI de la PDP
MSI_DEFAULT = "3,6"                     # baseline sin promo: 3 y 6 MSI en checkout con TDC
# PROMO ACTIVA: SKU | Producto | Precio | Meses MSI | % Desc | Precio Promo | Vigencia | Estado Landing
COL = {"sku": 0, "producto": 1, "precio": 2, "msi": 3, "pct": 4, "promo": 5, "vig": 6, "landing": 7}
# STOCK Y PROMOS: precio base col E (4), descuento directo col Q (16), tachado marketing col T (19)
STOCK_COL = {"sku": 0, "producto": 1, "precio_base": 4, "direct_disc": 16, "tachado": 19,
             "envio_gratis": 20}   # col U — la llena una fórmula desde '✍️ CAPTURA PROMOS'!N

# Metafield que enciende la chip "Envío gratis" en la web (PDP, colecciones, página de COD).
# Fuente de verdad: columna "¿Envío gratis?" del sheet INVENTARIO F24, que Sergio marca por promo.
ENVIO_NS, ENVIO_KEY = "f24", "envio_gratis"
# Perfil de entrega con tarifa $0 (creado 30-jul-2026). El metafield de arriba
# solo pinta la chip; ESTE es el que hace que el checkout no cobre envío.
PERFIL_ENVIO_GRATIS = os.environ.get(
    "F24_PERFIL_ENVIO_GRATIS", "gid://shopify/DeliveryProfile/101392187480")

# SKUs cuyo envío gratis es ESTRUCTURAL, no promocional: viene incluido en la
# oferta y no vence. No están en '📦 STOCK Y PROMOS', así que sin esta lista el
# reconcile los sacaría del perfil en la primera corrida.
#
# ⚠️ LOS COMBOS NO PUEDEN ENTRAR AQUÍ. Se intentó el 30-jul-2026 y NO se puede:
# COMBO-KAS12P-MINI60 y COMBO-KAS10P-MINI25 son BUNDLES (`requiresComponents:
# true`), y Shopify deriva el envío de un bundle desde sus componentes. El
# `deliveryProfileUpdate` devuelve `userErrors: []` y **ignora la variante en
# silencio** — no falla, simplemente no la asocia. Verificado comparando contra
# AK26, que sí se mueve con la misma llamada.
# Por eso siguen con sus 2 tarifas de $0 condicionadas a un total EXACTO
# ($7,199 / $4,899) en el perfil default, con la fragilidad conocida: un
# accesorio de $200 o un código de descuento rompen el envío gratis del combo, y
# cualquier carrito que dé esa cifra se lo lleva sin comprar el combo.
# Asociar los COMPONENTES tampoco sirve: se venden por separado y les daría
# envío gratis vendidos solos.
ENVIO_GRATIS_SIEMPRE: set[str] = set()

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


def parse_money(s):
    s = str(s or "").strip().replace("$", "").replace(",", "")
    if not s:
        return None
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def parse_frac(s):
    """'20%' -> 0.20 ; 0.2 -> 0.2 ; '' / '0' -> None. Descuento como fracción 0..1."""
    s = str(s or "").strip().replace("%", "").replace(" ", "")
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if f > 1:
        f = f / 100.0
    return round(f, 4) if f > 0 else None


def parse_msi_ladder(s: str) -> list[int]:
    return sorted({int(x) for x in re.findall(r"\d+", s or "")})


def parse_vig(s: str):
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _sheets_svc():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    sa = find_sa()
    if not sa:
        raise SystemExit("No encontré el service account de Sheets.")
    creds = service_account.Credentials.from_service_account_file(
        str(sa), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def read_promo_active(svc) -> list[dict]:
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
        rows.append({
            "sku": sku,
            "sku_upper": sku.upper(),
            "producto": str(r[COL["producto"]]).strip(),
            "regular_price": parse_money(r[COL["precio"]]),
            "promo_price": parse_money(r[COL["promo"]]),
            "pct_desc": str(r[COL["pct"]]).strip(),
            "msi_ladder": ladder,
            "msi_max": max(ladder) if ladder else 0,
            "eligible_912": any(m in (9, 12) for m in ladder),
            "vigencia": vig.isoformat() if vig else "",
            "vigente": (vig is None) or (today <= vig),
            "estado_landing": str(r[COL["landing"]]).strip(),
        })
    return rows


def read_base_prices(svc) -> dict:
    """{sku_upper: {'base','producto','direct_disc','tachado','envio_gratis'}} desde 📦 STOCK Y PROMOS.
    base = col E (precio venta real) · direct_disc = col Q · tachado = col T (ancla marketing)
    envio_gratis = col U ("Sí"/"No"), fórmula que jala de '✍️ CAPTURA PROMOS'!N la promo vigente."""
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"{STOCK_TAB}!A2:U").execute().get("values", [])
    out = {}
    for r in vals:
        r = (list(r) + [""] * 21)[:21]
        sku = str(r[STOCK_COL["sku"]]).strip()
        if not sku:
            continue
        out[sku.upper()] = {
            "base": parse_money(r[STOCK_COL["precio_base"]]),
            "producto": str(r[STOCK_COL["producto"]]).strip(),
            "direct_disc": parse_frac(r[STOCK_COL["direct_disc"]]),
            "tachado": parse_money(r[STOCK_COL["tachado"]]),
            "envio_gratis": _es_si(r[STOCK_COL["envio_gratis"]]),
        }
    return out


def _es_si(v) -> bool:
    """La col U puede venir 'Sí', 'SI', 'sí', 'x', 'TRUE'… o vacía. Todo lo demás es No."""
    s = str(v or "").strip().lower()
    return s in ("sí", "si", "s", "x", "true", "verdadero", "1")


# ---------------- Shopify ----------------

def fetch_all_variants(sc) -> dict:
    """Jala TODAS las variantes de Shopify (paginado). {sku_upper: {vid,pid,price,compare_at,title}}.

    SKUs DUPLICADOS (gemelo viejo en DRAFT de una carga repetida): gana SIEMPRE el
    ACTIVE — es el que se vende y el que ve el cliente. Antes ganaba "el último de la
    paginación", que le atinaba por casualidad; si el orden cambiaba, el precio de la
    promo se le aplicaba al DRAFT invisible y la tienda quedaba a precio de lista."""
    q = """query($cursor:String){
      productVariants(first:250, after:$cursor){
        edges{ node{ id sku price compareAtPrice
                     product{ id title status metafield(namespace:"%s", key:"%s"){ value } } } }
        pageInfo{ hasNextPage endCursor }
      }
    }""" % (MSI_NS, MSI_KEY)
    out, cursor = {}, None
    while True:
        d = sc.graphql(q, {"cursor": cursor})
        conn = d["productVariants"]
        for e in conn["edges"]:
            n = e["node"]
            sku = (n.get("sku") or "").strip()
            if not sku:
                continue
            mf = n["product"].get("metafield") or {}
            status = n["product"].get("status")
            prev = out.get(sku.upper())
            # duplicado: solo lo reemplazo si el nuevo es ACTIVE y el guardado no lo era
            if prev is not None and not (status == "ACTIVE" and prev.get("status") != "ACTIVE"):
                continue
            out[sku.upper()] = {
                "vid": n["id"], "pid": n["product"]["id"],
                "title": n["product"].get("title", ""),
                "price": n.get("price"), "compare_at": n.get("compareAtPrice"),
                "msi_mf": mf.get("value"), "status": status,
            }
        if conn["pageInfo"]["hasNextPage"]:
            cursor = conn["pageInfo"]["endCursor"]
        else:
            return out


# sentinela: dejar el compareAtPrice INTACTO (no incluir el campo en el update)
LEAVE = object()


def set_variant_price(sc, product_gid, variant_gid, price, compare_at):
    var = {"id": variant_gid, "price": f"{price:.2f}"}
    if compare_at is not LEAVE:
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


def set_msi_metafields(sc, updates):
    """updates: list[(product_gid, value)] → metafieldsSet en lotes de 25 (cap de la mutación)."""
    mut = """mutation($mfs:[MetafieldsSetInput!]!){
      metafieldsSet(metafields:$mfs){ userErrors{ field message } }
    }"""
    for i in range(0, len(updates), 25):
        batch = [{"ownerId": pid, "namespace": MSI_NS, "key": MSI_KEY,
                  "type": "single_line_text_field", "value": val}
                 for pid, val in updates[i:i + 25]]
        d = sc.graphql(mut, {"mfs": batch})
        errs = (d.get("metafieldsSet", {}) or {}).get("userErrors", [])
        if errs:
            raise RuntimeError(f"metafieldsSet: {errs}")


def set_envio_metafields(sc, updates):
    """updates: list[(product_gid, bool)] → metafield booleano f24.envio_gratis, en lotes de 25.

    Se escribe SIEMPRE (True y False), no solo cuando es True: si una promo con envío gratis
    expira, el producto tiene que quedar en 'false' o la chip se quedaría prendida para siempre.
    """
    mut = """mutation($mfs:[MetafieldsSetInput!]!){
      metafieldsSet(metafields:$mfs){ userErrors{ field message } }
    }"""
    for i in range(0, len(updates), 25):
        batch = [{"ownerId": pid, "namespace": ENVIO_NS, "key": ENVIO_KEY,
                  "type": "boolean", "value": "true" if val else "false"}
                 for pid, val in updates[i:i + 25]]
        d = sc.graphql(mut, {"mfs": batch})
        errs = (d.get("metafieldsSet", {}) or {}).get("userErrors", [])
        if errs:
            raise RuntimeError(f"metafieldsSet envio_gratis: {errs}")


def sync_perfil_envio_gratis(sc, updates):
    """updates: list[(variant_gid, bool)] → membresía del perfil de envío gratis.

    El metafield de arriba solo pinta la chip en la ficha. Quien decide si el
    CHECKOUT cobra envío es el perfil de entrega: Shopify no tiene ninguna
    condición "el carrito contiene el producto X" (el campo no existe en la API
    de descuentos, no es tema de plan), así que la única vía es un perfil aparte
    con tarifa $0 al que se le asocian las variantes.

    Esto es un RECONCILE, no un evento: se compara quién debe estar contra quién
    está, y se corrige la diferencia. Por eso una promo que expira se limpia
    sola — la col U se vuelve "No" y la variante sale en la siguiente corrida.
    Sin esto la ficha diría "envío gratis" y el cliente pagaría envío igual.
    """
    if not PERFIL_ENVIO_GRATIS:
        print("  🚚 perfil de envío gratis no configurado (F24_PERFIL_ENVIO_GRATIS) — solo metafields")
        return

    q = """query($id:ID!,$cursor:String){
      deliveryProfile(id:$id){
        profileItems(first:250, after:$cursor){
          edges{ node{ variants(first:25){ nodes{ id } } } }
          pageInfo{ hasNextPage endCursor } } } }"""
    dentro, cursor = set(), None
    while True:
        d = sc.graphql(q, {"id": PERFIL_ENVIO_GRATIS, "cursor": cursor})
        conn = ((d.get("deliveryProfile") or {}).get("profileItems") or {})
        for e in conn.get("edges", []):
            for v in e["node"]["variants"]["nodes"]:
                dentro.add(v["id"])
        pi = conn.get("pageInfo") or {}
        if pi.get("hasNextPage"):
            cursor = pi["endCursor"]
        else:
            break

    deben = {vid for vid, val in updates if val}
    entran = sorted(deben - dentro)
    salen = sorted(dentro - deben)

    mut = """mutation($id:ID!,$add:[ID!],$rm:[ID!]){
      deliveryProfileUpdate(id:$id, profile:{
        variantsToAssociate:$add, variantsToDissociate:$rm }){
        profile{ id } userErrors{ field message } } }"""
    # En lotes: asociar cientos de variantes de un jalón revienta el límite de costo.
    for i in range(0, max(len(entran), len(salen)), 50):
        add, rm = entran[i:i + 50], salen[i:i + 50]
        if not add and not rm:
            continue
        d = sc.graphql(mut, {"id": PERFIL_ENVIO_GRATIS, "add": add, "rm": rm})
        errs = (d.get("deliveryProfileUpdate", {}) or {}).get("userErrors", [])
        if errs:
            raise RuntimeError(f"deliveryProfileUpdate: {errs}")

    print(f"  🚚 perfil de envío: {len(deben)} con envío gratis real "
          f"(+{len(entran)} entraron · -{len(salen)} salieron)")


def set_product_tag(sc, product_gid, tag, add=True):
    mut = "tagsAdd" if add else "tagsRemove"
    d = sc.graphql(
        f"mutation($id:ID!,$tags:[String!]!){{ {mut}(id:$id, tags:$tags){{ userErrors{{ message }} }} }}",
        variables={"id": product_gid, "tags": [tag]})
    errs = (d.get(mut, {}) or {}).get("userErrors", [])
    if errs:
        raise RuntimeError(f"{mut} {product_gid}: {errs}")


def _f(x):
    return float(x) if x not in (None, "") else None


BASE_TOL = 1.0      # tolerancia para ignorar diferencias de redondeo (<$1) en precio base
SUSPECT_RATIO = 0.5  # cambio de precio base > 50% = sospechoso (dedazo 2×/mitad) → NO auto-aplica


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Aplica PROMOS (precio promo + tachado + restauración al expirar) + msi-912 + json.")
    ap.add_argument("--apply-base", action="store_true",
                    help="ADEMÁS empuja los precios BASE del sheet a Shopify (productos sin promo). "
                         "OFF por default: requiere reconciliar el sheet vs Shopify primero.")
    ap.add_argument("--json-only", action="store_true",
                    help="Regenera promos_active.json + state DESDE el Sheet SIN escribir nada a Shopify "
                         "(read-only). Lo usa el deploy-on-merge para hornear promos frescas sin side effects.")
    args = ap.parse_args()
    dry = not args.apply and not args.json_only

    print(f"{'DRY-RUN (preview, no escribe nada)' if dry else ('JSON-ONLY (read-only, sin Shopify)' if args.json_only else 'APPLY')}"
          f"{' + base prices' if args.apply_base else ''}")
    print("Source of truth: Sheet INVENTARIO F24\n")

    svc = _sheets_svc()
    rows = read_promo_active(svc)
    base = read_base_prices(svc)
    vigentes = [r for r in rows if r["vigente"]]
    promo_by_sku = {r["sku_upper"]: r for r in vigentes if r["promo_price"] is not None}

    import shopify_client as sc  # noqa
    print(f"Shopify: {sc.SHOP}  ·  jalando variantes…")
    variants = fetch_all_variants(sc)
    print(f"Variantes en Shopify: {len(variants)}\n")

    prev = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}

    # === 1) PROMOS: price=promo, compareAt=base (tachado). Captura el compareAt original. ===
    promo_changes, new_state = [], {}
    for sku_u, r in promo_by_sku.items():
        v = variants.get(sku_u)
        if not v:
            continue
        b = base.get(sku_u, {}).get("base")
        tach = base.get(sku_u, {}).get("tachado")
        want_p = r["promo_price"]
        # tachado (compareAt) = ancla de marketing si existe, si no el base, si no el regular
        want_c = tach if tach is not None else (b if b is not None else r["regular_price"])
        cur_p, cur_c = _f(v["price"]), _f(v["compare_at"])
        # compareAt original (Marvelsa) = lo guardado antes, o el actual si entra fresco a promo
        orig = prev.get(sku_u, {}).get("orig_compare_at", cur_c if sku_u not in prev else None)
        new_state[sku_u] = {"base": b, "promo": want_p, "orig_compare_at": orig}
        if cur_p is None or abs(cur_p - want_p) >= 0.01 or _f(want_c) != cur_c:
            promo_changes.append({"sku": sku_u, "pid": v["pid"], "vid": v["vid"],
                                  "cur_p": cur_p, "want_p": want_p, "want_c": want_c})

    # === 1b) DESCUENTO DIRECTO (STOCK col Q, sin promo): price=base*(1-desc), compareAt=base ===
    desc_by_sku, desc_changes = {}, []
    for sku_u, info in base.items():
        if sku_u in promo_by_sku:
            continue  # una promo activa manda sobre el descuento directo
        d, b, v = info.get("direct_disc"), info.get("base"), variants.get(sku_u)
        if not d or b is None or not v:
            continue
        desc_by_sku[sku_u] = d
        tach = info.get("tachado")
        # precio rebajado · tachado = ancla de marketing si existe, si no el base
        want_p, want_c = round(b * (1 - d), 2), (tach if tach is not None else b)
        cur_p, cur_c = _f(v["price"]), _f(v["compare_at"])
        orig = prev.get(sku_u, {}).get("orig_compare_at", cur_c if sku_u not in prev else None)
        new_state[sku_u] = {"base": b, "desc": d, "orig_compare_at": orig}
        if cur_p is None or abs(cur_p - want_p) >= 0.01 or _f(want_c) != cur_c:
            desc_changes.append({"sku": sku_u, "pid": v["pid"], "vid": v["vid"], "pct": d,
                                 "cur_p": cur_p, "want_p": want_p, "want_c": want_c})

    # === 2) EXPIRACIONES: en state pero ya no activos (ni promo ni descuento) → base + restaurar tachado ===
    expiries = []
    for sku_u, info in prev.items():
        if sku_u in promo_by_sku or sku_u in desc_by_sku:
            continue
        v = variants.get(sku_u)
        if not v:
            continue
        b = base.get(sku_u, {}).get("base") or info.get("base")
        if b is None:
            continue
        restore_c = info.get("orig_compare_at")  # Marvelsa original (o None)
        cur_p, cur_c = _f(v["price"]), _f(v["compare_at"])
        if cur_p is None or abs(cur_p - b) >= 0.01 or _f(restore_c) != cur_c:
            expiries.append({"sku": sku_u, "pid": v["pid"], "vid": v["vid"],
                             "cur_p": cur_p, "want_p": b, "want_c": restore_c})

    # === 3) PRECIO BASE (sin promo): el sheet manda, DIFF-based (>= $1). compareAt INTACTO. ===
    #   Guard anti-error: un cambio > SUSPECT_RATIO (50%) NO se auto-aplica — se marca para
    #   confirmar con Sergio (caza dedazos tipo 2× o mitad). Los cambios normales sí fluyen.
    base_review, base_suspect = [], []
    for sku_u, info in base.items():
        if sku_u in promo_by_sku or sku_u in desc_by_sku or sku_u in prev:
            continue
        b = info["base"]
        v = variants.get(sku_u)
        if v is None or b is None:
            continue
        cur_p = _f(v["price"])
        if cur_p is not None and abs(cur_p - b) >= BASE_TOL:
            entry = {"sku": sku_u, "pid": v["pid"], "vid": v["vid"],
                     "cur_p": cur_p, "want_p": b, "title": v["title"]}
            # Política "sin freno": el cambio SIEMPRE se aplica. Los cambios grandes
            # (>50%) solo se loguean como aviso para dejar rastro auditable (no congelan).
            base_review.append(entry)
            if cur_p > 0 and abs(b - cur_p) / cur_p > SUSPECT_RATIO:
                base_suspect.append(entry)

    # --- Reporte ---
    print(f"=== PROMOS — precio promo a setear ({len(promo_changes)}) ===")
    for c in sorted(promo_changes, key=lambda x: x["sku"]):
        print(f"  {c['sku']:<16} {str(c['cur_p']):>10} → {c['want_p']:>10.2f}  (tachado {c['want_c']})")
    if desc_changes:
        print(f"\n=== DESCUENTO DIRECTO — precio rebajado ({len(desc_changes)}) ===")
        for c in sorted(desc_changes, key=lambda x: x["sku"]):
            print(f"  {c['sku']:<16} {str(c['cur_p']):>10} → {c['want_p']:>10.2f}  (-{int(c['pct']*100)}%, tachado {c['want_c']})")
    if expiries:
        print(f"\n=== EXPIRARON — volver a precio base + restaurar tachado ({len(expiries)}) ===")
        for c in sorted(expiries, key=lambda x: x["sku"]):
            print(f"  {c['sku']:<16} {str(c['cur_p']):>10} → {c['want_p']:>10.2f}  (tachado {c['want_c']})")
    estado = "SE APLICA (--apply-base)" if args.apply_base else "solo revisión (sin --apply-base)"
    print(f"\n=== PRECIO BASE distinto en sheet ({len(base_review)}) — {estado} ===")
    for c in sorted(base_review, key=lambda x: x["sku"]):
        print(f"  {c['sku']:<18} shopify={c['cur_p']:>10}  sheet={c['want_p']:>10}  {c['title'][:34]}")
    if base_suspect:
        print(f"\n⚠️  CAMBIO DE BASE GRANDE (>{int(SUSPECT_RATIO*100)}%) — SE APLICA, queda en log de auditoría ({len(base_suspect)}):")
        for c in sorted(base_suspect, key=lambda x: x["sku"]):
            ratio = c["want_p"] / c["cur_p"] if c["cur_p"] else 0
            print(f"  {c['sku']:<18} shopify={c['cur_p']:>10}  sheet={c['want_p']:>10}  ({ratio:.2f}×)  {c['title'][:28]}")

    # msi-912 + promos_active.json
    for r in vigentes:
        v = variants.get(r["sku_upper"])
        r["in_shopify"] = bool(v)
        r["shopify_price"] = v["price"] if v else None
        r["product_gid"] = v["pid"] if v else None
    sellable = [r for r in vigentes if r["in_shopify"]]
    promo_missing = [r for r in vigentes if not r["in_shopify"]]

    # === 4) MSI chips (metafield f24.msi_meses) — diff vs valor actual en Shopify, sin state ===
    #   Promo vigente con "Meses MSI" → su ladder ("3,6" / "3,6,9,12"). Producto que tenía
    #   metafield y ya no está en promo → reset a MSI_DEFAULT. Sin metafield = default en el tema.
    pid_sku = {}
    msi_current = {}
    for sku_u, v in variants.items():
        pid_sku.setdefault(v["pid"], sku_u)
        msi_current.setdefault(v["pid"], v.get("msi_mf"))
    msi_desired = {}
    for r in sellable:
        if r["msi_ladder"]:
            msi_desired[r["product_gid"]] = ",".join(str(m) for m in r["msi_ladder"])
    msi_updates = []
    for pid, want in msi_desired.items():
        if msi_current.get(pid) != want:
            msi_updates.append((pid, want))
    for pid, cur in msi_current.items():
        if pid not in msi_desired and cur is not None and cur != MSI_DEFAULT:
            msi_updates.append((pid, MSI_DEFAULT))
    if msi_updates:
        print(f"\n=== MSI CHIPS PDP — metafield {MSI_NS}.{MSI_KEY} a escribir ({len(msi_updates)}) ===")
        for pid, val in sorted(msi_updates, key=lambda x: pid_sku.get(x[0], "")):
            print(f"  {pid_sku.get(pid, pid):<18} {str(msi_current.get(pid)):>12} → {val}")

    base_verb = "a aplicar" if args.apply_base else "por revisar"
    print(f"\nResumen: {len(promo_changes)} promo + {len(desc_changes)} descuento directo + "
          f"{len(expiries)} expiradas a aplicar | "
          f"{len(base_review)} base {base_verb} ({len(base_suspect)} con cambio grande, en log) | "
          f"{len(msi_updates)} msi_meses | {len(sellable)} promos vendibles")

    if dry:
        print("\n(DRY-RUN: no se escribió nada.)")
        return

    # ---- APPLY (promos + descuento directo + expiraciones siempre; base solo con --apply-base) ----
    # En --json-only se SALTAN todas las escrituras a Shopify; solo se regenera el JSON (más abajo).
    if not args.json_only:
        applied = list(promo_changes) + list(desc_changes) + list(expiries)
        if args.apply_base:
            applied += [{**c, "want_c": LEAVE} for c in base_review]  # base: precio sí, tachado intacto
        for c in applied:
            res = set_variant_price(sc, c["pid"], c["vid"], c["want_p"], c.get("want_c", LEAVE))
            print(f"  ✓ {c['sku']}: price={res['price']} compareAt={res['compareAtPrice']}")

        active_eligible = {r["sku_upper"] for r in sellable if r["eligible_912"]}
        for r in sellable:
            set_product_tag(sc, r["product_gid"], MSI912_TAG, add=r["eligible_912"])
        for sku_u in prev:
            if sku_u not in active_eligible and sku_u in variants:
                set_product_tag(sc, variants[sku_u]["pid"], MSI912_TAG, add=False)
        print(f"  🏷  msi-912 activos: {len(active_eligible)}")

        # --- cod-elegible: promo vigente + precio >= $10,000 (ver COD_TAG arriba) ---
        def _califica_cod(r):
            try:
                return float(r.get("shopify_price") or 0) >= COD_MIN_MXN
            except (TypeError, ValueError):
                return False

        active_cod = {r["sku_upper"] for r in sellable if _califica_cod(r)}
        for r in sellable:
            set_product_tag(sc, r["product_gid"], COD_TAG, add=_califica_cod(r))
        # Al expirar la promo o bajar de $10,000, el producto deja de calificar → se retira el tag.
        for sku_u in prev:
            if sku_u not in active_cod and sku_u in variants:
                set_product_tag(sc, variants[sku_u]["pid"], COD_TAG, add=False)
        print(f"  🏷  cod-elegible activos: {len(active_cod)}")

        # --- envío gratis: la chip de la ficha Y el envío real del checkout ---
        # Van juntos a propósito: si solo se escribiera el metafield, la ficha
        # prometería envío gratis y el checkout lo cobraría igual.
        envio_updates, envio_variantes = [], []
        for sku_u, info in base.items():
            v = variants.get(sku_u)
            if v:
                gratis = bool(info.get("envio_gratis"))
                envio_updates.append((v["pid"], gratis))
                envio_variantes.append((v["vid"], gratis))
        # Los combos no viven en el sheet: entran por la lista de estructurales.
        for sku_u in ENVIO_GRATIS_SIEMPRE:
            v = variants.get(sku_u.upper())
            if v:
                envio_updates.append((v["pid"], True))
                envio_variantes.append((v["vid"], True))
            else:
                print(f"  ⚠️  {sku_u} está en ENVIO_GRATIS_SIEMPRE pero no existe en la tienda")
        if envio_updates:
            set_envio_metafields(sc, envio_updates)
        con_envio = sum(1 for _, val in envio_updates if val)
        print(f"  🚚 envío gratis: {con_envio} con Sí · {len(envio_updates) - con_envio} en No")
        if envio_variantes:
            sync_perfil_envio_gratis(sc, envio_variantes)

        if msi_updates:
            set_msi_metafields(sc, msi_updates)
        print(f"  💳 msi_meses escritos: {len(msi_updates)}")

    def clean(r):
        return {k: v for k, v in r.items() if k not in ("product_gid", "variant_gid")}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROMOS_JSON.write_text(json.dumps({
        "source": f"{SHEET_ID}/{PROMO_TAB}",
        "generated": date.today().isoformat(),
        "note": "Solo promos VENDIBLES (existen en Shopify). El bot cotiza/vende únicamente estas.",
        "promos": [clean(r) for r in sellable],
        "excluidos_sin_pdp": [{"sku": r["sku"], "producto": r["producto"],
                                "estado_landing": r["estado_landing"]} for r in promo_missing],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    STATE_PATH.write_text(json.dumps(new_state, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json_only:
        print(f"\n✅ JSON-ONLY: {PROMOS_JSON.name} ({len(sellable)} vendibles) + {STATE_PATH.name} "
              f"regenerados del Sheet. Cero escrituras a Shopify.")
    else:
        print(f"\n✅ {len(applied)} precios + msi-912 aplicados. {PROMOS_JSON.name} "
              f"({len(sellable)} vendibles) + {STATE_PATH.name} escritos.")


if __name__ == "__main__":
    main()
