---
name: Autopublisher metaobject update keys + dedup guards
description: autopublisher.py debe usar keys ig_post_url/fb_post_url (no ig_permalink/fb_post_id) y forzar publish_error si update falla — sino loop infinito de re-publicación
type: feedback
originSessionId: d2c4c31d-c80a-48f2-9ee3-aedaaa8ffdcd
---
El script `scripts/content-hub-autopublisher/autopublisher.py` (g-bran/Spekgen-ops) hace `metaobjectUpdate` después de publicar a IG+FB. **Los keys del update DEBEN coincidir con la definición del metaobject `content_item`**:

- ✅ `ig_post_url` (NO `ig_permalink`)
- ✅ `fb_post_url` con URL completa `https://www.facebook.com/{post_id}` (NO `fb_post_id` con solo el ID)
- ✅ `date_published` en ISO datetime `YYYY-MM-DDTHH:MM:SS+00:00` (NO `%Y-%m-%d` date-only)

Si los keys son inválidos, Shopify regresa `userErrors` y `update_metaobject` lanza `RuntimeError`. **Si el except solo loguea warning y deja `status=approved`, el cron lo agarra en 1h y re-publica.** Esto es el bug que causó incidente MG-013 (2026-05-02): 16 publicaciones duplicadas FB+IG en 24h del mismo post.

**Why:** Incidente 2026-05-02 — MG-013 ("En México, el 80% de las marcas DTC...") publicado 16 veces. Root cause: keys equivocados → update fallaba silenciosamente → status quedaba approved → cron re-publicaba cada hora a :07 UTC. Cleanup: 15 FB borrados via Graph API DELETE; 16 IG borrados manuales (Graph API no permite DELETE de IG media). Fix permanente en commit `596d765` (Spekgen-ops).

Incidente previo similar: MG-008 (2026-04-23) publicado 5x — atribuido en su momento a "re-upload reseteando status" pero la causa raíz real era la misma: update con keys inválidos. La memoria anterior creía que el real autopublisher era la Supabase Edge Function (que sí tenía triple-guard implementado), pero el real es este script Python en GH Actions (que NO tenía guard).

**How to apply:**
1. Cuando edites el update path de `autopublisher.py`, verifica los keys contra el dump real del metaobject (`metaobjects(type:"content_item") { fields { key value } }`). NO inventar.
2. SIEMPRE agregar fallback: si `update_metaobject` falla → `update_metaobject(id, {"status": "publish_error"})` para sacarlo del filtro `status==approved`. Sin fallback el cron entra en loop.
3. Filter en `filter_ready_posts` debe tener defense-in-depth: skip si `ig_post_url` o `fb_post_url` o `date_published` no vacíos, aunque siga en `approved`. El campo autoritativo de "ya publicado" es la URL, no el status.
4. La Edge Function `_CONTENT_HUB_SHOPIFY/edge-functions/auto-publish/index.ts` NO está activa — no la confundas con el autopublisher real.
