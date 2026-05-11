---
name: Make http:ActionSendData v3 param locations
description: gzip/useMtls/serializeUrl/useQuerystring van en mapper (no parameters). json() helper YA NO FUNCIONA en Make IML desde ~2026-04-21 — usar flat payload + reassembly en backend.
type: feedback
originSessionId: 3a9fb5be-5b36-4397-870f-d6f45e992e8d
---
Make `http:ActionSendData` version 3 tiene dos gotchas que costaron ~45 min debugging HC 4780569 el 2026-04-20 + 2hrs extras el 2026-04-22:

**Gotcha 1: ubicación de params booleanos.** Estos 4 keys van en `mapper`, no en `parameters`:
- `serializeUrl` (default false)
- `useQuerystring` (default false)
- `gzip` (default true)
- `useMtls` (default false)

`parameters` solo acepta: `handleErrors` (required) + `useNewZLibDeCompress` (default true).

Si los pones en `parameters` al pushear via `scenarios_update`, el push acepta, pero en runtime Make tira `BundleValidationError: Validation failed for 4 parameter(s)` y desactiva el scenario.

**Gotcha 2: `json()` helper DEPRECADO (~2026-04-21).** Antes se usaba `{{json(1.line_items)}}` para serializar arrays/collections en raw body. **Ya no funciona** — Make tira `Failed to map 'data': Function 'json' not found!` y desactiva el scenario con `isinvalid:true`. Descubierto cuando HC scenario 4780569 falló silenciosamente el 2026-04-20 20:00 MX y warehouse no recibió emails de pedidos reales (order #1033).

**Why:** Make runtime cambió el set de IML functions disponibles. `json()` ya no está en la whitelist. Probablemente también `parseJSON()` y otros helpers de serialización están afectados — verificar antes de usar.

**Fix canónico: flat payload + reassembly en backend.** En lugar de enviar estructura anidada:
```json
{"order": {"id": "{{1.id}}", "line_items": {{json(1.line_items)}}, ...}}
```
Envía planamente:
```json
{"order_id": "{{1.id}}", "item_1_title": "{{1.line_items[1].title}}", "item_1_quantity": "{{1.line_items[1].quantity}}", "shipping_name": "{{1.shipping_address.name}}", ...}
```
Y en el backend detecta flat payload + re-arma la estructura:
```ts
function assembleOrderFromFlat(body) { ... }
const order = body.order ?? (isFlatOrderPayload(body) ? assembleOrderFromFlat(body) : body);
```

Ver implementación completa en `HC - 18. PEDIDOS/_BACKEND_SUPABASE/hc-process-order/index.ts` líneas 336-370 (helpers) + dispatch en `generate_shipping_label` handler.

**How to apply:**
1. Para CUALQUIER módulo http:ActionSendData v3: antes de push, llamar `mcp__...__app-module_get` con format=instructions, armar parameters/mapper exactamente según schema.
2. Para body con arrays/collections: NUNCA usar `{{json(...)}}`. Refactorizar a flat payload con sufijos numerados (`item_1_*`, `item_2_*`, etc., hasta N fijo — HC usa 10 items max).
3. Backend debe tolerar ambos shapes (legacy nested + nuevo flat) para migración gradual cross-scenario.
4. Si scenario se desactivó por `isinvalid:true`: `scenarios_update` + `scenarios_activate` lo valida server-side y limpia el flag (update solo NO basta — flag queda stale).
5. Para validar end-to-end sin disparar acción real: `scenarios_run` corre solo el trigger module (1 operation), no inyecta data al webhook. La validación real llega con el próximo POST en producción.
