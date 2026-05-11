---
name: HC order notification recipients (Make 4780535 + 4780569)
description: Lista de destinatarios internos en los flows de pedido/status/ticket de Healthy Chuchos en Make
type: project
originSessionId: 488d15ae-e070-43e1-81d9-9d3772590860
---
Los flows internos de notificación de pedidos HC viven en 2 Make scenarios. Destinatarios actuales (2026-05-01):

**Scenario 4780535** — `HC - Nuevo Pedido Almacen` (webhook Shopify `orders/create`)
- Mod 3 `[PAGO PENDIENTE]` (filtro: `financial_status=pending` — OXXO/transferencia):
  - asuarezmanriquez@gmail.com
  - almacenmetagreen@gmail.com
  - monsealonzougc@gmail.com
  - gibran.alonzo0506@gmail.com
  - ceo.organicnow@gmail.com (CEO Organic Now, agregado 2026-05-01)

**Scenario 4780569** — `HC - Pago Confirmado Almacen` (webhook Shopify `orders/paid`)
- Mod 2 `[PAGO CONFIRMADO]` con guía Skydropx + ticket brandeado adjuntos:
  - mismos 5 que arriba
- Mod 5 `🚨 Edge function falló` (alerta status si `hc-process-order` no generó guía):
  - gibran.alonzo0506@gmail.com
  - ceo.organicnow@gmail.com

**Why:** El CEO de Organic Now (Gibran's papá Enrique Alonzo Carabez via Organic Now infra) recibe loop de todas las operaciones de pedido HC. Decisión: solo en flows internos (almacén/ops), NUNCA en customer-facing (`hc-abandoned-mailer` y futuro ticket-al-cliente).

**How to apply:**
- Si se agrega un nuevo flow interno de pedido/status (Sprint B ticket al cliente, webhook Skydropx tracking, follow-up post-entrega), preguntar a Gibran si CEO va en BCC.
- Si se necesita modificar la lista, editar via `mcp__18578e46__scenarios_update` con blueprint completo (full shape: name+flow+metadata+scheduling+interface — ver `feedback_make_scenarios_update_full_shape.md`).
- Doc operativo: `HC - HEALTHY CHUCHOS/HC - 18. PEDIDOS/_AUTOMATION_STATUS.md` (mantener sincronizado).
