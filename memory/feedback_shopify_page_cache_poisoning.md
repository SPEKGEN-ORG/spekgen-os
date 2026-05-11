---
name: Shopify page cache puede quedar poisoned permanentemente
description: Si un URL /pages/* se cachea mal, nunca se invalida. Delete+recreate no ayuda. Crear URL nuevo.
type: feedback
---

Cuando un URL `/pages/{handle}` de Shopify cachea mal su output, el cache puede quedar poisoned de forma PERMANENTE. Síntoma: la página responde HTTP 200 con contenido viejo incluso cuando el page_id original fue eliminado y recreado con ID nuevo (el resourceId en el HTML sigue siendo el del page deleted).

**Why:** Shopify tiene un page_cache app-level (no CDN) que parece estar keyed por handle + shop + algo. 2026-04-10: `/pages/portal-hc` quedó stuck mostrando TEST-001 incluso después de: (1) borrar y recrear el page 3 veces, (2) cambiar template_suffix a uno nuevo, (3) re-subir el theme con timestamps de cache-bust, (4) agregar query params únicos. El etag cambiaba pero el contenido era idéntico. cf-cache-status: DYNAMIC (no era Cloudflare). El fix único: usar un handle COMPLETAMENTE diferente. **Peor aún: un handle fresh también puede poisonearse después de una 2a migración.** `hc-hub` funcionó al crear, luego de re-migrar metaobjects (delete+recreate) empezó a servir content cacheado mezclado (counts oscilaban 9/0/7/12 ↔ 2/1/4/21). Tuvo que abandonarse y crear `hc-live` fresh. Lección: handles son quemables — cada delete+recreate de metaobjects puede poisonar el handle que los lista.

**How to apply:**
- Si detectas cache poisoning (misma HTML devuelta ignorando cambios, o counts oscilando), no pelees con el cache — crea un handle nuevo.
- Durante el setup inicial de un nuevo Shopify portal, usa handles quemables (`{client}-live`, `{client}-hub`, `{client}-v2`, etc.) y nunca el handle "obvio" en primer intento.
- Evita correr migraciones destructivas (delete all + recreate) sobre metaobjects que un handle ya está renderizando. Si hay que hacerlo, asume que el handle se quemará y prepara un handle nuevo simultáneamente.
- El template mapea múltiples handles al mismo client_slug en el `{% case %}` block — es fácil soportar legacy + nuevo handle simultáneamente.
- Si ya está en producción y hay que cambiar URL, documentar redirect via Shopify admin o via Liquid redirect en template.
