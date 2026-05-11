---
name: GR Analytics Monitor
description: GR Analytics Monitor (GA4+Clarity) via GitHub Actions. Days impares 9:07 AM MX. Setup 2026-04-14
type: project
originSessionId: 3ceb1165-acd2-4d03-a25b-a17a39c21373
---
# GR Analytics Monitor — Cloud (GitHub Actions)

**Setup:** 2026-04-14 (replicado de HC)
**Workflow:** `g-bran/Spekgen-ops/.github/workflows/gr-analytics-monitor.yml`
**Script:** `scripts/hc-analytics-monitor/analytics_monitor.py` (env-driven, reusado — no es HC-specific)
**Cron:** `7 15 1-31/2 * *` — días impares 9:07 AM MX (intercala con GR Meta Monitor en días pares 9:17 AM)

## IDs
- GA4 Property: `470503075`
- Clarity Project: `3223270816013972`
- Sheet destino: mismo que GR Meta Monitor (secret `GR_SHEET_ID`)
- SA: `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` (Viewer GA4 + Editor Sheet)

## Secrets en g-bran/Spekgen-ops
- `GR_GA4_PROPERTY_ID`, `GR_GA4_PRODUCT_SLUGS`
- `GR_CLARITY_PROJECT_ID`, `GR_CLARITY_API_KEY`
- `GR_SHOPIFY_ACCESS_TOKEN`, `GR_SHOPIFY_SHOP` (agregado 2026-04-14 — modo access token directo, shpat_...)
- (existentes reusados) `GR_SHEET_ID`, `GR_SA_JSON_B64`, `GR_ALERT_EMAIL`, `MAKE_WEBHOOK_URL`

## Product slugs trackeados
`artrix, creatine-muscle-complex, colageno-protein-nutrition, hidro-nex-cell, kit-intra-b`

## First run (2026-04-14)
- GA4: 253 sesiones · 19 ATC · 2 compras · $2,645 MXN · conv 0.79%
- Clarity 7d fallback groupBy=url: 0 sesiones (known issue; 1d test: 13 sesiones — API key OK)
- Shopify: 2 órdenes · $2,573 MXN · AOV $1,286 · código `GREENGRATIS` × 1 · 100% nuevos
- 10 tabs creados en sheet: GA4_Overview/History/Pages/Sources, Clarity_Overview/History/Pages, Shopify_Overview/History/Products

## Why
GR necesita monitoreo autónomo pre-Japón (30 abril) igual que HC. Intercala con Meta Monitor para tener actualizaciones diarias del sheet.

## How to apply
Si el workflow falla: check GH Actions logs. 403 GA4 → verificar SA Viewer. 401 Clarity → regenerar token en clarity.microsoft.com/projects.
