# GHL MCP Server (Custom, Multi-Location)

## Estado
- **LIVE** desde 2026-04-23, 30 tools expuestas como `mcp__ghl__*` en Claude Code
- Registrado en `~/.claude.json` (NO en `settings.json` — Claude Code 2.x no lo lee de ahí)
- Server path: `SPK - SPEKGEN AGENCY/SPK - 16. MCP SERVERS/ghl-mcp/`
- Stack: Python 3.11 (via `uv`) + FastMCP + httpx async + pydantic v2

## Qué resuelve
MCP server custom para GoHighLevel v2 API con soporte multi-location desde día 1. Las 5 sub-accounts de SPEKGEN (HC/LF/GR/MG/SPEKGEN) son accesibles con un solo tool pasando `location` como short name. Server resuelve PIT + locationId desde `_ghl_locations.json` (git-ignored).

## 30 Tools (10 módulos)
- **Contacts (10)**: search_contacts, get_contact, create_contact, update_contact (NO tags!), upsert_contact, add_contact_tags, remove_contact_tags, add_contact_note, list_contact_notes, set_contact_custom_field
- **Conversations (3)**: search_conversations, get_conversation_messages, send_message (SMS/Email/WhatsApp/IG/FB/GMB/Live_Chat/Custom)
- **Opportunities (5)**: search_opportunities, get_opportunity, create_opportunity, update_opportunity, move_opportunity_stage
- **Calendars (3)**: list_calendars, list_appointments, create_appointment
- **Pipelines (1)**: list_pipelines
- **Workflows (2)**: list_workflows, add_contact_to_workflow (remove NO soportado — v1 only)
- **Tasks (3)**: list_contact_tasks, create_task, complete_task
- **Location helpers (3)**: list_custom_fields, list_tags, list_users
- **Forms (1)**: list_form_submissions
- **Meta (1)**: list_configured_locations

## Reglas operativas clave
1. **Siempre pasar `location`** como primer arg — short name: HC, LF, GR, MG, SPEKGEN
2. **Tags append/remove**: usar `add_contact_tags` / `remove_contact_tags`. NUNCA `update_contact` con tags (destructivo, reemplaza todo el set)
3. **Custom fields**: llamar `list_custom_fields` primero para resolver ID, luego `set_contact_custom_field`
4. **Opportunities**: llamar `list_pipelines` para pipeline_id + stage_id antes de CRUD
5. **Pagination**: normalizada a `next_cursor` (GHL tiene 5 estilos distintos; server lo oculta)
6. **Retry 429**: exponencial backoff 1s/2s/4s. Rate limit 100 req / 10s per install

## Cuándo usar (vs Make)
- **GHL MCP**: one-shot, exploración, reportes cross-client, disparar mensaje a 1 contacto, enrollment, notas/tasks
- **Make**: recurrente, cron, forms→upsert+sheets+workflow, bots con state, fire-and-forget, Japan-proof

## Docs
- `ghl-mcp/README.md` — install/configure/register, 32 tools listados, scope table
- `ghl-mcp/docs/RESEARCH.md` — GHL v2 API research compilado (pagination styles, scope map, gotchas)
- `ghl-mcp/docs/evaluation.xml` — 10 evaluation questions
- Platform Selection Protocol en `.claude/CLAUDE.md` root

## Verificación
- 45/45 scope probe matrix: todos los PITs tienen 9 read scopes
- End-to-end: initialize → tools/list (32) → list_configured_locations (5) → list_pipelines HC (3 real)
- `_ghl_locations.json` poblado con credenciales reales (HC, LF, GR, MG, SPEKGEN)

## Caveats
- **Workflow REMOVE** requiere v1 API, NO soportado. Fallback: Make o UI
- **No bulk ops** — si hace falta batch, usar script Python local o Make
- **No location-wide task list** — solo por contacto (GHL limitación)
- **Sin users CRUD, memberships, payments, snapshots** — fuera de scope; agregar si surgen needs
