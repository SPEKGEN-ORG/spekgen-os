# GHL F24 — Setup que necesita el bot (para Pedro, en la UI)

> La API/PIT NO crea pipelines ni custom fields en GHL v2 → se hacen en la UI.
> El bot ya está construido y conectado a la location F24 (`HNuSoIl2aCXP2DXEdMVZ`).
> Esto es lo que falta del lado GHL para que el funnel quede completo.

## 1. Canal de WhatsApp + reenvío inbound a Make (CRÍTICO — desbloquea el bot)
- Chip/número de WhatsApp ya conectado a la subcuenta F24 ✓ (2026-06).
- **Falta: el Workflow que reenvía cada mensaje entrante al webhook de Make.** Sin esto,
  el bot NUNCA recibe mensajes. Es UI de GHL (no se puede por API). Receta exacta (espejo de HC):

  **Workflow GHL "F24 Bot — Inbound a Make"**
  - **Trigger:** `Customer Replied` → Channel = **WhatsApp** (o "Inbound Message", canal WhatsApp).
  - **Acción:** `Webhook` (Premium action)
    - Method: **POST**
    - URL: `https://hook.us2.make.com/kuyq4cksp5cy6pg9ka4mh0uriorti9o6`
    - Body (Custom Data / JSON), con estos campos exactos (los lee el módulo 1 del scenario):
      - `contact_id`  = `{{contact.id}}`
      - `message.body` = `{{message.body}}`  *(el texto del mensaje entrante)*
      - `full_name`   = `{{contact.name}}`
      - `phone`       = `{{contact.phone}}`
  - Guardar + **Publish** el workflow.
  - Nota: NO filtrar por tag aquí — el scenario de Make ya maneja whitelist (`bot test`) y
    pausa (`bot-pausado`). El workflow solo reenvía TODO inbound de WhatsApp.

## 2. Tags
- `bot-pausado` — freno manual. Cuando un asesor toma un chat, aplica este tag y el bot
  se calla; al quitarlo, el bot retoma. (Se autocrea al aplicarlo la 1ª vez.)
- `bot test` — whitelist. Mientras el bot esté en modo prueba (WHITELIST_MODE=True), SOLO
  responde a contactos con este tag. Aplícalo al contacto de Gibran para probar.

## 3. Pipelines (2) — mapeados al ciclo real del pedido (no por fuente de ads)
> **Decisión (2026-06-17):** los pipelines mapean el PROCESO. La fuente de ads
> (Facebook / Google / directo / orgánico) NO se parte en pipelines separados — vive
> como **campo de oportunidad `fuente`** (ver §6), porque ya existe la capa de
> atribución (workflow `FB/GL Tagging` + tagger Make 5405187 + tags `fuente-*` +
> campo `wa_gclid`) y las conversiones a Meta CAPI / Google ya disparan solas,
> independientes del pipeline. Filtrando por `fuente` obtienes las vistas FB vs Google.

**Pipeline A — "Ventas WhatsApp (B2C)"** (el principal — agro / construcción / herramienta):
  Cada etapa la mueve el bot/edge function, no a mano:
  1. **Nuevo lead** — inbound WhatsApp (ya viene con tag `fuente-*` del tagger)
  2. **Calificando** — bot en descubrimiento (proving questions)
  3. **Cotizado** — bot armó cotización ítem×ítem del catálogo
  4. **Pedido creado / link enviado** — `f24-process-order` creó Draft Order + invoice/MP link
  5. **Pago iniciado** — tag `pago-clic` (clic en `f24-pay`)
  6. **Ganado (pagado)** — `f24-mp-webhook` / order paid → llena `numero_pedido` + `tracking_url`
  7. **Perdido** — sin respuesta tras D3/D8/D18, o `requiere-humano` que no cerró

**Pipeline B — "Procurement B2B / Mayoreo"** (proceso distinto — proveedor / volumen):
  Lead B2B → Calificado → Cotización volumen → Alta de proveedor (docs fiscales) → Negociación → Ganado / Perdido

## 4. Custom fields (para que el bot lea estado del pedido)
Crear estos campos de contacto (los llenará un workflow "Orden Recibida" estilo HC cuando
exista, y el bot los LEE para dar seguimiento):
  - `tracking_url` (texto) — link de seguimiento del pedido
  - `numero_pedido` (texto)
  - `purchase_count` (número)
> Cuando estén creados, pásame sus **IDs** (Settings → Custom Fields) y los cableo en
> `build_f24_bot_blueprint.py` (constantes `F24_CF_*`). Sin esto el bot igual funciona;
> solo no da seguimiento de pedidos por número.

## 5. Datos de Sergio (para cerrar capacidades)
- **Cuenta bancaria de Ferre24** (CLABE/banco/titular) para pago por transferencia
  → mientras no exista, el bot escala transferencia a humano (no inventa CLABE).
- **Paquete fiscal** (CSF, opinión 32D, acta, comprobante, datos bancarios) para alta de
  proveedor → el bot lo ofrece y escala; el asesor lo manda.

## 6. Campo de oportunidad `fuente` (la "rama" FB vs Google)
Crear **un custom field de tipo OPPORTUNITY** (Settings → Custom Fields → Opportunity):
  - `fuente` (Single Option) con opciones: `facebook`, `google`, `directo`, `organico`.
Lo llena el bot al crear la oportunidad, derivándolo de los tags `fuente-*` que ya pone el
tagger (`wa_gclid` presente → `google`; tag Meta/FB → `facebook`; etc.). Con esto, en
Opportunities filtras cualquiera de los 2 pipelines por `fuente` y tienes los tableros
Facebook vs Google (y directo/orgánico) sin duplicar pipelines.

## 7. Opp-tracking del bot — ✅ LIVE (2026-06-17, blueprint v4.5 PROD)
El bot ya hace `upsert` idempotente de oportunidad (`POST /opportunities/upsert`, match por
contacto+pipeline) en el pipeline **"Ventas Whatsapp"** (`d8xeJjhr4wkmPv8xr5bA`) y la avanza
de etapa según la conversación, con guardia solo-avanza (`opp_stage` 1-4 en el datastore →
nunca retrocede):
  - **Nuevo lead** (`27df7384…`) — primer mensaje atendido
  - **Calificado** (`24098db0…`) — `products_mentioned` no vacío
  - **Cotizado** (`19ba1a33…`) — señal `quoted:true` (el bot dio precio)
  - **Link de pago enviado** (`e327d976…`) — `action=create_order`, `monetaryValue` = total real

Hecho en la fuente (`build_f24_bot_blueprint.py` + `F24_BOT_SYSTEM_PROMPT.md`), data structures
Make `388280` (campo `quoted`) y `403910` (body upsert). Validado: endpoint idempotente + DEV
`isinvalid:False` + PROD live. **Source** de la opp = "whatsapp-bot"; la segmentación FB vs
Google sale de los tags `fuente-*` del contacto (ya existentes).

### Pendiente Fase 2 (no urgente)
- **Ganado** = `f24-mp-webhook` pone `status:won` al confirmarse el pago (la edge function ya
  toca GHL; falta agregarle el move de opp).
- **Perdido** = al agotar el re-engagement (D18 sin respuesta) → `status:lost`.
