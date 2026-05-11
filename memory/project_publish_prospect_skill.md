---
name: /publish-prospect skill — publica mockup+propuesta a spekgen.com
description: Skill reusable para publicar cualquier prospecto a spekgen.com con URLs limpias. 2-4 prospectos/día esperados
type: project
originSessionId: 4223a5d4-0334-4c10-9b95-244e4feb260f
---
**Qué hace:** Toma el mockup HTML + propuesta HTML de un prospecto y los publica en `spekgen.com/{slug}mockup` y `spekgen.com/{slug}propuesta`. Sube imágenes al CDN de Shopify, oculta el chrome del tema Horizon, versiona por hash de contenido para bypass del page_cache poisoning.

**Ruta:**
- Skill: `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/publish-prospect/SKILL.md`
- Script: `SPK - SPEKGEN AGENCY/PROSPECTOS/_publish_prospect.py`
- Depende de: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/shopify_client.py` + `.env`

**Uso:**
```bash
cd "SPK - SPEKGEN AGENCY/PROSPECTOS"
python3 _publish_prospect.py \
    --slug enlace \
    --prospect-dir "ENLACE TELECOMUNICACIONES - LA PAZ" \
    --propuesta "propuesta/PROPUESTA_ENLACE.html" \
    --brand "Enlace Telecomunicaciones"
```

**Arquitectura clave (ver feedback memories):**
1. `feedback_shopify_page_cache_poisoning.md` → handle versionado por sha256[:6] + redirect a URL limpia
2. `feedback_horizon_grid_collision.md` → rename `.grid` → `.spk-grid` en HTML antes de publicar
3. Caché local `.spekgen_publish_cache.json` (sha256[:16] del archivo) para no re-subir imágenes

**First use:** Enlace Telecomunicaciones (2026-04-18). LIVE:
- https://spekgen.com/enlacemockup
- https://spekgen.com/enlacepropuesta

**Video support (2026-05-06):** `MIME_MAP` extendido con `mp4/webm/mov`. Mockups ahora pueden llevar `<video src="videos/reel_NN.mp4">` y el script los sube a Shopify CDN como `FILE` con content-type correcto. Pipeline para FB/IG reels: `yt-dlp` (instalar via `brew install yt-dlp`) + `ffmpeg -c:v libx264 -crf 28 -preset veryfast -movflags +faststart` para optimizar peso. Primer uso: B&B Cabo (`spekgen.com/bbwellnessmockup` con 5 reels).

**How to apply:** Cuando Gibran diga "publica X a spekgen" o "súbele el link a spekgen" para un prospecto, correr el script. Gibran procesa 2-4 prospectos/día = no hacer a mano.

**Expected cadence:** 10-20 deploys/semana. El skill ahorra ~30 min/prospecto vs hacerlo manual.
