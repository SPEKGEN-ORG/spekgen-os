# /factory-batch CHANGELOG

## v3 — 2026-05-06

### Breaking changes
- **100% Web UI Gemini.** API path archivado en `_archive/generate_images.py.v2`. Razón: 5 cuentas Google One PRO de Gibran = $0 costo, calidad superior validada en BATCH_LF_2026-05-05-v1 (8/8 ads ≥8.0 score).
- **Drop cost tracker.** Sin API = sin costo a trackear. `SPEKGEN_GEMINI_COST_TRACKER.xlsx` queda como log histórico, no se actualiza más.
- **Bucket taxonomy renombrada.** Antes: `OFFER` / `TESTIMONIO` / `MULTIPRODUCT_STACK` / `UGC_PERSONA` etc. Ahora: per-client en `_buckets/{CLIENT}.json`. LF estrena: `OFFER` / `LUPITA+OFFER` / `LUPITA+AUTHORITY` / `PROBLEM-SOLUTION` / `WILDCARD`.
- **Recap PDF consolidado.** `build_recap_pdf_ads_matrix.py` eliminado (era duplicado del genérico). Queda solo `build_recap_pdf.py` refactoreado para nuevos buckets.

### Added
- **Pricing pre-flight obligatorio** integrado a `validate_batch.py --pricing-check`. Pull live de `{shop_url}/products.json` + comparación contra `{client}_PRICING_REFERENCE.xlsx`. Bloquea si discrepancias o stock=False.
- **`generate_batch_log.py`** NUEVO. Programáticamente genera `LOGS/{CLIENT}/BATCH_LOG.md` bloques A (pre-producción), B (producción/scoring), C (post-launch) por ad. Source of truth para learning loop cross-batch.
- **`_buckets/{CLIENT}.json`** NUEVO. Per-client bucket taxonomy + adset/campaign IDs + pricing mechanic + calibración. Único punto de configuración por cliente.
- **`_archive/`** carpeta nueva para v2 deprecado.
- **Dashboard.html con instrucciones step-by-step** embedded en `init_batch.py`. Onboarding zero-knowledge para team member o Claude futuro.
- **Integración explícita con `/lf-media-buying-cycle`** — handoff post-Fase 5.

### Changed
- Workflow simplificado de **8 fases v2 → 5 fases v3**:
  1. Brief (concept + bucket assignment)
  2. Init batch (folder + skeleton)
  3. Brief + prompts SCALIST + pricing validation
  4. Generación Web UI (human runner)
  5. Deliverables (BATCH_LOG + recap PDF + handoff)
- Pre-flight reads enriquecidos: ahora incluye `MONTH_PLAN_MAY26.md` + `PROMPT_PATTERNS_LF.md` + `CALIBRATION.md` + `LF_PRICING_REFERENCE.xlsx`.

### Removed
- `scripts/generate_images.py` → `_archive/generate_images.py.v2`
- `scripts/build_recap_pdf_ads_matrix.py` → eliminado (consolidado)
- Cost tracker auto-hookup en cualquier script
- "Hybrid Web UI + API" workflow language en SKILL.md

### Migration notes
- Batches v2 existentes (HC-032, HC-033, BATCH_CROSS_2026-04-21-v4, etc.) NO necesitan migración — son históricos.
- Próximo batch (BATCH_LF_2026-05-XX-v1 week 2) usa v3 desde inicio.
- Si HC/GR/MG no han creado su `_buckets/{CLIENT}.json`, próximo batch para ellos se bloqueará en validate_batch hasta que se cree (forzar setup).

## v2 — 2026-04-28
Storage client-first, pre-flight reads, hybrid Web UI + API, cost tracker, dual PDF, drive sync.

## v1 — 2026-04-21
Workflow centralizado en `SPK - 15. FACTORY/`.
