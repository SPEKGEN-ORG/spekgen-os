---
name: GR WhatsApp Bot + Manual Replies State
description: Estado del bot WhatsApp de GreenRay — LIVE desde 2026-04-10 con Make + Claude Haiku 4.5, arquitectura completa y discrepancia ARTRIX pendiente
type: project
---

# GR WhatsApp Bot — LIVE ✅ WHITELIST MODE (2026-04-10)

## Estado: FUNCIONANDO end-to-end · WHITELIST_MODE=True (testing)
- Fix definitivo del pause tag `bot-pausado` completado 2026-04-10 20:23 (operador singular `text:notcontain`)
- Safety rollback a `WHITELIST_MODE=True` aplicado 2026-04-10 22:11 despues de que Gibran noto que el bot respondia full-open
- Test E2E validado 2026-04-10 ~22:15: Gibran (con tag `bot test`) recibio respuesta del bot

## Modo de operacion actual (whitelist)
- **Bot responde solo a contactos con tag `bot test`** — en este momento: contacto de Gibran (`B5v1dcyOWqrj7ByGXXsW`)
- Router pre-filter: `{{join(11.contact.tags; "|")}} text:notcontain "bot-pausado"` — bloquea cualquier contacto muteado manualmente
- Route filters (ambas): regex del mensaje AND `text:contain "bot test"`
- Para flipear a produccion (abrir a todos): `WHITELIST_MODE = False` en `build_gr_bot_blueprint.py:42` + rebuild + push via `/gr-bot-update` o `scenarios_update`. Hacerlo solo cuando el prompt este validado con N mensajes reales.

## Leccion clave (del debug de 3+ horas)
**Make filter operators son SINGULAR**: `text:contain`, `text:notcontain`, `text:equal`, `text:notequal`, `text:pattern`, `text:notpattern`. Los plural (`contains`, `notcontains`) NO EXISTEN y fallan silenciosamente bloqueando todas las rutas sin error. Ver `feedback_make_operators_singular.md`.

## Arquitectura Make (scenario 4668313)
Flow 6 módulos:
1. **Custom Webhook** (hook 2127196) — recibe payload de GHL Workflow (snake_case: `contact_id`, `full_name`, `phone`, `message.body`)
2. **Datastore GetRecord** (datastore 89882) — lee historial por `contact_id` con filter `contact_id != ""`
3. **HTTP → Anthropic Messages API** — `claude-haiku-4-5-20251001`, `inputMethod: dataStructure` con data structure 334561 ("Anthropic Messages Request": model/max_tokens/system/messages[]). CRÍTICO: debe usar `dataStructure` no `jsonString` porque Make auto-escapa el `{{1.message.body}}` (si se usa jsonString, caracteres especiales del mensaje rompen el JSON body — error en position 7307).
4. **JSON ParseJSON** (type 333981) — parsea la respuesta del bot, strip markdown fences con `{{trim(replace(replace(3.data.content[1].text; "```json"; ""); "```"; ""))}}`
5. **HTTP → GHL Conversations** — `inputMethod: dataStructure` con data structure 333968, type=`WhatsApp` hardcoded, `contactId: {{1.contact_id}}`, `message: {{join(4.messages; "\n\n")}}`. Auth: `Bearer pit-0b7f3a47-60c7-4150-a3cc-28fa6df4bf4f`
6. **Datastore AddRecord** — guarda historial con overwrite=true

## System prompt (embedded en blueprint, NO en MD aparte)
- Versión actual: v1.3 (2026-04-10) con fix voseo
- Catálogo 52 productos + mapeo síntoma→producto + 14 reglas obligatorias
- Reglas clave: disclaimer médico siempre, never "cura/trata/controla", links obligatorios, tuteo mexicano (tú/ti/te), NUNCA voseo (vos/tenés/querés)
- Formato respuesta: JSON `{"action","messages","products_mentioned","intent"}`

## Credenciales (blueprint plaintext — rotar post-deploy)
- Anthropic API key: `sk-ant-api03-v2hfC8plFf5IE...` (expuesta, rotar ASAP)
- GHL PIT token: `pit-0b7f3a47-60c7-4150-a3cc-28fa6df4bf4f`

## Data structures Make
- 334561: Anthropic Messages Request (model/max_tokens/system/messages array)
- 333968: GHL Conversations body (type/contactId/message)
- 333981: Claude response parser (action/messages/products_mentioned/intent)

## Python builder
`GR - GREENRAY/GR - 08. WHATSAPP/build_gr_bot_blueprint.py` (ubicacion permanente en Drive) — construye el blueprint y lo escribe a `/tmp/gr_bot_bp_v4.json`. Para cambios al system prompt usar SIEMPRE la skill `/gr-bot-update` que automatiza: backup → edit → rebuild → push → activate → verify → changelog → rollback automatico si falla. Nunca editar el builder a mano ni tocar Make UI directamente.

## Skill /gr-bot-update
Path: `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/PERSONALIZADAS/gr-bot-update/SKILL.md`
Changelog: `GR - GREENRAY/GR - 08. WHATSAPP/GR_BOT_CHANGELOG.md` (registra cada cambio al prompt con antes/despues, razon, test sugerido, status)
Backups: `GR - GREENRAY/GR - 08. WHATSAPP/_builder_backups/` (copia del builder pre-edit, timestamped)

## Queue drain pattern
Si quedan mensajes atascados en cola por errores: el filter `contact_id != ""` permite que los bundles stale (sin `contact_id`) terminen en 1 op en vez de errorear con 2+ ops. Esto libera la cola sin perder nada.

## Sprints pendientes post-MVP
- **Sprint B**: Shopify draft order automation cuando `intent=ready_to_buy`
- **Sprint C**: Habilitar canales IG + FB en el GHL workflow (ya soportado por el bot, solo falta config GHL)
- **Sprint D**: Hardening — logs a Sheets (Make módulo paralelo), email alerts on error, SOPs para Japón

## How to apply:
- Nunca volver a modo "manual replies" — el bot está LIVE.
- Si el bot rompe durante Japón: revisar executions_list(4668313), buscar status 3, fix y re-push via builder.
- Cambios al prompt SIEMPRE via `/tmp/build_gr_bot_bp_v4.py` (nunca editar MD suelto que no se refleja).

---

# 🚨 ARTRIX — Discrepancia crítica PENDIENTE (D-020)

**Contexto**: El 2026-04-09 se detectó que ARTRIX estaba mal clasificado en el bot prompt v1.1 (decía DIGESTIVO/reflujo cuando es ANTIINFLAMATORIO/OSTEOARTICULAR). Al arreglarlo, se encontró una segunda discrepancia entre la FT oficial y el COMPLETISIMO log.

## La discrepancia
| Activo | FT oficial (`FICHA Artrix.pdf`) | `GR_PRODUCT_LOG_COMPLETISIMO_v1.0.xlsx` (fila 23) |
|---|---|---|
| Curcumina 95% | 50 mg ✓ | 50 mg ✓ |
| MSM | 100 mg ✓ | 100 mg ✓ |
| **Boro** | **6 mg** | 50 mg ✗ |
| **Calcio de Coral** | **250 mg** | 150 mg ✗ |
| **Ácido Hialurónico** | No en tabla nutrimental (mencionado en beneficios) | 150 mg ✗ |
| **Piperina** | **No existe** | 10 mg ✗ |
| **Cápsula total** | **500 mg** | 510 mg ✗ |

## Estado actual
- Bot prompt v1.2: usa datos de FT oficial (406mg activos confirmados + Ác. Hialurónico sin dosis)
- Product Log Global (v1.0 operativo) — GR-P011 creado con datos de FT oficial
- Completísimo fila 23 — flag `STATUS: DISCREPANCIA FT vs LOG - 2026-04-09` + nota larga
- Regla 11 del bot: FT PDF es la fuente de verdad

## Pendiente
Reconciliar con **Greenmark lab products S.A. de C.V.** (fabricante, Zapopan Jal.) — pueden ser dos versiones de fórmula (vieja vs actual) o errores de transcripción en el completísimo. No se puede hablar de dosis específicas en contenido hasta que esto se reconcilie.

## Why: Si el bot lista ingredientes del completísimo, estaría dando dosis incorrectas al cliente. Regla 11 del prompt (FT PDF es fuente de verdad) previene esto mientras se reconcilia.

## How to apply:
- Si una sesión futura pregunta sobre activos/dosis de ARTRIX → FT PDF (`02. PRODUCTOS/02. FICHAS TECNICAS/FICHA Artrix.pdf`) manda.
- Si alguien va a crear contenido/ads de ARTRIX → NO usar datos del completísimo hasta reconciliar. Usar solo los 4 activos confirmados en FT (Curcumina 50mg, MSM 100mg, Boro 6mg, Calcio Coral 250mg) + mención cualitativa de Ácido Hialurónico sin dosis.
- Si Gibran contacta a Greenmark y confirma una versión: actualizar FT, completísimo, bot prompt, y product log global. Quitar flag.
