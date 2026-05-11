# HC Order Automation Backend — Supabase Edge Functions

**Status 2026-04-30 PM:** v9 edge function unchanged. Make 4780569 v8 LIVE — agrega filter `tracking_number not empty` en módulo Gmail almacén + nuevo módulo 5 Gmail alerta a Gibran cuando edge function falla (filter opuesto). Backup: `make_backups/scenario_4780569_20260430-130802_pre_router.json`. Trigger del fix: pedido #1035 con dirección rechazada por Skydropx Pro API → email "GUÍA LISTA" vacío llegó al equipo almacén.

**Status 2026-04-22 PM:** v9 DEPLOYED + Make 4780569 v7 LIVE. v9 agrega `zoom: 0.78` en PDFShift para que ticket brandeado quepa en 1 página (warehouse imprimía en 2 hojas). Validado con order #1033 reimpreso y reenviado al equipo almacén.

## v9 cambios (2026-04-22 PM) — Ticket 1-página fix

- `ticket_template.ts:239`: PDFShift body agrega `zoom: 0.78` (escala contenido 78% antes de paginar A4)
- PDF resultante: 262 KB, 1 página garantizada (verificado con conteo `/Type /Page` en bytes)
- Sin cambios al layout HTML — solo escala render
- Si ticket se ve apretado, subir a `zoom: 0.82-0.85` (1 línea, redeploy en 30s)
- Layout HTML preserva los 6 QRs (4 productos + tienda + IG) — Gibran rechazó explícitamente removerlos

## v8 cambios (2026-04-22 AM) — Flat payload bypass de json()

- `index.ts` agrega `isFlatOrderPayload(body)` + `assembleOrderFromFlat(body)` helpers
- Dispatch `generate_shipping_label` ahora acepta:
  - Legacy nested: `{order: {...}}`
  - Nuevo flat: `{order_id, item_N_title/quantity/price, shipping_*, customer_*}`
- Make 4780569 módulo HTTP (id=3) reescrito con ~35 keys planos — cero `json()`
- Memoria `feedback_http_action_send_data_v3_params.md` actualizada con el fix canónico
- ✅ Regresión v8 RESUELTA en v9: deploy v9 incluyó el archivo local completo (839 líneas) con `HC_SA_JSON_B64` base64 hardcoded. `create_draft_order` y `test_sheets_sync` vuelven a funcionar sin necesidad de setear env var en Supabase Dashboard.

**Status anterior 2026-04-20:** v7 DEPLOYED + Make 4780569 v6 LIVE + Make 4780535 v2 LIVE. **Branded ticket PDF integrado al flow.**

Warehouse pipeline 100% autónomo:
- `orders/paid` → Make 4780569 → HTTP Edge Function (Skydropx label + **ticket PDF branded via PDFShift** + Shopify fulfillment) → Email almacén con **2 PDFs adjuntos** (guía + ticket)
- `orders/create` (pending payments only) → Make 4780535 → Email PAGO PENDIENTE (sin guía)
- Email [NUEVO PEDIDO - PROCEDER AL ENVIO] ELIMINADO — duplicaba el email de 4780569

## v7 cambios (2026-04-20 noche) — Ticket Branded PDF

- `ticket_template.ts` + `render_ticket.py` con CDN logo + slim mockups (200×200 q75) — NO base64 embed
- PDFShift 2MB limit es del OUTPUT, no input: mockups 400×400 q85 = PDF 2.3MB (falla); 200×200 q75 = PDF 322KB (OK)
- Edge Function agrega `ticket_pdf_b64` + `ticket_filename` + `friendly_code` ("HC-YYMMDD-XX") a respuesta de `generate_shipping_label`
- Nuevo modo `render_ticket`: renderea PDF SIN tocar Skydropx/Shopify — para smoke tests y re-generación de órdenes viejas
- `PDFSHIFT_API_KEY` embebida como fallback `Deno.env.get(...) ?? "sk_..."` — patrón agencia, no depende de Supabase secrets
- Make scenario 4780569 módulo Gmail: 2º attachment `{{toBinary(3.data.ticket_pdf_b64;"base64")}}` / `{{3.data.ticket_filename}}`
- Blueprint de replicación para GR/LF: `SPK - SPEKGEN AGENCY/SPK - 07. BLUEPRINTS/TICKET_PIPELINE_v1.md`

Sprint B pendiente: ticket al cliente final (email + WhatsApp). Arquitectura de ticket ya renderizable standalone vía `render_ticket` mode.

**v3 cambios vs v2 (2026-04-19 PM):**
- Eliminada dependencia de `MAKE_WEBHOOK_HC_SYNC` (no hay Google Sheets connection en Make team 354061).
- Sheets API directo desde Edge Function via SA JWT RS256 (crypto.subtle) + OAuth 2.0 service-account flow.
- SA `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` hardcoded como fallback (`HC_SA_JSON_B64`).
- Sheet HC_CUSTOMERS_LOG compartido con SA como Editor 2026-04-19 (manual, 1 vez).
- Modo `test_sheets_sync` agregado para diagnóstico.
- Token Google cached in-memory 1h; token Shopify cached 23h.

## Arquitectura

```
Shopify orders/paid webhook
   → Make 4780569 (router)
   → HTTP POST https://wjlwpfaogjpeqgyxxnwa.functions.supabase.co/hc-process-order
       Authorization: Bearer <HC_BACKEND_SECRET>
   ← { tracking_number, tracking_url, label_url, carrier, service, total, fulfillment_id, parcel }
   → Make: email unificado al cliente (ticket v4 HTML + label PDF attached + tracking URL)
   → Make: email almacén con tracking + carrier
```

## Por qué Supabase Edge en vez de Vercel

Regla CLAUDE.md 5: "Archivos locales > web apps. Solo infra web si estrictamente necesario Y con SOPs para Gibran". Vercel requiere `npx vercel --prod` manual de Gibran + setear env vars en dashboard → viola autonomía Japón. Supabase Edge se deploya desde chat vía MCP (`mcp__f3fa92ef...__deploy_edge_function`) sin intervención manual.

Project Supabase: `wjlwpfaogjpeqgyxxnwa` (mismo que Content Hub bucket `post-media`).

## Archivos

- **Edge Function (canónico):** `HC - HEALTHY CHUCHOS/HC - 18. PEDIDOS/_BACKEND_SUPABASE/hc-process-order/index.ts` — Deno/TS, ~280 líneas
- **Vercel scaffolding (fallback histórico):** `HC - HEALTHY CHUCHOS/HC - 18. PEDIDOS/_BACKEND_VERCEL/api/hc-process-order.py` — Python/BaseHTTPRequestHandler. NO borrar.

## Secrets requeridos (Supabase)

```
SKYDROPX_CLIENT_ID
SKYDROPX_CLIENT_SECRET
SHOPIFY_SHOP          (wza1wu-ki.myshopify.com)
SHOPIFY_CLIENT_ID
SHOPIFY_CLIENT_SECRET
HC_BACKEND_SECRET     (generar random, usar en Make Authorization header)
```

## Lógica core

### Packaging
- PRODUCTS: artridog/dogrelax/gastrodog = polvo 290g [10.5×10.5×9.5]; omegadog = cápsulas 110g [5.5×5.5×9.8]
- BOXES: sobre_0 (14g) / rm_85 (71g) / rm_27 (156g) / rm_349 (162g)
- Burbuja: 30g
- Origen: Zapopan 45235 Jalisco
- Pick box: P=0,C≤2→sobre; P=0,C≥3→rm_85; P=1,C≤2→rm_85; P=2-4→rm_27; P=5-8→rm_349; P>8→manual+rm_349

### Skydropx (Pro API v1)
- Base: `https://pro.skydropx.com/api/v1`
- OAuth: `POST /oauth/token` grant=client_credentials scope="default orders.create"
- `POST /quotations` con address_from/to + parcel + requested_carriers:[fedex,dhl,estafeta]
- Poll `GET /quotations/{id}` hasta `rates[].status == "price_found_internal"`
- **Campos reales en rate:** `provider_name`, `provider_service_name`, `total`, `days`, `status` (NO `provider`/`service_level_name`/`rate_status`)
- Pick: Standard = cheapest overall; Express = cheapest donde `days==1`
- `POST /shipments` con `rate_id` → poll `GET /shipments/{id}` hasta `status=completed|generated|ready` o `label_url`/`tracking_number` poblado

### Shopify fulfillment
- OAuth client_credentials (Partners app HC)
- Flow: `GET /orders/{id}/fulfillment_orders` → filtrar `status in (open, in_progress)` → `POST /fulfillments.json` con `line_items_by_fulfillment_order` + `tracking_info.{number, url, company}` + **`notify_customer: false`** (el email va por Make unificado, no por Shopify default)

## Pendientes pre-deploy

1. **Gibran regenera SKYDROPX_API_KEY** en `app.skydropx.com → Configuración → API` (la actual tira 401)
2. Deploy: `mcp__f3fa92ef...__deploy_edge_function` con name=`hc-process-order`, verify_jwt=false, files=[index.ts]
3. Supabase secrets set (los 6 listados arriba)
4. Test end-to-end con orden real → verificar Shopify muestra fulfillment con tracking + Skydropx muestra guía generada
5. Make 4780569: agregar módulo HTTP call → reemplazar email cliente actual con email unificado

## Decisiones de diseño

- **Sync, no async**: backend corre Skydropx flow completo dentro del request (<30s típico). Make espera la respuesta. No usar queue porque Make ya hace el handling del webhook y reintentar desde Make es más simple.
- **Auth bearer custom, no JWT Supabase**: Make manda `Authorization: Bearer $HC_BACKEND_SECRET`. Simple, sin overhead de JWT. `verify_jwt: false` en deploy.
- **Fallback behavior**: si Skydropx no da rates → response `{ok:false, error:"no_rates", parcel}`. Make route debe manejar este caso (alert al almacén para generar manualmente).
