---
name: HC Bot LIVE (v2.8.2 Chucho Bot identity + open whitelist + dev scenario)
description: HC AI Bot WhatsApp v2.8.2 deployed 2026-04-24. Whitelist OFF — bot responde a TODOS los contactos HC (freno manual = tag `bot-pausado`). Scenario 4781819 PROD, 4851547 DEV. Self-pause auditado 2026-05-02 — asimétrico: bot LEE tag pero NO lo escribe; mutea via datastore (id 10 = 24h user_request, id 25 = 4h human) — por eso Monse/Gibran no ven el pausado en inbox GHL.
type: project
originSessionId: 335bed10-e44f-4566-a538-b33301229a6c
---
# HC Bot — Estado LIVE (v2.8.2 whitelist OFF + dev scenario, 2026-04-24)

## Versión actual v2.8.2 (2026-04-24)

**Whitelist OFF.** Bot abre a todos los contactos HC. Freno manual = tag `bot-pausado` (router filter pre-route bloquea cualquier route si el tag está presente).

**SOP Monse:** cuando tome un chat humano activo, aplicar `bot-pausado` desde inbox GHL. Cuando cierre el caso, quitar el tag → bot retoma.

**Contactos taggeados `bot-pausado` al abrir (2026-04-24):**
- `GqHou650kJWckO3HJb2Q` — Veronica Echeverri (+52 55 8686 5758). Conversación activa por Mika (anemia) + transferencia pendiente. Quitar tag cuando cierre la venta.

## Self-pause mechanism (auditado 2026-05-02 — ESPEJO ASIMÉTRICO)

Auditoría completa del scenario 4781819 confirma **3 fuentes de pausa, 0 escritura de tag**:

| Fuente | Módulo | Cómo activa | Cómo detiene |
|---|---|---|---|
| **Tag GHL `bot-pausado`** | id `4` (`builtin:BasicRouter`) filtro "NO tiene tag 'bot-pausado'" — `{{join(11.contact.tags;"|")}}` `text:notcontain` `bot-pausado` | Manual (Monse / Gibran via GHL UI o `add_contact_tags`) | Router se salta TODO. Cero respuesta, cero Claude call |
| **Datastore `bot_muted_until` futuro** | id `2` (GetRecord ds 92713) → id `24` SetVariables `existing_mute_active = bot_muted_until > now` | Self-write desde id `10` (Claude `action="human_handoff"` → +24h, `muted_by=user_request`) | Filtros de id `5` (greeting) e id `12` (Claude branch) gateados por `should_respond=true` |
| **Outbound humano ≤4h** | ids `20→21→22→23` polling `/conversations/{id}/messages` + aggregator filtro "Outbound humano en ventana de handoff" → id `24` `is_human_active = length(23.array)>0` | Cuando id `25` (DataStoreAddRecord, route C, filtro `is_human_active=true`) escribe `bot_muted_until = now+4h`, `muted_by=human` | Mismo: `should_respond=false` apaga branches |

**Decisión central — id `24` (`util:SetVariables`):**
```
is_human_active     = if(length(23.array) > 0; "true"; "false")
existing_mute_active = if((ifempty(2.bot_muted_until;"") != "") && (parseDate(2.bot_muted_until) > now); "true"; "false")
should_respond      = if((length(23.array) = 0) && ((ifempty(2.bot_muted_until;"") = "") || (parseDate(2.bot_muted_until) <= now)); "true"; "false")
mute_until_iso      = formatDate(addHours(now;4); "YYYY-MM-DDTHH:mm:ss[Z]")
```

**Asimetría crítica:** el scenario **lee** el tag `bot-pausado` pero **nunca lo escribe**. Cuando el bot detecta handoff (Claude → `action="human_handoff"`) o detecta humano respondiendo, mutea SOLO el datastore — nunca propaga al tag GHL. Implicaciones:

- ✅ El bot **se silencia solo** correctamente (verificado caso `.` / +5219541147118 hoy 2026-05-02 10:21 — `tags:[]` pero bot dejó de responder porque id `10` escribió `bot_muted_until = +24h` con `muted_by=user_request`).
- ⚠️ **Inbox GHL no muestra que el bot está pausado** — las únicas señales son el datastore (no visible en UI) y el último mensaje del bot ("te paso con alguien del equipo"). Monse podría asumir que el bot sigue activo.
- ⚠️ **Si Gibran/Monse aplican el tag manualmente** (como hice yo hoy), redundante pero idempotente — no rompe nada.

**Trigger keywords (en system prompt Claude R31, no en filtros Make):**
```
"quiero hablar con alguien", "quiero hablar con una persona", "quiero hablar con Monse"
"un humano", "una persona", "alguien del equipo"
"no quiero bot", "bot no", "no quiero hablar con bot"
"pasame con alguien", "pasame con Monse"
```

R30 (identidad — NO escala): `"¿eres bot?"`, `"¿es Monse?"`, etc. → Claude responde V1-V6, sigue atendiendo.

**Mejora pendiente (opcional):** agregar branch en route B post-Claude que llame `add_contact_tags` con `bot-pausado` cuando `8.action = "human_handoff"`. Beneficio: visibilidad en inbox GHL + permite que Monse vea quiénes están con humano. Costo: 1 módulo http + risk de divergencia datastore/tag (datastore vence en 24h, tag necesitaría removal explícito).

**Trade-off documentado:** mantener asimétrico mientras Monse no use tags como protocolo activo. Si en futuro Monse adopta tag-driven workflow → wire la escritura del tag.

## Arquitectura PROD + DEV

| Scenario | ID | Hook | Estado | Propósito |
|---|---|---|---|---|
| **PROD** | `4781819` | `2177719` | ACTIVE | Tráfico real GHL → WhatsApp |
| **DEV** | `4851547` | `2210913` | INACTIVE | Iteraciones de features (cart creation, nuevos intents, etc.) |

**Workflow de iteración:**
1. Edita `build_hc_bot_blueprint.py` o `HC_BOT_SYSTEM_PROMPT.md`
2. `python3 build_hc_bot_blueprint.py` → genera `/tmp/hc_bot_bp_v1.json`
3. `./deploy_bot.sh dev v2.9.0-rc1` → deploy a dev scenario
4. Test con `scenarios_run` + payload mock (copiar de executions_list de prod)
5. Si pasa → `./deploy_bot.sh prod v2.9.0` → deploy a prod

**Limitación webhook:** 1 hook = 1 scenario. Dev tiene su propio hook (2210913). Para test end-to-end con WhatsApp real, swap temporal: prod OFF → dev ON → mandar mensaje al GHL webhook URL (que apunta al hook prod 2177719, NO llegaría a dev) — por eso dev es solo para test de lógica vía `scenarios_run`.

**Deploy script:** `HC - 08. WHATSAPP/deploy_bot.sh <prod|dev> <version-tag>` — swap automático del hook según target, archiva blueprint en `_BLUEPRINTS/` con timestamp.

## Versión anterior v2.8.1 (2026-04-24 madrugada)

**Fix regression parseJSON.** Builder re-introducía `parseJSON(3.data).contact.*` en módulo 26 porque el fix v2.7 fue un patch post-builder one-off. Persistido en `customer_context_module()`: ahora referencia `11.contact.*` (módulo 11 json:ParseJSON upstream del router). También persistido patch módulo 10 (24h human_handoff mute) en `datastore_add_claude()`.

## Versión v2.8 (2026-04-23 evening)

## Versión actual v2.8 (2026-04-23 evening)

**Identity flip:** de "eres parte del equipo HC (humano)" a "eres el Chucho Bot (AI, transparente)". Eliminada regla "NUNCA aclares que eres bot".

**Nuevas reglas:**
- **R29 — INTRO TURNO 1:** cuando historial == "(primera interaccion, sin historial previo)", Claude incluye al inicio 1 de 6 variantes literales con personalidad (V1-V6), con fallback firstName opcional.
- **R30 — CONFIRMACIÓN IDENTIDAD:** si user pregunta "¿eres bot?", "¿es Monse?", etc., Claude responde una variante V1-V6 + continúa atendiendo. NO escala.
- **R31 — HUMAN HANDOFF:** si user insiste "quiero humano", "no quiero bot", etc., Claude emite `action: "human_handoff"` + mensaje de cierre.

**Module 10 (datastore upsert post-Claude) patched:**
- `muted_by = if(8.action = "human_handoff"; "user_request"; preserve)`
- `bot_muted_until = if(8.action = "human_handoff"; now+24h; preserve)`

Diferencia vs mute polling 4h: polling-handoff (humano respondió manual) → Route C módulo 25 → 4h, `muted_by=human`. User-requested (cliente pidió humano) → Route B módulo 10 → 24h, `muted_by=user_request`.

**6 variantes intro (V1-V6)** en el md del prompt, todas con emojis 🤖🐶🐾💊📦, personalidad "bot pero de los despiertos". Claude random-picks.

## Versión anterior v2.7 (2026-04-23 mañana)

## Versión v2.7 (2026-04-23 mañana)

**Fix crítico:** módulo 24 usaba `and()`/`or()` — no existen en IML. Reescritas 2 variables (`existing_mute_active`, `should_respond`) con `&&`/`||`. Ver `feedback_make_iml_no_and_or_functions.md`.

**Nuevo: CUSTOMER CONTEXT injection.**
- **Módulo 26** (`util:SetVariables`, insertado al inicio de route 1 del router) extrae:
  - `first_name` = `parseJSON(3.data).contact.firstName`
  - `tracking_url` = custom field `OBs4k0YKs56hj2RirRpY` (URL completa Shopify `/orders/{token}/authenticate?key=…`)
  - `numero_pedido` = `CtF8O0zRTly1rO40iz4Y`
  - `last_products` = `OAxAoOCIGbqoT3uVNCFD`
  - `last_purchase_date` = `e5u636XsMKIXTI6vpJxD`
  - `last_purchase_value` = `yEBpa3vac8KdwxoXwwjs`
  - `purchase_count` = `cv7D5NT7994PHuxJmeXu`
  - `ltv_total` = `i1AB2LSLISEYZsBD1IUs`
  - `abandoned_cart_url` = `Wb6DcdYwEeunrQskxd5u`
  - Patrón IML: `{{ifempty(get(map(parseJSON(3.data).contact.customFields; "value"; "id"; "<ID>"); 1); "")}}`
- **Módulo 12** (`user_message_content`) agrega bloque `[CONTEXTO DEL CLIENTE]` al inicio con valores de `{{26.*}}`.
- **Módulo 7** (system prompt Anthropic) agregadas reglas R22–R28: tracking URL literal (nunca inventar), saludo con firstName real, recurrentes vs nuevos, carrito abandonado.

**Fuente de los custom fields:** Workflow GHL "Orden Recibida" (id `04abf7e2-667f-4fdb-975e-8e2297733cf0`, v46, published) construido por Pedro. Se dispara con orden Shopify confirmada, actualiza en GHL los fields citados. El mismo workflow envía el template WhatsApp de confirmación con el link `tracking_url`.

## Historia

## Historia
- 2026-04-21 19:42 UTC: prompt v2.5.1 deployed, WHITELIST=False (open to all)
- 2026-04-22 ~02:00 UTC: feedback Verónica forzó rollback. Bot le habló como "Hector". Bot se identificó como "Monse". Bot respondió encima de mensaje manual de Gibran.
- 2026-04-22 ~02:15 UTC: prompt v2.6 deployed + WHITELIST=True (rollback)
- 2026-04-22 ~03:53 UTC: **POLLING-BASED AUTO-HANDOFF deployed** (módulos 20-25). Scenario re-activado. Listo para reabrir a TODOS tras validación.

## Versión deployed
- **Prompt:** v2.6 (2026-04-22) — IDENTIDAD equipo HC (no Monse) + ANTI-NAME-CONFUSION + DISPARADORES escalación. ~36KB.
- **Scenario Make:** `4781819` (HC AI Bot — WhatsApp), team 354061 — `isActive: true`, `isinvalid: false`
- **Webhook:** `2177719` — `https://hook.us2.make.com/p7eno8hqwpcwa7b8ddlcoi2ky9q5gv5i`
- **Datastore:** `92713` (memoria + bot_muted_until + muted_by ahora EN USO)
- **WHITELIST_MODE:** `True` — solo responde a contactos con tag `bot test` (Gibran)
- **Kill-switch:** tag `bot-pausado` en GHL silencia contactos específicos
- **Modelo:** `claude-haiku-4-5-20251001`

## Polling-based auto-handoff (nuevo 2026-04-22)

### Diseño elegido vs webhook outbound
Descartamos GHL OutboundMessage webhook por dependencia de UI access (Monse no onboardeada, complejidad config). En su lugar: polling de la conversations API de GHL ANTES de responder. Cero infra extra, cero dependencia humana.

### Flujo (ids reales en blueprint)
```
1 webhook → 2 datastore_get → 3 ghl_get_contact → 11 parse_contact
  → 20 ghl_search_conversation (GET /conversations/search?contactId=...)
  → 21 ghl_list_messages (GET /conversations/{id}/messages?limit=20, stopOnHttpError=false)
  → 22 iterator (BasicFeeder sobre messages.messages)
  → 23 aggregator (BasicAggregator con filter discriminador humano)
  → 24 SetVariables (is_human_active, existing_mute_active, should_respond, mute_until_iso)
  → 4 router con 3 routes:
       Route A (greeting) → filter incluye should_respond=true
       Route B (Claude pipeline) → filter incluye should_respond=true
       Route C (mute) → filter is_human_active=true → datastore upsert bot_muted_until=now+4h
```

### Discriminador humano (filter del aggregator módulo 23)
2 OR-groups, ambos requieren: `direction=outbound` + `source!=workflow` + `dateAdded >= now-4h`. Adicional:
- **Group 1 (UUID):** `length(userId) > 30` — match cuando GHL UI o API humano
- **Group 2 (móvil):** `length(userId) < 30` + `from NO contiene espacios` — match cuando Monse responde desde WhatsApp app de su móvil (formato `+5213326402219` sin espacios). Bot/GHL UI usan `+52 1 33 2640 2219` con espacios.

### should_respond logic (módulo 24)
```
should_respond = (length(23.array) = 0) AND (bot_muted_until = "" OR bot_muted_until <= now)
```
Bot solo responde si: NO detectó humano activo en ventana 4h Y no hay mute previo válido.

## Arquitectura anti-crash JSON (no tocar sin entender)
4 defensas activas tras 2 crashes "Source is not valid JSON" del 2026-04-21:
1. **Prefill en API request:** `messages[-1] = {"role": "assistant", "content": "{"}` — fuerza a Claude a continuar desde `{`
2. **Fallback ifempty:** `ifempty(content[0].text; content[1].text)` — cubre simple + extended-thinking shapes
3. **Prefix `{` en mapper:** `"{" + trim(...)` reconstruye JSON completo
4. **Strip fences + trim:** belt-and-suspenders por ``` extra

Mapper canónico módulo #8: `{{"{" + trim(replace(replace(ifempty(7.data.content[0].text; 7.data.content[1].text); "```json"; ""); "```"; ""))}}`

## Pipeline end-to-end
- Inbound WhatsApp → GHL webhook → scenario 4781819 → polling handoff check → router
- Saludo simple → canned response (sin IA)
- Conversación compleja → Claude Haiku + datastore memoria + GHL send
- Ready-to-buy confirmado (gate #13 user msg contiene `"127 5350"` + gate #16 Claude eval `ready=true`) → Edge Function `hc-process-order` → Draft Order Shopify + row HC_CUSTOMERS_LOG

## Edge Function companion
- **Endpoint:** `https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/hc-process-order` (v3 Supabase)
- **Modos:** calculate_totals, validate_receipt (Claude Haiku Vision), create_draft_order, test_sheets_sync
- Draft Orders bypass Shopify threshold ($2K BRUTO no NETO)
- Sheet HC_CUSTOMERS_LOG `1ISfHucwF1fkxZyfcjdQtr29_kVU81sRUvwG7nAtRc_Y`

## Pendientes conocidos
1. ~~AUTO-HANDOFF~~ ✅ DONE 2026-04-22 (polling-based)
2. **Reabrir bot a TODOS:** validar polling-handoff con 5+ pruebas reales (Gibran y Monse responden manual mid-conversation, verificar bot se silencia 4h). Después: cambiar `WHITELIST_MODE=False` en builder + re-push.
3. **UX:** quitar link CDN `DATOS_TRANSFERENCIA.png` del mensaje de transferencia (se ve como link feo).
4. **Validación auto comprobantes:** `validate_receipt` mode existe en Edge Function pero NO wired al scenario. Falta branch: detectar imagen inbound → bajar URL → POST validate_receipt → si score alto → create_draft_order.
5. **Borrar drafts test Shopify:** `#D2` + `#D3` siguen OPEN.
6. **Shopify discounts:** verificar Automatic Discounts 5%/10% activos + borrar `CHUCHO10`.

## Test plan polling-handoff (validar antes de reabrir)
1. Cliente whitelist manda mensaje → bot responde normal.
2. Gibran responde manual via GHL UI → siguiente mensaje del cliente NO recibe respuesta del bot (Route C silencia + Route A/B bloqueadas).
3. Monse responde desde su móvil (WhatsApp app) → mismo comportamiento.
4. Verificar datastore record: `bot_muted_until` 4h en futuro, `muted_by: human`.
5. Editar manualmente `bot_muted_until` 5 segundos en pasado → cliente manda otro mensaje → bot SÍ responde.

## Cleanup 2026-04-22
- Borrados (capture infra ya no necesaria): scenario 4823525, hook 2197472, datastore 93862, structure 347011.

## Lecciones del incident Verónica (2026-04-21)
- Bot infirió nombre del HISTORIAL → fix: regla anti-name-confusion v2.6 + reset record.
- Bot se identificó como Monse → fix: v2.6 "eres parte del equipo HC".
- Bot no detectó humano → fix: polling auto-handoff (deployed hoy).

## Archivos clave
- System prompt: `HC - HEALTHY CHUCHOS/HC - 08. WHATSAPP/HC_BOT_SYSTEM_PROMPT.md`
- Builder: `.../HC - 08. WHATSAPP/build_hc_bot_blueprint.py` (constants `HC_LOCATION_ID`, `HANDOFF_HOURS=4`, `WHITELIST_MODE=True`)
- Canned: `.../HC - 08. WHATSAPP/HC_BOT_CANNED_RESPONSES.md`
- KB: `.../HC - 08. WHATSAPP/HC_BOT_KNOWLEDGE/products/` + `PRICING_COMBOS.md`
- Edge Function: `.../HC - 18. PEDIDOS/_BACKEND_SUPABASE/hc-process-order/index.ts`
- Diseño handoff (histórico): `.../HC - 08. WHATSAPP/AUTO_HANDOFF_DESIGN.md` (descartado a favor de polling, dejar como referencia o mover a `_DONE/`)

## Confianza / monitoreo pre-Japón
- Alta confianza (95%+) anti-crash JSON
- Alta confianza polling-handoff anti-talk-over (cubre 3 canales: GHL UI / GHL API / WhatsApp móvil)
- Recomendado: cron check diario que valide ≥1 exec con status:1 en últimas 24h del scenario 4781819
- Alerta email si `dlqCount > 0` o status ≠ 1 en cualquier execution
