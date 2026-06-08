#!/usr/bin/env python3
"""Genera el Knowledge Base del bot F24 desde el catálogo Shopify LIVE.

A diferencia del bot de HC (4 productos hardcodeados desde un xlsx), F24 tiene
~189 SKUs de ferretería. Este script jala todos los productos ACTIVE de Shopify
(precio, compare_at, SKU, categoría, URL) y genera:

  F24_BOT_KNOWLEDGE/CATALOG_INDEX.md  — tabla compacta por categoría (lo lee el bot)
  F24_BOT_KNOWLEDGE/catalog.json      — machine-readable (lo usa el blueprint + Edge Fn)
  F24_BOT_KNOWLEDGE/PRICING_POLICY.md — MSI, envío gratis, promos (placeholder rotativo)

Regenerar cuando cambie el catálogo:
    /usr/bin/python3 build_f24_knowledge.py

El bot cotiza SOLO lo que existe aquí. Para armar draft orders, el bot pasa
SKUs+cantidades al Edge Function f24-process-order, que resuelve SKU→variant_id
en vivo (no se hardcodean variant IDs).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Reusar el cliente Shopify probado del pipeline PDP de F24
SCRIPT_DIR = Path(__file__).resolve().parent
F24_ROOT = SCRIPT_DIR.parent.parent  # .../F24- FERRE24
SHOPIFY_SCRIPTS = F24_ROOT / "F24 - 04. WEBSITE (1)" / "01. LIVE BUILD" / "scripts"
sys.path.insert(0, str(SHOPIFY_SCRIPTS))
import shopify_client as sc  # noqa: E402

OUT_DIR = SCRIPT_DIR / "F24_BOT_KNOWLEDGE"

# Promos: fuente de verdad = promos_active.json, generado por sync_f24_promos.py desde
# el Sheet INVENTARIO F24 / "🔥 PROMO ACTIVA". Solo incluye promos VENDIBLES (existen
# en Shopify). Correr `sync_f24_promos.py --apply` antes de este script.
PROMOS_JSON = OUT_DIR / "promos_active.json"


def read_msi_promos() -> dict:
    """Lee promos_active.json y devuelve {SKU_UPPER: {ladder, msi_max, eligible_912,
    promo_price, regular_price, pct, hasta, producto}}. Tolerante a fallos (si no
    existe, devuelve {} y el bot opera sin promos)."""
    try:
        if not PROMOS_JSON.exists():
            print("⚠️  promos_active.json no existe (corre sync_f24_promos.py); el bot sigue sin promos.")
            return {}
        data = json.loads(PROMOS_JSON.read_text(encoding="utf-8"))
        out = {}
        for r in data.get("promos", []):
            sku = (r.get("sku") or "").strip()
            if not sku:
                continue
            out[sku.upper()] = {
                "ladder": r.get("msi_ladder", []),
                "msi_max": r.get("msi_max", 0),
                "eligible_912": bool(r.get("eligible_912")),
                "promo_price": r.get("promo_price"),
                "regular_price": r.get("regular_price"),
                "pct": r.get("pct_desc", ""),
                "hasta": r.get("vigencia", ""),
                "producto": r.get("producto", ""),
            }
        return out
    except Exception as e:
        print(f"⚠️  No se pudo leer promos_active.json ({e}); el bot sigue sin promos.")
        return {}

# Categorías derivadas por keyword en el título (orden = prioridad de match).
# Cubre la familia de producto actual (motopartes / equipo de jardín y obra).
CATEGORY_RULES = [
    ("Generadores", ["generador", "planta de luz", "inverter"]),
    ("Generadores-Soldadores", ["soldador", "bakarac"]),
    ("Motobombas", ["motobomba", "bomba de agua", "bomba periférica", "bomba "]),
    ("Hidrolavadoras", ["hidrolavadora"]),
    ("Compresores", ["compresor"]),
    ("Motosierras y Poda", ["motosierra", "serrucho", "poda", "podadora"]),
    ("Desbrozadoras y Jardín", ["desbrozador", "desmalezadora", "motocultor", "fumigador", "aspersor"]),
    ("Compactación y Obra", ["bailarina", "compactadora", "apisonadora", "vibrador", "revolvedora"]),
    ("Mangueras y Accesorios", ["manguera", "layflat", "accesorio", "kit", "refacci"]),
]


def short_title(title: str) -> str:
    """Nombre legible para cotizar. Algunos títulos del catálogo son párrafos enteros
    de marketing; cortamos en el primer separador y limitamos longitud."""
    t = title.strip()
    # Cortar en el primer separador editorial (— : |) si el primer segmento es razonable
    for sep in ["—", " - ", ":", "|"]:
        if sep in t:
            head = t.split(sep)[0].strip()
            if 4 <= len(head) <= 70:
                return head
    # Si no hay separador útil, truncar a la primera frase / 70 chars
    t = re.split(r"(?<=[.!?])\s", t)[0]
    return (t[:67] + "...") if len(t) > 70 else t


def spec_excerpt(html: str, limit: int = 220) -> str:
    """Convierte descriptionHtml de Shopify a un extracto de texto plano para el bot.
    Quita tags, colapsa espacios, prioriza líneas con specs (números/unidades)."""
    if not html:
        return ""
    # <li>/<br>/<p> → separadores; quitar tags; decodificar entidades comunes
    txt = re.sub(r"<\s*(li|br|/p|/h\d|/tr)\s*[^>]*>", " · ", html, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    for a, b in [("&amp;", "&"), ("&nbsp;", " "), ("&aacute;", "á"), ("&eacute;", "é"),
                 ("&iacute;", "í"), ("&oacute;", "ó"), ("&uacute;", "ú"), ("&ntilde;", "ñ"),
                 ("&ordm;", "º"), ("&deg;", "°"), ("&quot;", '"'), ("&#39;", "'")]:
        txt = txt.replace(a, b)
    txt = re.sub(r"\s+", " ", txt).strip(" ·\t\n")
    if len(txt) > limit:
        txt = txt[:limit].rsplit(" ", 1)[0] + "…"
    return txt


def categorize(title: str, product_type: str, tags: list[str]) -> str:
    hay = f"{title} {product_type} {' '.join(tags)}".lower()
    for cat, kws in CATEGORY_RULES:
        if any(kw in hay for kw in kws):
            return cat
    if product_type.strip():
        return product_type.strip()
    return "Otros"


def fetch_all_active() -> list[dict]:
    """Pagina todos los productos ACTIVE con su primera variante."""
    out: list[dict] = []
    cursor = None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        data = sc.graphql(
            """
            query($after: String) {
              products(first: 100, query: "status:active", after: $after) {
                pageInfo { hasNextPage endCursor }
                edges { node {
                  title handle productType tags descriptionHtml
                  featuredImage { url }
                  metafields(first: 8, namespace: "f24") { edges { node { key value } } }
                  variants(first: 1) { edges { node { id sku price compareAtPrice availableForSale } } }
                } }
              }
            }
            """,
            variables={"after": cursor},
        )["products"]
        for e in data["edges"]:
            n = e["node"]
            v = (n["variants"]["edges"] or [{}])
            vn = v[0].get("node", {}) if v else {}
            gid = vn.get("id") or ""
            mf = {m["node"]["key"]: m["node"]["value"] for m in n.get("metafields", {}).get("edges", [])}
            out.append({
                "title": n["title"].strip(),
                "short_title": short_title(n["title"]),
                "handle": n["handle"],
                "category": categorize(n["title"], n.get("productType", ""), n.get("tags", [])),
                "sku": (vn.get("sku") or "").strip(),
                # variant_id es el fallback estable cuando el SKU viene vacío;
                # el Edge Function f24-process-order resuelve el pedido por SKU o por este ID.
                "variant_id": gid.rsplit("/", 1)[-1] if gid else "",
                "variant_gid": gid,
                "price": vn.get("price"),
                "compare_at_price": vn.get("compareAtPrice"),
                "available": vn.get("availableForSale", True),
                # Fuente de verdad de specs (Shopify): marca/modelo/categoría + extracto de descripción.
                "marca": mf.get("marca", "").strip(),
                "modelo": mf.get("modelo", "").strip(),
                "specs": spec_excerpt(n.get("descriptionHtml", "")),
                "image_url": ((n.get("featuredImage") or {}).get("url") or "").split("?")[0],
            })
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]
    return out


def fmt_price(p) -> str:
    if p is None:
        return "?"
    try:
        return f"${float(p):,.0f}"
    except (ValueError, TypeError):
        return f"${p}"


def write_catalog_index(products: list[dict], domain: str, promos: dict | None = None) -> None:
    promos = promos or {}
    by_cat: dict[str, list[dict]] = {}
    for p in products:
        by_cat.setdefault(p["category"], []).append(p)

    md = [
        "# Ferre24 — Catálogo (Knowledge Base del bot)",
        "",
        f"*{len(products)} productos ACTIVE. Regenerar con `build_f24_knowledge.py`.*",
        "",
        "> El bot cotiza ÚNICAMENTE productos de esta lista. El **precio** es el de venta;",
        "> el precio **tachado** (si existe) es referencia. Para cerrar, el bot pasa el/los",
        "> **SKU + cantidad** al sistema de órdenes — NO inventa precios ni productos.",
        "",
    ]
    # Sección de promos vigentes (source of truth: Sheet INVENTARIO F24 / PROMO ACTIVA).
    md.append("## ⚡ PROMOS ACTIVAS (source of truth: Sheet INVENTARIO F24 / 🔥 PROMO ACTIVA)")
    if promos:
        cb = {s: i for s, i in promos.items() if i.get("eligible_912")}
        md.append(f"{len(promos)} producto(s) en promoción vigente. El **precio promo YA está en el catálogo** "
                  "(precio de venta = precio promo; el regular aparece tachado). Cotiza ese precio tal cual.")
        md.append("")
        md.append("Reglas de meses sin intereses (MSI) por promo:")
        md.append(f"- SKUs con **9 o 12 MSI** ({len(cb)} de la lista): si el cliente paga a 9/12 meses → cierra con "
                  "`order.payment_method='msi_promo'` (genera link MercadoPago Cuenta B). Hasta 6 MSI también por link normal.")
        md.append("- SKUs solo con 3/6 MSI: `order.payment_method='online'` (link normal Shopify, hasta 6 MSI).")
        md.append("- NUNCA prometas 9/12 a un SKU que no diga 'Sí' en la columna Cuenta B.")
        md.append("")
        md.append("| SKU | Promo | Regular | Desc | MSI | Cuenta B (9/12) | Vence |")
        md.append("|---|---|---|---|---|---|---|")
        for sku, info in sorted(promos.items()):
            ladder = ", ".join(str(m) for m in info.get("ladder", [])) or "—"
            cbf = "**Sí**" if info.get("eligible_912") else "no"
            promo_cell = fmt_price(info["promo_price"]) if info.get("promo_price") is not None else "solo MSI"
            md.append(f"| `{sku}` | {promo_cell} | {fmt_price(info.get('regular_price'))} "
                      f"| {info.get('pct','')} | {ladder} | {cbf} | {info.get('hasta','')} |")
    else:
        md.append("Ahorita NO hay promos vigentes. Todos los SKUs: solo hasta 6 MSI (link normal).")
    md.append("")
    # Orden: categorías definidas primero, luego el resto alfabético
    ordered = [c for c, _ in CATEGORY_RULES if c in by_cat]
    ordered += sorted(c for c in by_cat if c not in ordered)
    for cat in ordered:
        items = sorted(by_cat[cat], key=lambda x: x["title"])
        md.append(f"## {cat} ({len(items)})")
        md.append("")
        for p in items:
            antes = f" (antes {fmt_price(p['compare_at_price'])})" if p["compare_at_price"] else ""
            url = f"https://{domain}/products/{p['handle']}"
            ident = p["sku"] or f"id:{p['variant_id']}"
            name = (p.get("short_title") or p["title"]).replace("|", "/")
            marca_modelo = " · ".join(x for x in [p.get("marca"), p.get("modelo")] if x)
            head = f"- **{name}** · `{ident}` · {fmt_price(p['price'])}{antes}"
            if marca_modelo:
                head += f" · {marca_modelo}"
            pr = promos.get((p["sku"] or "").upper())
            if pr:
                tag = "⚡PROMO"
                if pr.get("eligible_912"):
                    tag += f" {pr.get('msi_max')}MSI"
                head += f" · {tag}"
            if not p.get("available", True):
                head += " · 🔴 AGOTADO"
            md.append(head)
            if p.get("specs"):
                md.append(f"  {p['specs']}")
            md.append(f"  PDP: {url}")
            if p.get("image_url"):
                md.append(f"  IMG: {p['image_url']}")
        md.append("")
    (OUT_DIR / "CATALOG_INDEX.md").write_text("\n".join(md), encoding="utf-8")
    print(f"✅ CATALOG_INDEX.md ({len(products)} productos, {len(by_cat)} categorías)")


def write_catalog_json(products: list[dict], domain: str) -> None:
    payload = {"domain": domain, "count": len(products), "products": products}
    (OUT_DIR / "catalog.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ catalog.json ({len(products)} productos)")


def write_pricing_policy() -> None:
    path = OUT_DIR / "PRICING_POLICY.md"
    if path.exists():
        print("•  PRICING_POLICY.md ya existe — no se sobrescribe (es editable a mano)")
        return
    md = [
        "# Ferre24 — Política de precios y promociones",
        "",
        "> Editable a mano. El bot lee esto para responder dudas de pago/envío/promos.",
        "> La promo PROFUNDA rotativa (9-12 MSI) se actualiza aquí cada ~15 días (o se",
        "> sincroniza vía Make). Si no hay lista vigente, el bot dice 'pregunta por las",
        "> promos del mes' — nunca queda roto.",
        "",
        "## Oferta base permanente (33 SKUs definidos)",
        "- **3 y 6 meses sin intereses** disponibles.",
        "- **Envío gratis** según umbral / promoción vigente.",
        "",
        "## Promo profunda rotativa (cambia ~cada 15 días)",
        "- _Pendiente: lista vigente de SKUs con 9-12 MSI / envío gratis (la define Sergio/proveedor)._",
        "- Mientras no haya lista: el bot ofrece 'pregunta por las promos de la semana'.",
        "",
        "## Envío",
        "- Cobertura: Tinguindín origen + Zamora/Reyes/Periván + GDL + nacional.",
        "- **Entrega regional 24-48h** (cuña de marca: GDL y Michoacán).",
        "",
        "## Pago",
        "- Tarjeta (MSI según SKU), transferencia/depósito, OXXO.",
        "- Para cerrar: el bot arma el pedido y manda **link de pago seguro**.",
        "",
    ]
    path.write_text("\n".join(md), encoding="utf-8")
    print("✅ PRICING_POLICY.md (plantilla inicial)")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    domain = sc.PRIMARY_DOMAIN or sc.SHOP
    print(f"Jalando catálogo ACTIVE de {sc.SHOP} (dominio público: {domain}) ...")
    products = fetch_all_active()
    promos = read_msi_promos()
    print(f"Promos 9/12 MSI vigentes: {len(promos)} SKU(s) {list(promos.keys()) if promos else ''}")
    for p in products:
        pr = promos.get((p["sku"] or "").upper(), {})
        p["msi_promo"] = str(pr.get("msi_max", "")) if pr.get("eligible_912") else ""
    write_catalog_index(products, domain, promos)
    write_catalog_json(products, domain)
    write_pricing_policy()
    print(f"\nOutput: {OUT_DIR}")


if __name__ == "__main__":
    main()
