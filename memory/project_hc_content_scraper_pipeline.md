---
name: HC Content Scraper pipeline status
description: Pipeline autónomo HC Content Intel (GH Actions daily). Estado 2026-04-11 PM: video teardown vuelve a FULL AUTO (hybrid), Gemini desbloqueado con key nueva, 5 videos queued procesados end-to-end.
type: project
---

**Pipeline:** `scripts/content-scraper/main.py` corre en GH Actions Daily (`HC Content Scraper (Daily)`, cron 13:07 UTC).

**Estado 2026-04-11 PM (post-unblock):**
- 139 raw → 117 after dedupe → 0 errors
- Apify Meta Ads Library: 40 ads (ex-Graph API)
- Google Trends: 14
- Instagram: 40
- TikTok: 40
- Amazon Reviews: ~5
- Reddit: disabled (IP block, ver _TODO_UNBLOCK.md)

**Video Teardown:** modo `hybrid` (full auto). `main_video.py::process_video_hybrid` llama Gemini File API directo con la nueva key (proyecto 250810559337, cuota free tier — separada del HC project con billing pendiente). Queue en `Video_Pending_Review` sigue existiendo como fallback.

**2026-04-11 drain histórico:** los 5 videos que se encolaron cuando estábamos en semi_auto fueron procesados end-to-end:
- gemini-2.5-flash: 5/5 OK (525–1504 chars transcript, 3–14 beats cada uno)
- teardown_structurer + Haiku remix: 4/5 clean (3x ArtriDog, 1x DogRelax); 1 edge case (9cb3439794f49120 @thepuggysmalls Easter post → hc_product_fit quedó como placeholder literal porque el video era demasiado vago para elegir)
- Video_Teardowns filas 2-6 actualizadas in-place con rehydrate_haiku.py
- Video_Pending_Review 5 rows → status=done, processed_by=direct-api-unblocked

**Why hybrid funcionó:** nueva Gemini API key creada en aistudio.google.com/api-keys (proyecto `projects/250810559337`) NO comparte billing con el HC project bloqueado. Curl test `gemini-2.5-flash:generateContent` → 200 OK con la key nueva. Key nueva ya rotada en: HC .env, SPEKGEN .env, GH secret `GEMINI_API_KEY`. Backups en `.env.bak.2026-04-11`.

**How to apply:**
- Si Gibran pregunta cuántos items da el pipeline: ~110-140/día con los 5 scrapers activos
- Si pregunta por video teardown: corre full auto hybrid, no requiere drain manual
- Si detectas rows en `Video_Pending_Review` con status=queued: hubo un failover temporal, correr `/hc-video-process-pending` O verificar si Gemini key volvió a fallar
- Si Gemini vuelve a 403: flip `configs/hc.json::video_teardown.mode` → `"semi_auto"` como fallback, drain via skill, reportar

**Files clave:**
- `main.py` source_map → `scrape_meta_ads_library` (Apify)
- `main_video.py::process_video_hybrid` → Gemini API directo (path activo)
- `main_video.py::process_video_semi_auto` → fallback queue (disponible pero no activo)
- `video/gemini_analyzer.py::analyze_video` → File API upload + generate_content
- `video/teardown_structurer.py::structure` → Haiku remix (needs `ANTHROPIC_API_KEY`)
- `sheets_writer.py::write_teardowns` → append a Video_Teardowns
- Skill: `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/PERSONALIZADAS/hc-video-process-pending/SKILL.md` (standby, solo si fallback semi_auto)
- Workflow: `.github/workflows/hc-content-scraper.yml`

**Commit del flip:** `cdb29c8 hc.json: flip video_teardown mode semi_auto → hybrid` en Spekgen-ops main.
