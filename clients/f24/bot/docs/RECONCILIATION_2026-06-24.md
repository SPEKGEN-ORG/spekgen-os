# Reconciliación bot F24: fork de Drive → repo (2026-06-24)

## Por qué

El bot WhatsApp de Ferre24 se deploya SOLO desde este repo (`main`) vía el GH Action
`f24_promos_sync.yml`. La carpeta de Drive `F24 - 08. WHATSAPP/bot_multimodal/` era un
**fork huérfano**: tenía lógica de producción (edge functions + builders de escenarios)
que NUNCA estuvo versionada en el repo. Esta reconciliación trae esa lógica al repo para
que el fork de Drive pueda eliminarse sin perder código.

## Qué se versionó (antes vivía SOLO en el fork de Drive)

### Edge functions (`edge/`)
Todas ACTIVE en Supabase `wjlwpfaogjpeqgyxxnwa`. **La versión DEPLOYADA en Supabase es la
fuente de verdad** — estas copias locales vienen del fork de Drive y PUEDEN estar atrás del
deploy. Para el source exacto live: Supabase `get_edge_function` / dashboard.

| Función | Versión deployada (2026-06-24) | Rol |
|---|---|---|
| `f24-process-order` | v10 | Draft order Shopify + link de pago + escribe CP en GHL (mode `save_cp`). **Esta copia SÍ es la deployada** (actualizada en esta misma fecha). |
| `f24-pay` | v4 | Link de pago envuelto (tracking de clic) |
| `f24-mp-webhook` | v1 | Webhook MercadoPago (recrea orden Shopify al pagar 9/12 MSI) |
| `f24-media` | v8 | Multimodal: nota de voz → transcripción, foto → match catálogo |
| `f24-opp-track` | v1 | Upsert de oportunidad GHL + avance de etapa |
| `f24-generate-guide` | v2 | Generación de guía (paquetería) |

> ⚠️ Para `f24-pay`, `f24-mp-webhook`, `f24-media`, `f24-opp-track`, `f24-generate-guide`:
> verificar contra el deploy de Supabase antes de re-deployar desde estas copias (pueden lag).

### Builders de escenarios (`scenario_builders/`)
Construyen escenarios Make LIVE distintos del cerebro del bot:
- `build_f24_cart_blueprint.py` — carrito abandonado (scenario 5420839)
- `build_f24_followup_blueprint.py` — re-engagement D3/D8/D18 (cerebro 5278490)
- `create_source_tagger_scenario.py` + `build_google_upload_scenario.py` — atribución/tagger (5405187) + Google upload
- `gen_catalog_compact.py` — genera el catálogo compacto para `f24-media`
- `sync_f24_weights.py` — sync de pesos (prep paquetería)
- `deploy_f24_bot_win.py` — port Windows del deploy (el `.sh` es el canónico)
- `test_f24_bot_brain.py` — harness de pruebas offline del cerebro
- `_oneoffs_applied/` — scripts de mutación de una sola vez YA aplicados a escenarios live (históricos; se conservan por trazabilidad)

### Docs (`docs/`)
`_GHL_SETUP_SPEC_PEDRO.md`, `FIX_DURABLE_RUNBOOK.md`, `F24_FOLLOWUP_TEMPLATES.md`,
`_PESOS_WORKFLOW.md`.

## Qué NO se migró (a propósito — regenerable o histórico)

- `_BLUEPRINTS/*.json` (~70 snapshots de deploy) — archivos de archivo, regenerables por el build. No son source.
- `catalog_links*.json`, `reeng_ledger.json`, `_promo_state.json` — data/estado, regenerable por `build_f24_knowledge.py` / runtime.
- `AUDITS/`, `F24_BOT_SYSTEM_PROMPT_v2_DRAFT.md`, `_README.md` — docs históricos.

## Pendiente (NO hacer sin confirmar con Pedro)

Eliminar/archivar `F24 - 08. WHATSAPP/bot_multimodal/` de Drive. **Antes de borrar:
confirmar con Pedro que no tiene trabajo local sin commitear ahí.** El código vivo va a
`~/dev` (repo), no a Drive (regla SPEKGEN). Ver memoria `project_f24_bot_deploy_source_of_truth`.
