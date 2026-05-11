---
name: Ads Factory architecture
description: Pipeline L1-L7 para generar/lanzar/matar ads autónomos pre-Japón. BATCH_2026-04-21 primer piloto semi-auto (13 ads)
type: project
originSessionId: 0ef324ba-aded-46a9-b591-7e34cbd4db1e
---
Ads Factory: pipeline de 7 capas en `SPK - SPEKGEN AGENCY/SPK - 00. COMMAND CENTER/03. HERRAMIENTAS/_ads_factory/`

**Why:** Gibran vuela a Japón ~30 abril 2026 sin WiFi 21 días. Los 3 clientes ads (GR/HC/LF) necesitan creative fresco autónomo. Manual = se rompe en Japón.

**How to apply:**
- Big picture completo en `_BIG_PICTURE_ADS_FACTORY.md`. Leer ese doc antes de tocar el pipeline.
- Piloto manual arrancó 2026-04-21 con `BATCH_2026-04-21/ads_batch.json` (13 ads: 5 HC, 4 LF, 4 GR) + `ads_batch.html` viewer con copy buttons.
- Roadmap: P0 piloto hoy → P1 Gemini API (22-24 abr) → P2 batch upload (24-26 abr) → P3 trigger layer (26-28 abr) → P4 kill loop (28-30 abr).
- Registry source-of-truth: `ads_registry.jsonl` (append-only, 1 línea/ad, status, cost, last_pull metrics).
- Modo dry-run obligatorio durante semana 1 de Japón (ads se crean en PAUSED, Gibran aprueba via email).
- Kill switch: `ADS_FACTORY_AUTO_LAUNCH=false` fuerza PAUSED.
- Costos mensuales estimados: ~$215 MXN (Gemini + Haiku).
- MG queda fuera del scope (B2B GHL, no Meta Ads).
