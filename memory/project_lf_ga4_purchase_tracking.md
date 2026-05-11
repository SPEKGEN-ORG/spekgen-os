---
name: LF GA4 purchase tracking fix (Custom Pixel)
description: Fix 2026-04-14 del bug GA4 compras=0 en LF via Shopify Custom Pixel + Measurement Protocol
type: project
originSessionId: 3ceb1165-acd2-4d03-a25b-a17a39c21373
---
**Bug:** Hasta 2026-04-14, GA4 LF reportaba 0 compras / $0 revenue aunque Shopify tenía órdenes reales (discrepancia descubierta al agregar pull Shopify al analytics monitor: Shopify=1 orden $1,485 MXN vs GA4=0).

**Root cause:** `theme.liquid` solo corre en `lofitness.club`. El checkout de Shopify corre en `shop.app` / `checkout.shopify.com` — el gtag nunca se ejecuta ahí, entonces GA4 nunca recibe `purchase`. Bug clásico post-checkout.liquid-deprecation.

**Fix:** Shopify Custom Pixel (Settings > Customer Events > Add custom pixel). Corre en sandbox cross-domain incluyendo thank-you page. Subscribe a `checkout_completed` (crítico), `checkout_started`, `product_added_to_cart`. Envía a GA4 via Measurement Protocol.

**Why not theme gtag / Google & YouTube app:**
- gtag en theme: no ejecuta en checkout domain (el bug original)
- G&Y app: dependencia externa, menos control
- Custom Pixel: nosotros controlamos el código, zero maintenance, Japan-proof

**How to apply (para replicar a GR/HC si aparece mismo bug):**
1. GA4 Admin > Data Streams > stream web > Measurement Protocol API secrets > Create > copy value
2. Shopify Admin > Settings > Customer Events > Add custom pixel > paste JS template > Save > Connect
3. Template JS: `04. WEBSITE/{client}-pixel/{client}_ga4_purchase_pixel_CUSTOM.js` (hardcodear MEASUREMENT_ID + API_SECRET, subscribe con `analytics.subscribe`)
4. Validar: sintético MP vía `/debug/mp/collect` (debe dar `validationMessages: []`), luego orden real, luego GA4 Realtime

**IDs LF:**
- Measurement ID: `G-89BJG65M7L`
- Property: `484501054`
- Stream: `10483611619` (NO confundir con `14368812728`/`G-PRZNDSHB3R` que es stream huérfano en otra property)
- MP Secret: `1diNWDWDSmKMHO0SirBNdw` (GH secret: `LF_GA4_MP_SECRET`)
- Pixel name en Shopify: `LF GA4 Purchase Tracking`

**Cómo NO se puede crear via API:**
Shopify Admin API solo expone `webPixelCreate` (requiere app extension pre-registrada). Custom pixels con JS arbitrario solo via UI. `write_custom_pixels` scope permite READ pero no CREATE.

**Validación:**
- Test sintético MP 2026-04-14: HTTP 204, validationMessages=[], transaction_id TEST-1776186365 enviado
- Validación end-to-end con orden real: pendiente 2026-04-15 (re-correr lf-analytics-monitor ventana 1d y comparar GA4.purchases vs Shopify.orders)
