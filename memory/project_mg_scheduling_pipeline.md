---
name: MG Scheduling Pipeline (hub reutilizado)
description: MG publica a IG+FB reutilizando autopublisher GH Actions HC, sin portal. Upload via upload_mg_batch_to_hub.py desde batch.json.
type: project
originSessionId: a5708d43-16a4-4f49-b963-5845e965c731
---
MG no tiene portal Shopify propio (a diferencia de HC `/pages/hc-vault`). Para scheduling de orgánicos se reutiliza la infraestructura HC sin construir portal dedicado.

**Pipeline (activado 2026-04-22):**

1. Batch factory con `status: ready` + `final_images: [...]` en `batch.json`.
2. `python3 SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/upload_mg_batch_to_hub.py "<batch_dir>" --only "MG-XXX" --status approved` — sube a Supabase `post-media/mg/{POST_ID}/` y upsertea metaobject `content_item` con `client="mg"`.
3. `Spekgen-ops/.github/workflows/content-hub-autopublisher.yml` (cron `7 * * * *`) publica IG+FB en `date_planned`+`time_planned` MX_TZ.

**Status=approved directo** (no hay review UI para MG — Gibran aprueba offline en el batch).

**MG Meta IDs** ya hardcoded en `autopublisher.py:49`: IG `17841462109913746`, FB `132180209979937`.

**Why:** Opción C evaluada vs A (portal MG nuevo = mucho trabajo) y B (Meta API `scheduled_publish_time` solo funciona en FB, no IG). Autopublisher cloud = Japan-proof.

**How to apply:** para futuros batches MG, ejecutar `upload_mg_batch_to_hub.py`. Caption se ensambla automáticamente como `caption + \n\n + hashtags`. Default status=approved.
