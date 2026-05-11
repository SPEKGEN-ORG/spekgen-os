---
name: FB carousel requires attached_media flow
description: Meta FB Graph API no tiene carousel endpoint directo — se construye con photos?published=false + feed attached_media
type: feedback
originSessionId: 7b482b91-b863-4b7c-9374-a32723feaee3
---
FB carousel = flujo de 2 pasos vía page token:

1. Upload cada imagen unpublished: `POST /{page_id}/photos?published=false&url=...&access_token=...` → devuelve `photo_id`
2. Crear post de feed con todas: `POST /{page_id}/feed` con `message=...&attached_media=[{"media_fbid":"id1"},{"media_fbid":"id2"},...]`

Single image sigue siendo `POST /{page_id}/photos` con `caption` + `url` (published=true por default).

URL permalink: `GET /{post_id}?fields=permalink_url`.

**Why:** Bug vivía en `publish-now` edge function (Supabase) v1-v3: `publishFB` solo mandaba `imageUrls[0]` con `POST /{page_id}/photos` → FB recibía solo slide 1 de carruseles. Comentario del archivo literalmente decía "FB page (first image + caption)" — limitación baked-in nunca arreglada. Gibran eliminaba posts manual y reposteaba carrusel completo 3 días seguidos.

**How to apply:** Para cualquier publisher FB carousel: usar attached_media flow, nunca asumir que `/photos` acepta múltiples imágenes. Validado en `publish-now` v4 deployed 2026-04-22 (project `wjlwpfaogjpeqgyxxnwa`). Autopublisher.py de GH Actions ya usa este patrón en `publish_facebook()` (lines 307-353 de spekgen-ops).

**Diagnóstico rápido si reaparece:** `mcp__supabase__get_edge_function` → leer `publishFB`. Si solo usa `imageUrls[0]` → bug. Si usa `attached_media` → OK.
