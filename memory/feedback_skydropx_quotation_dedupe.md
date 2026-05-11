---
name: Skydropx quotation dedupe trap + EF idempotency gap
description: Skydropx cachea quotations por (origin,dest,parcel,carriers); qid muerta no se renueva. EF hc-process-order no maneja esto ni idempotency en re-llamadas
type: feedback
originSessionId: 9c89afc3-59bd-4a57-bca0-057858abed5f
---
Skydropx Pro (`pro.skydropx.com/api/v1`) deduplicates `POST /quotations` by `(origin, dest, parcel, requested_carriers)` tuple. Si en el primer poll un carrier devuelve `no_coverage` o `not_applicable`, esa `qid` queda inmutable y cualquier POST posterior con los MISMOS params devuelve la misma `qid` muerta. **Re-llamar al EF `hc-process-order` no resuelve** — sigue cayendo en `no_rates` indefinido.

**Why:** Descubierto procesando manual la orden HC #1036 (Mexicali BC 21250) el 2026-05-06. Primera quotation marcó Estafeta como `no_coverage`/`not_applicable` (probablemente downtime momentáneo del API de Estafeta). El EF pollee 30s, regresó `no_rates`. Re-correr el EF devolvió la misma `qid` (`d1bc40c0-...`) con los mismos rates muertos. Solo al cambiar `requested_carriers` (de `["fedex","dhl","estafeta"]` a un set ampliado con paquetexpress/ups/ampm) Skydropx generó `qid` nueva (`5bd6ce77-...`) y esta vez Estafeta sí dio rate `price_found_internal` $171.22.

**How to apply:**
- Si el EF `hc-process-order` regresa `no_rates` y la orden es real (no test), NO confiar en re-llamarlo. Hablar Skydropx directo desde un script con set ampliado de carriers para forzar `qid` nueva.
- Whitelist segura para auto-pick rate: solo `{fedex, dhl, estafeta}`. Paquetexpress/UPS/AmPm dan rates `external` que requieren campos extra (`consignment_note`, `package_type` por package) que el EF no provee.
- Skydropx shipment shape correcto: `packages[]` array (NO `parcel` singular), con `package_type:"4G"` y `consignment_note:"31181701"` (suplementos) por package. EF ya lo hace bien.
- `address_to.street1` max 45 chars — truncar `address1 + address2` o poner address2 como `street2`.
- **Patrón "fix manual sin disparar webhook":** NO marcar la orden como `paid` en Shopify después de generar la guía manual — eso re-dispara `orders/paid` → Make 4780569 → EF → guía duplicada (~$170 perdidos). Dejar orden en `pending`; cuando MP liquide solo, Shopify se actualizará y disparará el webhook. Hasta que se parche idempotency en EF, hay que pausar Make 4780569 antes de que MP liquide o aceptar la guía duplicada.
- Script de referencia: `HC - HEALTHY CHUCHOS/process_order_1036.py` (formato fix_order_1034*).

**Pendiente parche EF (P0 pre-Japón):**
1. Si `pollRates` regresa 0 internal después de 30s → reintentar con set distinto de `requested_carriers` antes de devolver `no_rates`.
2. Idempotency: chequear si la orden ya tiene `fulfillment` con `tracking_number` antes de cotizar Skydropx. Si sí → skip generación de guía, solo re-emitir email almacén con tracking existente.
