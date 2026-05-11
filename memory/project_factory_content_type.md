---
name: Factory extendido a tipo=content
description: Factory `/factory-batch --type content` ahora funcional. Schema + dashboard + validador + strategy cheat-sheet. MG-006→012 es el piloto content.
type: project
originSessionId: 7c9dda25-0096-4ccb-b43a-0f27ae42bfd5
---
El factory unificado (`SPK - SPEKGEN AGENCY/SPK - 15. FACTORY/`) ahora soporta tipo `content` además de `ads`. Primera corrida: BATCH_MG_2026-04-22-v1 (7 posts MG-006→012, cadencia S-C-C-S-C-C-S).

**Archivos clave creados 2026-04-22:**
- `_templates/content_batch.schema.json` — JSON Schema draft-07 para array de posts. Required: post_id, client, pillar, format (carrusel|estatico), funnel (TOFU|MOFU|BOFU), title, concept_style, publish_date, publish_time, hook, slides[{num,role,text,prompt}], caption >=80 words, cta_keyword, cta_line, hashtags, naming_convention, attachments, expected_outcome.
- `_templates/content_entry.json` — skeleton reusable.
- `_templates/dashboard_content.html` — dark-purple adaptado. Fetcha `batch.json`. Renderea multi-slide prompts con COPIAR button por slide + por caption. Filtros: format/funnel/pillar/client. Naming badge, CTA line destacado, hashtags en monospace.
- `_strategy/STRATEGY_MG.md` — cheat sheet MG (paleta, Inter font, CTAs MAQUILA/ESCALA/PROCESO/FORMATOS/DROPSHIPPING, 5 pilares, ICP A1-A4, voz, reglas confidencialidad B2B, naming convention, WCI tiers).

**Scripts modificados:**
- `init_batch.py` — ahora selecciona template por `--type` via `template_map` (ads→dashboard_base.html, content→dashboard_content.html).
- `validate_batch.py` — detecta tipo automáticamente por shape del primer entry (`ad_code` → ADS, `post_id` → CONTENT). Validación content: post_id pattern `^(MG|HC|GR|LF|GIBRAN)-[0-9]{3}[A-Z]?$`, format counts (estatico=1 slide, carrusel>=2), prompt length >=50, caption >=80 words, attachments path exist, FINAL/ dir exist.

**Workflow tipo content (igual que ads):**
1. `init_batch.py --type content --client MG --date 2026-04-22`
2. Claude escribe `batch.json` con N posts (cada slide tiene su `prompt` completo con ABSOLUTE TEXT RULE).
3. Copy RESOURCES a `RESOURCES/{post_id}/` + crear `FINAL/` subdir.
4. `validate_batch.py` para check.
5. `serve_dashboard.py` en localhost:8765.
6. Para cada post: click COPIAR slide → Gemini 2.5 Pro web UI → adjuntar refs → descargar → `RESOURCES/{post_id}/FINAL/`.
7. (Deferred) Upload a Content Hub Shopify del cliente via `_CONTENT_HUB_SHOPIFY/upload_post_to_hub.py`.

**Reusable para:** próximos batches HC/LF/GIBRAN content (mismo schema, mismo dashboard, solo cambian _strategy y RESOURCES). Strategy docs: `_strategy/STRATEGY_HC.md` y `STRATEGY_LF.md` existen (ads) pero no tienen sección content específica aún — crear cuando toque.
