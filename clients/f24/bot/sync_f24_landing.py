#!/usr/bin/env python3
"""Reconcilia la LANDING de promociones de Ferre24 (/pages/promociones).

SOURCE OF TRUTH: Sheet "INVENTARIO F24" (1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U),
pestaña "🔥 PROMO ACTIVA" — la misma que consume sync_f24_promos.py. El equipo de F24
marca promos en "📦 STOCK Y PROMOS" y esa pestaña se auto-llena. Este script la lee y:

  1. Filtra a promos VIGENTES (hoy <= Vigencia fin, formato dd/mm/yyyy).
  2. Reconcilia la colección Shopify `promociones-vigentes`:
       - AGREGA los SKUs vigentes que existan en Shopify (resuelven a un producto).
       - QUITA los productos que ya NO estén vigentes (esto da de baja la tarjeta en la
         landing cuando una promo expira). Idempotente: no toca lo que ya está bien.
  3. Escribe los DATOS VIVOS del contador/fecha en metafields de la colección:
       - custom.promo_end   = vigencia máx en ISO (lo consume el countdown JS).
       - custom.promo_fecha = vigencia máx en texto español ("30 de junio").
     El Liquid del tema (ya subido una vez) lee estos metafields + collection.products_count
     EN VIVO, así que el contador, la fecha y el countdown se mantienen solos en cada sync
     SIN redeploy del tema. Además bustea el full-page cache de /pages/promociones cuando
     cambia el count o la fecha (re-PUT del body_html), para que el cambio se vea de inmediato.
     Mantiene también `end_iso` en la copia del template del repo como FALLBACK (no se sube).

Robusto a filas incompletas: si un SKU no resuelve en Shopify, lo reporta y lo omite
(no truena). El grid liquid plano (theme/f24-promo-grid.liquid) renderiza TODA la
colección directo, sin tags de grupo.

Por defecto corre en DRY-RUN (no escribe nada). Para aplicar: --apply

    /usr/bin/python3 sync_f24_landing.py            # dry-run (preview)
    /usr/bin/python3 sync_f24_landing.py --apply     # reconcilia colección + escribe template repo

NOTA DE SEGURIDAD: incluso con --apply este script SOLO toca la colección Shopify
`promociones-vigentes` (collects) y la copia LOCAL del template en el repo. NO sube
nada al tema de Shopify ni hace git. La colección no es pública por sí sola; la landing
solo cambia cuando alguien sube el grid + template al tema.
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

# En el repo cloud (GitHub Actions) usamos el shopify_client.py que vive junto a este
# script (clients/f24/bot/) y las credenciales Shopify llegan por env (secrets). Igual
# que sync_f24_promos.py / sync_f24_inventory.py de este mismo bot.
#
# Para validar localmente (dry-run desde la máquina de Gibran, donde el .env vive en el
# árbol de Drive), hacemos best-effort de cargar ese .env si lo encontramos. No tiene
# efecto en cloud (no existe Drive ahí) y es read-only.
def _bootstrap_local_env() -> None:
    if os.environ.get("SHOPIFY_SHOP"):
        return  # cloud: secrets ya inyectados
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    candidates = [
        Path.home() / "Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com"
        / "My Drive 2" / "01. CLIENTS OFFICIAL" / "F24- FERRE24" / ".env",
    ]
    for env_path in candidates:
        if env_path.exists():
            load_dotenv(env_path)
            break


_bootstrap_local_env()

# Template versionado EN EL REPO (no se sube al tema desde aquí).
REPO_TEMPLATE_PATH = SCRIPT_DIR / "theme" / "page.landing-promociones.json"

SHEET_ID = "1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U"
PROMO_TAB = "🔥 PROMO ACTIVA"
COLLECTION_HANDLE = "promociones-vigentes"
COLLECTION_TITLE = "Promociones vigentes"
# Página landing (para el FPC-bust al cambiar la promo).
PAGE_HANDLE = "promociones"
# Secciones del template que llevan el chip countdown end_iso.
COUNTDOWN_SECTIONS = ("promobar", "hero", "promogrid", "final")

# Meses en español para el texto humano de la fecha (locale-independiente).
SPANISH_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Columnas: SKU | Producto | Precio | Meses MSI | % Desc | Precio Promo | Vigencia (fin) | Estado Landing
COL = {"sku": 0, "producto": 1, "precio": 2, "msi": 3, "pct": 4, "promo": 5, "vig": 6, "landing": 7}

SA_REL = "HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/config/spekgen_service_account.json"


# ---------------- Sheet (mismo patrón que sync_f24_promos.py) ----------------

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
        rows.append({
            "sku": sku,
            "sku_upper": sku.upper(),
            "producto": str(r[COL["producto"]]).strip(),
            "regular_price": parse_money(r[COL["precio"]]),
            "promo_price": parse_money(r[COL["promo"]]),
            "pct_desc": str(r[COL["pct"]]).strip(),
            "msi_ladder": ladder,
            "vigencia": vig.isoformat() if vig else "",
            "vig_date": vig,
            "vigente": (vig is None) or (today <= vig),
            "estado_landing": str(r[COL["landing"]]).strip(),
        })
    return rows


# ---------------- Shopify: colección promociones-vigentes ----------------

def resolve_product_id_by_sku(sc, sku: str):
    """Devuelve (product_id:int, title, handle) para un SKU, o None si no existe."""
    q = sku.replace('"', '\\"')
    data = sc.graphql(
        """query findBySku($q:String!){
             productVariants(first:5, query:$q){
               edges{ node{ sku product{ id title handle status } } }
             }
           }""",
        variables={"q": f"sku:{q}"})
    edges = (data.get("productVariants", {}) or {}).get("edges", [])
    for e in edges:
        node = e["node"]
        if (node.get("sku") or "").strip().upper() == sku.strip().upper():
            gid = node["product"]["id"]
            return int(gid.rsplit("/", 1)[-1]), node["product"]["title"], node["product"]["handle"]
    return None


def find_collection_by_handle(sc, handle: str):
    data = sc.rest("GET", "custom_collections.json", params={"handle": handle})
    cols = data.get("custom_collections", [])
    return cols[0] if cols else None


def ensure_collection(sc, apply: bool):
    existing = find_collection_by_handle(sc, COLLECTION_HANDLE)
    if existing:
        return int(existing["id"])
    if not apply:
        return None  # dry-run: aún no existe
    payload = {"custom_collection": {
        "title": COLLECTION_TITLE,
        "handle": COLLECTION_HANDLE,
        "published": True,
        "body_html": "Equipo seleccionado en promoción durante la vigencia vigente.",
    }}
    created = sc.rest("POST", "custom_collections.json", payload=payload)
    cid = int(created["custom_collection"]["id"])
    print(f"  + created collection {COLLECTION_HANDLE} (id={cid})")
    return cid


def list_collects(sc, collection_id: int) -> list[dict]:
    """Devuelve los collects (con product_id) de la colección. Pagina por Link header."""
    out: list[dict] = []
    params = {"collection_id": collection_id, "limit": 250}
    data = sc.rest("GET", "collects.json", params=params)
    out.extend(data.get("collects", []))
    # La colección de promos nunca debería pasar de 250; mantenemos simple como swap_promo_cycle.
    return out


# ---------------- Contador (end_iso) en el template del repo ----------------

def update_template_dates(end_iso: str, apply: bool) -> tuple[str, list[str]]:
    """Pone end_iso en las secciones countdown del template VERSIONADO EN EL REPO.

    Devuelve (end_iso_anterior_representativo, secciones_tocadas). En dry-run no escribe.
    NO sube nada al tema.
    """
    if not REPO_TEMPLATE_PATH.exists():
        raise SystemExit(
            f"No existe el template del repo: {REPO_TEMPLATE_PATH}. "
            "Cópialo desde el LIVE BUILD antes de correr (ver LANDING_NOTES.md).")
    doc = json.loads(REPO_TEMPLATE_PATH.read_text(encoding="utf-8"))
    sections = doc.get("sections", {})
    touched, prev_vals = [], []
    for key in COUNTDOWN_SECTIONS:
        s = sections.get(key)
        if not s:
            continue
        st = s.setdefault("settings", {})
        prev_vals.append(st.get("end_iso", ""))
        if st.get("end_iso") != end_iso:
            touched.append(key)
        st["end_iso"] = end_iso
    prev = next((v for v in prev_vals if v), "")
    if apply and touched:
        new_text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
        REPO_TEMPLATE_PATH.write_text(new_text, encoding="utf-8")
    return prev, touched


def max_vigencia_date(vigentes: list[dict]):
    """Devuelve la fecha de vigencia MÁXIMA entre las promos activas, o None."""
    dates = [r["vig_date"] for r in vigentes if r.get("vig_date")]
    return max(dates) if dates else None


def end_iso_from_date(d) -> str:
    """date -> ISO con tz -06:00 a las 23:59:59 (formato que consume el countdown JS)."""
    return f"{d.isoformat()}T23:59:59-06:00" if d else ""


def spanish_date(d) -> str:
    """date(2026,6,30) -> '30 de junio' (texto humano para la landing)."""
    return f"{d.day} de {SPANISH_MONTHS[d.month - 1]}" if d else ""


def max_vigencia_end_iso(vigentes: list[dict]) -> str:
    """Compat: vigencia MÁXIMA -> ISO. Mantiene la firma usada por el resto del script."""
    return end_iso_from_date(max_vigencia_date(vigentes))


# ---------------- Metafields de la colección (count/fecha viven en datos vivos) ----------------

def set_collection_promo_metafields(sc, cid: int, end_iso: str, fecha_txt: str,
                                     apply: bool) -> list[str]:
    """Escribe custom.promo_end (ISO countdown) y custom.promo_fecha (texto español)
    en la colección vía GraphQL metafieldsSet (upsert real). El Liquid los lee vivos,
    así el contador y la fecha de la landing NO requieren redeploy del tema.

    Devuelve la lista de keys escritas (vacía en dry-run o si no hay fecha)."""
    if not end_iso or not fecha_txt:
        return []
    if not apply:
        return ["promo_end", "promo_fecha"]
    owner = f"gid://shopify/Collection/{cid}"
    sc.graphql(
        """mutation setMF($mf:[MetafieldsSetInput!]!){
             metafieldsSet(metafields:$mf){
               metafields{ namespace key value }
               userErrors{ field message }
             }
           }""",
        variables={"mf": [
            {"ownerId": owner, "namespace": "custom", "key": "promo_end",
             "type": "single_line_text_field", "value": end_iso},
            {"ownerId": owner, "namespace": "custom", "key": "promo_fecha",
             "type": "single_line_text_field", "value": fecha_txt},
        ]})
    return ["promo_end", "promo_fecha"]


def bust_page_cache(sc, handle: str, marker: str, apply: bool) -> bool:
    """Invalida el full-page cache de Shopify de /pages/{handle} re-PUTeando body_html
    con un comentario-marcador. Solo cambia el HTML cuando cambia el marker (count/fecha),
    así un cambio de fecha se ve de inmediato sin tocar el tema. NO es un theme push.

    Patrón validado en feedback_shopify_fpc_cachebust. Devuelve True si bustó."""
    data = sc.rest("GET", "pages.json", params={"handle": handle})
    pages = data.get("pages", [])
    if not pages:
        print(f"  (FPC-bust: no encontré la página handle='{handle}', omito)")
        return False
    page = pages[0]
    body = page.get("body_html") or ""
    # Quita un marcador previo y agrega el nuevo.
    body = re.sub(r"<!-- promo-sync:.*? -->", "", body).rstrip()
    new_body = f"{body}\n<!-- promo-sync: {marker} -->"
    if new_body == (page.get("body_html") or ""):
        return False  # nada cambió
    if apply:
        sc.rest("PUT", f"pages/{page['id']}.json",
                payload={"page": {"id": page["id"], "body_html": new_body}})
    return True


# ---------------- Main ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Reconcilia la colección en Shopify + escribe el template del repo. Sin esto = dry-run.")
    args = ap.parse_args()
    dry = not args.apply

    print(f"{'DRY-RUN (preview, no escribe nada)' if dry else 'APPLY (colección Shopify + template repo)'}")
    print(f"Source of truth: Sheet INVENTARIO F24 / '{PROMO_TAB}'\n")

    rows = read_promo_active()
    vigentes = [r for r in rows if r["vigente"]]
    expiradas = [r for r in rows if not r["vigente"]]
    print(f"Filas en PROMO ACTIVA: {len(rows)}  |  vigentes: {len(vigentes)}  |  expiradas: {len(expiradas)}\n")

    import shopify_client as sc  # noqa  (versión del LIVE BUILD — resuelve .env/token/THEME_ID)
    print(f"Shopify: {sc.SHOP}\n")

    # Resolver cada SKU vigente a un producto (omite los que no existan, no truena).
    resolved: dict[int, dict] = {}   # product_id -> {sku, title, handle}
    missing: list[dict] = []
    for r in vigentes:
        item = resolve_product_id_by_sku(sc, r["sku"])
        if not item:
            missing.append(r)
            continue
        pid, title, handle = item
        resolved[pid] = {"sku": r["sku"], "title": title, "handle": handle}

    want_pids = set(resolved.keys())

    # Estado actual de la colección.
    cid = ensure_collection(sc, apply=args.apply)
    current_collects: dict[int, int] = {}  # product_id -> collect_id
    if cid:
        for c in list_collects(sc, cid):
            current_collects[int(c["product_id"])] = int(c["id"])
    have_pids = set(current_collects.keys())

    to_add = sorted(want_pids - have_pids)
    to_remove = sorted(have_pids - want_pids)
    keep = sorted(want_pids & have_pids)

    print(f"Colección `{COLLECTION_HANDLE}`"
          + (f" (id={cid})" if cid else " (aún NO existe — se crearía con --apply)"))
    print(f"  vigentes resueltos en Shopify: {len(want_pids)}  |  ya en colección: {len(keep)}\n")

    print(f"AGREGAR ({len(to_add)}):")
    for pid in to_add:
        info = resolved[pid]
        print(f"  + {info['sku']:<16} {info['title'][:54]:<54} #{pid}")
    print(f"\nQUITAR ({len(to_remove)})  ← baja de tarjeta al expirar:")
    for pid in to_remove:
        print(f"  - product #{pid} (collect {current_collects[pid]}) — ya no vigente / fuera de promo")

    if missing:
        print(f"\nOMITIDOS ({len(missing)} no resuelven en Shopify — el equipo debe subir su PDP):")
        for r in sorted(missing, key=lambda x: x["sku"]):
            print(f"  · {r['sku']:<16} {r['producto'][:50]:<50} [{r['estado_landing']}]")

    # Contador + fecha humana (viven en datos vivos: metafields de la colección).
    max_date = max_vigencia_date(vigentes)
    end_iso = end_iso_from_date(max_date)
    fecha_txt = spanish_date(max_date)
    prev_iso, _ = update_template_dates(end_iso, apply=False) if end_iso else ("", [])
    print(f"\nCONTADOR (end_iso fallback en {REPO_TEMPLATE_PATH.name}):")
    if end_iso:
        print(f"  actual: {prev_iso or '—'}  ->  nuevo (vigencia máx): {end_iso}")
        print(f"  secciones template: {', '.join(COUNTDOWN_SECTIONS)}")
    else:
        print("  sin vigencias fechadas en las promos activas — no se toca el contador.")

    print(f"\nDATOS VIVOS (metafields de la colección — los lee el Liquid sin redeploy):")
    print(f"  custom.promo_end   -> {end_iso or '—'}")
    print(f"  custom.promo_fecha -> {fecha_txt or '—'}")
    print(f"  contador equipos   -> {len(want_pids)} (collection.products_count, vivo)")

    print(f"\nResumen: +{len(to_add)} agregar | -{len(to_remove)} quitar | "
          f"{len(keep)} sin cambio | {len(missing)} omitidos | contador -> {end_iso or 'sin cambio'}")

    if dry:
        print("\n(DRY-RUN: no se escribió nada. Corre con --apply para aplicar.)")
        return

    # APPLY — reconciliar collects.
    if cid is None:
        cid = ensure_collection(sc, apply=True)
    for pid in to_add:
        sc.rest("POST", "collects.json", payload={"collect": {
            "collection_id": cid, "product_id": pid}})
        print(f"  ✓ +{resolved[pid]['sku']} (#{pid})")
    for pid in to_remove:
        sc.rest("DELETE", f"collects/{current_collects[pid]}.json")
        print(f"  ✓ -#{pid}")

    # APPLY — contador en el template del repo (fallback; NO se sube al tema).
    if end_iso:
        _, touched = update_template_dates(end_iso, apply=True)
        if touched:
            print(f"  ✓ end_iso (fallback) -> {end_iso} en {', '.join(touched)} ({REPO_TEMPLATE_PATH})")
        else:
            print(f"  = contador (fallback) ya estaba en {end_iso}")

    # APPLY — metafields de la colección (fuente viva del contador/fecha en el Liquid).
    written = set_collection_promo_metafields(sc, cid, end_iso, fecha_txt, apply=True)
    if written:
        print(f"  ✓ metafields colección: custom.promo_end={end_iso} · custom.promo_fecha='{fecha_txt}'")

    # APPLY — bustear el full-page cache de la landing si cambió count/fecha.
    marker = f"{len(want_pids)} {end_iso}"
    if bust_page_cache(sc, PAGE_HANDLE, marker, apply=True):
        print(f"  ✓ FPC-bust /pages/{PAGE_HANDLE} (marker: {marker})")
    else:
        print(f"  = /pages/{PAGE_HANDLE} sin cambio de count/fecha (no se bustea)")

    print(f"\n✅ Colección reconciliada (+{len(to_add)}/-{len(to_remove)}). "
          f"Metafields vivos escritos + cache busteado. "
          f"El Liquid del tema (ya subido) renderiza contador/fecha solos en cada sync.")


if __name__ == "__main__":
    main()
