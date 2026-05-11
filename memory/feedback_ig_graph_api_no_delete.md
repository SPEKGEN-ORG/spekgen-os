---
name: Instagram Graph API no permite DELETE de media publicada
description: DELETE /{ig-media-id} siempre falla con error code=1 "unknown error". Borrados de posts IG deben ser manuales; FB sí permite DELETE via API
type: feedback
originSessionId: 31f81eb4-139b-4296-ad4b-fd862b64e010
---
La Instagram Graph API **NO permite borrar posts publicados** via `DELETE /{ig-media-id}`. Siempre retorna `{"error":{"code":1,"message":"(#1) An unknown error occurred"}}` — limitación documentada, solo permite borrar comments, no media.

**Why:** Intenté borrar 4 IG duplicates de MetaGreen (incidente MG-008 publicado 5x el 2026-04-23) con `curl -X DELETE https://graph.facebook.com/v21.0/{id}?access_token=...` — los 4 fallaron con el mismo error. Los 4 FB duplicates SÍ se borraron con page token (`"success":true`).

**How to apply:**
- Cleanup de IG duplicates = **manual** desde la app Instagram o Business Suite. No intentar via API.
- FB duplicates sí se pueden borrar via API con Page Access Token (obtener con `GET /{page_id}?fields=access_token` usando user token).
- Para prevenir duplicados → idempotencia en el publisher (ver `feedback_autopublisher_dedup_guardrail.md`).
