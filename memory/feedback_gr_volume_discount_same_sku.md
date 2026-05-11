# feedback: GR widget volumen "2pz 5% / 4pz 10%" es SAME-SKU only

**Confirmado 2026-04-21** via inspección del HTML de `/products/gaxaliv-porobioticos`.

El widget "¡Llévate más! Ahorra más!" con opciones "Compra 1", "Compra 2" (5% OFF), "Compra 4" (10% OFF) aplica **únicamente a múltiplos del MISMO SKU** (misma variant × N).

**NO aplica a combos de productos distintos.** Ejemplo:
- 4× Gaxaliv Probióticos ($372 × 4 = $1,488 → $1,339.20 con 10% OFF) ✅
- 1× Gaxaliv + 1× Enzymas + 1× Probióticos + 1× HR (4 productos distintos) ❌ NO aplica descuento

## Implicación para ads

Ads que usen el ángulo "llévate el sistema completo" / "trío" / "pack de X productos distintos" **NO pueden apoyarse en este widget para claim de descuento**. El cliente llegaría al carrito esperando 10% OFF y no lo recibiría → refund/queja/CPA destruido.

**Para ads con múltiples productos distintos**, hay que crear **product bundle real** en Shopify con precio fijo (ej. HORMO FX Pack 40+ creado 2026-04-21 a $799).

**Para ads con producto único**, el badge "LLÉVATE 2 · 5% OFF · LLÉVATE 4 · 10% OFF" sí funciona y es copy válido.

## Implementación del widget

Probablemente una app Shopify o custom section. No tiene branding visible en HTML (no es Bold, Appstle, Rebuy conocido). El descuento se aplica automáticamente en checkout cuando detecta qty ≥ 2 o 4 del mismo variant.

## No validado en otros clientes

- LF: no tiene este widget (bundles son product-level con variants)
- HC: no tiene este widget (usa cupón CHUCHO10)
- MG: N/A (B2B GHL)
