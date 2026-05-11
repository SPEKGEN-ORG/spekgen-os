# feedback: NUNCA escribir precios en ads sin validar contra Shopify Admin API

**Regla dura desde 2026-04-21:** antes de cerrar batch.json con ads que mencionan precio, bundle, descuento o compare_at, SIEMPRE hacer pre-flight pull del catálogo Shopify del cliente y cruzar cada precio con lo real.

## Qué pasó (incidente 2026-04-21)

Batch v4.1 con 15 ads (9 GR + 3 LF + 3 HC). Los 4 ads con "promo/bundle" tenían precios completamente inventados:

| Ad | Precio en ad | Precio real Shopify | Delta |
|---|---|---|---|
| GR Gastro "Sistema $1,280/$1,720" | $1,280 | Bundle `Protocolo Gaxaliv` existe a $1,052, no $1,280. Además SKU base OUT-OF-STOCK | fantasía |
| GR Pack 40+ "$990/$1,300" | $990 | Bundle NO existía. Suma individual $875 | fantasía |
| GR Trío Proteicos "$999/$1,380" | $999 | Bundle NO existía. Suma real $2,928. Precio del ad = 66% OFF imposible | fantasía |
| LF Kit "$699/$920" | $699 | Trío Esencial real = $1,077/$1,267 (15% OFF) | fantasía |

Gibran detectó los 4 errores al cruzar manualmente. Si hubiera subido a Meta y disparado tráfico, habría generado quejas de clientes + CPA destruido.

## Root cause

- Al escribir JSON del batch, generé precios "atractivos" por lógica interna sin abrir Shopify.
- El ruido cross-client (mezcla GR + LF + HC en un mismo batch) agravó la situación: 3 catálogos, 3 mecánicas de descuento distintas, 3 temas Shopify distintos.
- Factory workflow v4.1 NO tenía pre-flight check obligatorio.

## Regla de oro

Si un ad menciona `price`, `compare_at_price`, `discount_pct`, `bundle`, `offer_tag` o similar:

1. **PULL catálogo Shopify del cliente** vía Admin API (script snippet abajo)
2. **Verificar cada SKU/handle referenciado existe** y está `active`
3. **Verificar precio del ad == precio Shopify** (o compare_at)
4. **Si es bundle**: verificar que el product bundle existe. Si no existe → crear product real antes de escribir el JSON (o matar el ángulo).
5. **Si es descuento**: verificar que el descuento es real (ya sea via `compare_at`, widget volumen, o discount code). Si inventas un % → flag al usuario antes de cerrar.

## Snippet pre-flight (Python stdlib)

```python
import os, json, urllib.request
STORE = "{cliente}.myshopify.com"
TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]  # del .env del cliente
req = urllib.request.Request(
    f"https://{STORE}/admin/api/2024-10/products.json?limit=250",
    headers={"X-Shopify-Access-Token": TOKEN}
)
products = json.loads(urllib.request.urlopen(req).read())["products"]
# Ahora cruzar vs lo que dice el ad
```

## Mecánicas de descuento por cliente (validadas 2026-04-21)

- **GR:** widget volumen `2pz 5% / 4pz 10%` es **SAME-SKU** (misma referencia × N), NO cross-SKU. Casi todos los productos tienen `compare_at_price` ~15% mayor que `price` (descuento "permanente"). Ver `feedback_gr_volume_discount_same_sku.md`.
- **LF:** bundles fijos via product con variants (ej. Kit Esencial: Dúo $700/$778, Trío $1,077/$1,267). No widget volumen.
- **HC:** cupón `CHUCHO10` manual. Bundles product-level.

## Refactor obligatorio pendiente

`/factory-batch` debe:
- Ejecutar pre-flight catalog pull automático al hacer `init_batch.py --client X --type ads`
- Cachear catálogo en `batch.json._meta.shopify_catalog_snapshot`
- `validate_batch.py` rechaza si algún precio/handle en ads no cruza contra el snapshot

Tracked como pendiente en `GR/_CLIENT_CONTEXT.md` y Obsidian daily note 2026-04-21.
