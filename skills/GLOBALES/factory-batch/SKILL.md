---
name: factory-batch
description: >
  Skill UNICA para producción de batches de imágenes/contenido (ads, content,
  PDPs, prospects) en SPEKGEN. v3 (2026-05-06): 100% Web UI Gemini (5 cuentas
  PRO Google One — costo $0). Pre-flight pricing OBLIGATORIO contra catálogo
  live + xlsx de referencia. BATCH_LOG bloques A/B/C generados programáticamente.
  Recap PDF whiteboard canónico post-batch. Per-client bucket taxonomy.
  NO maneja audit/upload/monitoring/reporting (eso es /lf-media-buying-cycle).
activation_triggers:
  - "batch de ads"
  - "batch de content"
  - "batch de contenido"
  - "batch de pdps"
  - "nuevo batch"
  - "produce ads"
  - "produce content"
  - "factory batch"
  - "crea batch"
  - "genera batch"
  - "iteracion de ads"
  - "carrusel"
  - "post organico"
  - "pdp images"
---

# factory-batch v3 — Production-only · Web UI Gemini

## Por qué existe

Producción estandarizada de creativos para SPEKGEN. **Esta skill solo cubre PRODUCCIÓN.** Las demás fases (audit / decisiones / upload Meta / monitoring / reporting) viven en `/lf-media-buying-cycle` y skills hermanas por cliente.

## Cambios v3 (vs v2 — 2026-05-06)

| Cambio | Razón |
|---|---|
| ❌ Drop "Hybrid Web UI + API" → ✅ **100% Web UI** | Gibran tiene 5 cuentas Google One PRO — $0 costo, calidad superior validada en BATCH_LF_2026-05-05-v1 (8/8 ads ≥8.0 score) |
| ❌ Drop cost tracker (xlsx) | Sin API = sin costo a trackear |
| ✅ ADD pricing pre-flight obligatorio | Regla `feedback_ads_price_validation_mandatory.md` — NUNCA escribir precio en ad sin validar catálogo |
| ✅ ADD `generate_batch_log.py` script | Genera `BATCH_LOG.md` bloques A/B/C programáticamente — fuente de verdad de prompts/scores/results para learning loop |
| ✅ ADD per-client bucket taxonomy | LF: LUPITA+OFFER / OFFER / LUPITA+AUTH / PSS / WILDCARD. HC/GR/MG: TBD per cliente. Cargado de `_buckets/{CLIENT}.json` |
| ✅ ADD dashboard.html con instrucciones embedded | Para que un team member nuevo (o Gibran después de ausencia) sepa qué hacer click-by-click sin training |
| ✅ Recap PDF canónico (1 sola implementación) | Antes había 2 (`build_recap_pdf.py` + `build_recap_pdf_ads_matrix.py`) — kill el genérico, queda solo ads-matrix style |
| ❌ Drop generate_images.py (API) | Movido a `_archive/`. Si vuelve API, recuperable. |
| ✅ Integración explícita con `/lf-media-buying-cycle` | Recap output sirve de input para workflows de monitoring |

## Cuándo invocar

- "batch de ads para LF" → `--type ads --client LF`
- "batch de content HC" → `--type content --client HC --post-id HC-033`
- "PDP OmegaDog" → `--type pdp --client HC --product OMEGADOG`
- "mockup prospect Yerena" → `--type prospect --name yerena`

**NO usar para:**
- Audit / decisiones / upload Meta → `/lf-media-buying-cycle` (LF) — análoga TBD para otros
- Publicar mockup+propuesta → `/publish-prospect`
- Reporte mensual cliente → `/publish-monthly-report`
- Análisis cross-client → `/cross-client-intel`

## Pre-flight check OBLIGATORIO (antes de redactar prompts)

Cargar EN ORDEN. Sin confirmación literal en chat de los reads, NO avanzar a prompts:

### Para `--type ads` cliente LF (ejemplo canónico):

1. `SPK - 15. FACTORY/_brand_rules/LF.md` — reglas hard NEVER/ALWAYS, paleta, tipografía
2. `SPK - 15. FACTORY/_learnings/LF/ADS/_MASTER.md` — lessons cross-batch
3. `SPK - 15. FACTORY/_prompts/LF/ADS/_MASTER.md` — prompts ganadores agrupados por bucket
4. `SPK - MEDIA BUYING OPS/LOGS/LF/MONTH_PLAN_MAY26.md` — plan vigente, qué bucket toca
5. `SPK - MEDIA BUYING OPS/LOGS/LF/PROMPT_PATTERNS_LF.md` — síntesis prompt patterns winners
6. `SPK - MEDIA BUYING OPS/LOGS/LF/CALIBRATION.md` — números reales del cliente
7. `LF - LO FITNESS/LF - 02. PRODUCTOS/00. PRODUCT LOG GLOBAL/LF_PRICING_REFERENCE.xlsx` — pricing ground truth
8. Live pull: `https://lofitness.club/products.json` — verificar precios contra xlsx (auto via `validate_batch.py --pricing-check`)

### Para otros clientes:
- HC: `_brand_rules/HC.md` + `_learnings/HC/ADS/_MASTER.md` + `_prompts/HC/ADS/_MASTER.md` + dashboard gsheet HC + product log HC
- GR/MG: análogo

Decir literal en chat: *"Leí brand_rules + learnings master + prompts master + month plan + pricing reference. Catálogo live validado: 0 discrepancias. Aquí van los N prompts."*

## Workflow v3 (5 fases — simplificado de 8 v2)

### Fase 1 — Brief
Claude lee pre-flight + propone batch. Gibran aprueba mix (split 50/27/13/10 LF, distinto per cliente).

### Fase 2 — Init batch
```bash
python3 scripts/init_batch.py --type ads --client LF --batch-id BATCH_LF_2026-05-XX-v1
```

Crea `ads/LF/2026-05/BATCH_LF_2026-05-XX-v1/` con:
- `batch.json` skeleton con N entries vacíos
- `dashboard.html` con instrucciones step-by-step embedded para human runner
- `RESOURCES/{ad_code}/` (vacías — pegas ahí los attachments por ad)
- `FINAL/` (vacía)
- `BORRADOR/` (vacía)
- `_DELIVERABLES/` (vacía)

### Fase 3 — Brief + prompts SCALIST

Claude llena `batch.json` con:
- ad_code, format (bucket), product, concept_angle, entity_id_signature
- gemini_prompt completo formato SCALIST (subject + composition + action + location + style + specs + text)
- ad_copy (primary_text, headline, description, cta, landing_url con UTMs)
- attachments path
- expected_outcome

Validar antes de avanzar:
```bash
python3 scripts/validate_batch.py {batch_dir} --pricing-check --client LF
```

Output: ✅ todos los precios cuadran con catálogo live // ❌ discrepancias listadas con propuesta de fix.

### Fase 4 — Generación Web UI

Gibran (o team member) abre `dashboard.html` (server local `:8766`) y por cada ad:
1. Click "COPIAR PROMPT" → pega en gemini.google.com
2. Drag attachments del panel del dashboard
3. Itera (1-N turnos) hasta score ≥8 (rubric: texture/lighting/anatomy/typography/cohesion)
4. Guarda ganadora en `FINAL/{ad_code}.png`
5. Mensaje a Claude: `"LF-066 listo iter 3 score 8.5"` (o solo `"LF-066 listo"` si Gibran no quiere dictar)

Claude appendea Block B a `BATCH_LOG.md` por cada ad terminado.

### Fase 5 — Deliverables + handoff a /lf-media-buying-cycle

```bash
python3 scripts/generate_batch_log.py {batch_dir}     # genera BATCH_LOG.md A/B/C
python3 scripts/build_recap_pdf.py {batch_dir}         # genera whiteboard PDF
```

Output:
- `LOGS/{CLIENT}/BATCH_LOG.md` actualizado con bloques A+B (C se llena post-upload)
- `{batch_dir}/{batch_id}_recap.pdf` — whiteboard cliente × buckets
- `{batch_dir}/_DELIVERABLES/` con copia para sync

Handoff: notificar a Claude operator del cliente (`/lf-media-buying-cycle workflow 05_friday_upload`) que el batch está READY_FOR_UPLOAD.

## Buckets (per cliente)

Cada cliente define sus buckets en `_buckets/{CLIENT}.json`:

```json
{
  "client": "LF",
  "split_pct": {"OFFER": 50, "LUPITA+AUTHORITY": 27, "PROBLEM-SOLUTION": 13, "WILDCARD": 10},
  "buckets": {
    "OFFER":             {"adset_id": "120244794416320731", "color": "#059669"},
    "LUPITA+OFFER":      {"adset_id": "120244794420800731", "color": "#7C3AED", "subset_of": "OFFER"},
    "LUPITA+AUTHORITY":  {"adset_id": "120244794420800731", "color": "#0EA5E9"},
    "PROBLEM-SOLUTION":  {"adset_id": "120244794420430731", "color": "#F59E0B"},
    "WILDCARD":          {"adset_id": "120244794421490731", "color": "#DC2626"}
  }
}
```

Buckets per cliente vivirán en `_buckets/` (a crear cuando se onboardee HC/GR/MG con su propia restructura).

## Schema batch.json (v3 ads — alineado con BATCH_LF_2026-05-05-v1)

```json
{
  "batch_id": "BATCH_LF_2026-05-XX-v1",
  "type": "ads",
  "client": "LF",
  "campaign_destination": {
    "scale_campaign_id": "...",
    "testing_campaign_id": "...",
    "testing_adsets": {"A_KIT_OFFERS": "...", "B_PROBLEM_SOLUTION": "...", "C_LUPITA_AUTHORITY": "...", "D_WILDCARDS": "..."},
    "page_id": "...",
    "instagram_user_id": "...",
    "pixel_id": "..."
  },
  "model_used": "gemini-3-pro-image-preview (Web UI)",
  "created": "YYYY-MM-DD",
  "version": "v1",
  "status": "DRAFT",
  "compliance_check": ["claims_aprovados", "tildes_correctas", "disclaimer_obligatorio"],
  "context": {"estado_cuenta": "...", "hipotesis_validada": "...", "split_creative_mes": "..."},
  "entries": [
    {
      "ad_code": "LF-066_FITMAX_2PACK_OFFER_PURO",
      "client": "LF",
      "destination_adset": "A_KIT_OFFERS (id 120244794416320731)",
      "product": "Fit Max Pack 2 ($1,076.40)",
      "format": "OFFER puro",
      "concept_angle": "...",
      "entity_id_signature": "...",
      "aspect_ratio": "4:5",
      "objective": "...",
      "hook_text_on_image": "...",
      "gemini_prompt": "BLOCK 1 — FORMAT...\n\nBLOCK 2 — SUBJECT...\n...",
      "extra_attachments": ["RESOURCES/LF-066/FitMax_product.png"],
      "ad_copy": {"primary_text":"", "headline":"", "description":"", "cta_type":"SHOP_NOW", "landing_url":""},
      "expected_outcome": "...",
      "winning_variant": null,
      "status": "DRAFT",
      "final_image_path": null,
      "meta_ad_id": null,
      "meta_creative_id": null,
      "meta_image_hash": null,
      "claude_score": null,
      "iter_winner": null,
      "notes": null
    }
  ]
}
```

## Reglas duras (cross-tipo, v3)

1. **Pre-flight reads obligatorios** — sin confirm en chat, no avanza a prompts
2. **Pricing pre-flight obligatorio** — `validate_batch.py --pricing-check` antes de redactar `ad_copy`. NO inventar precios.
3. **Stock check** — productos con `available=False` en catálogo NO se pueden usar (auto-flag en validate_batch)
4. **Español correcto** — tildes, ñ. Verificar Ctrl+F antes de finalizar batch.json
5. **NUNCA símbolos decorativos** en prompts (sparkles, diamonds, stars) salvo brief explícito (origen: HC-032 watermark crisis)
6. **Identity Lock obligatorio** en ads con persona del cliente (Lupita LF, Pepa HC, etc.)
7. **COFEPRIS / brand voice** — verbos "apoya/contribuye/favorece/ayuda a" únicos permitidos para suplementos. Disclaimer obligatorio.
8. **BATCH_LOG bloque A pre-poblado** automático al cerrar Fase 3
9. **BATCH_LOG bloque B** llenado durante/post Fase 4 (iter+score)
10. **Recap PDF** obligatorio post-Fase 5

## Scripts (v3)

```
factory-batch/
├── SKILL.md                        ← este archivo (v3)
├── README.md                       ← TBD
├── CHANGELOG.md                    ← v2→v3 changes
├── _archive/
│   └── generate_images.py          ← API path (no usado, recuperable)
├── _buckets/
│   └── LF.json                     ← bucket taxonomy LF
└── scripts/
    ├── init_batch.py               ← crea folder + batch.json skeleton
    ├── generate_dashboard.py       ← NEW: dashboard.html con instrucciones onboarding embedded para human-runner
    ├── validate_batch.py           ← valida JSON + pricing pre-flight + stock check (--pricing-check)
    ├── generate_batch_log.py       ← NEW: genera BATCH_LOG.md bloques A/B/C
    ├── serve_dashboard.py          ← localhost:8766
    ├── finalize_selection.py       ← mueve descartadas a BORRADOR/
    ├── build_recap_pdf.py          ← whiteboard cliente × buckets (canónico v3 — HTML+Playwright matrix)
    └── sync_deliverables.py        ← copia PDFs a Drive
```

## Modelo + Técnica

- **Web UI**: `gemini.google.com` (5 cuentas Google One PRO)
- **Modelo**: `gemini-3-pro-image-preview` (lo que sirve la UI)
- **Watermark**: Web UI sí mete watermark visible — **Gibran lo quita manualmente** post-download
- **Costo**: $0
- **Iteración**: conversational chain con identity lock prefix; abandonar chain y reiniciar con master image si drift

## Dependencias

- Python 3 stdlib + `requests` + `Pillow` + `playwright` (para PDF) + `openpyxl` (pricing xlsx)
- Web UI Gemini (Chrome + Google One PRO)
- `/lf-media-buying-cycle` — para handoff post-batch

## Histórico

- **2026-04-21** — v1 creado. Workflow centralizado en SPK - 15. FACTORY/.
- **2026-04-28** — v2: storage client-first, pre-flight reads, hybrid Web UI + API, cost tracker, dual PDF, drive sync.
- **2026-05-06** — **v3** refactor:
  - 100% Web UI (drop API path → `_archive/`)
  - Pricing pre-flight obligatorio integrado a validate_batch
  - BATCH_LOG generator NEW (learning loop)
  - Per-client bucket taxonomy (`_buckets/{CLIENT}.json`)
  - Dashboard.html con instrucciones embedded para human-runner
  - Consolidación recap PDF canónico
  - Integración explícita con `/lf-media-buying-cycle`
