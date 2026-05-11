---
name: Meta transient fetch failures on publish-now
description: Meta crawler ocasionalmente falla al fetchear URLs Supabase con code=324/9004 pese a que las imágenes están OK. Retry manual suele funcionar.
type: feedback
originSessionId: 361459d3-d3ac-42b3-863e-bc0304c7fe66
---
Meta (IG + FB) a veces rechaza publicaciones con `code=324` (FB "Missing or invalid image file") y `code=9004` (IG "Only photo or video can be accepted as media type") aunque las URLs estén válidas y los PNG sean correctos (formato, tamaño, content-type).

**Why:** HC-026 (2026-04-23, aprobado por Monse) quedó en `publish_error` con estos códigos. Las URLs Supabase respondían 200 + image/png 1080x1350 1.15MB sin problema. Retry manual vía `publish-now` funcionó a la primera. Causa probable: Cloudflare bot mitigation o glitch transitorio del crawler de Meta al fetchear desde Supabase (`__cf_bm` cookie presente).

**How to apply:**
1. publish-now v5 (2026-04-23) ya hace retry automático con backoff 15s + 45s para códigos transitorios {1, 2, 4, 324, 9004}. 3 intentos totales. Solo debería aparecer `publish_error` si 3 intentos fallan.
2. Si aún así marca error, invocar manualmente: POST `{SB_URL}/functions/v1/publish-now` con bearer `AUTOPUBLISH_SHARED_SECRET` y body `{item_id, rating}`. Script de referencia: `/tmp/retry_hc026.py`.
3. Para agregar más códigos a retry: editar `TRANSIENT_META_CODES` en `publish-now` index.ts.
