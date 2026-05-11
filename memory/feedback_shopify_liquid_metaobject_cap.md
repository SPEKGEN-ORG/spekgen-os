---
name: Shopify Liquid metaobject 50-item cap is hard
description: shop.metaobjects.TYPE.values esta capped a 50 en Liquid Y el lookup [handle] devuelve ghosts. Solucion = Storefront API client-side
type: feedback
originSessionId: 0535f9eb-4082-48ed-af73-5d4381dd49ac
---
`shop.metaobjects.TYPE.values` en Liquid devuelve maximo 50 metaobjects (los 50 mas viejos por createdAt). No hay parametros para paginar ni filtrar.

**Trampa critica:** `shop.metaobjects.TYPE[handle]` (lookup por handle) tambien esta capped — solo funciona para handles que ya estan en `.values`. Para handles fuera del cap, devuelve un MetaobjectDrop fantasma que `!= blank` evalua a `true` pero apunta al ULTIMO metaobject valido cargado. Esto causa duplicacion silenciosa: el mismo item se rinde N veces como si fueran distintos.

**Workaround del metafield (NO funciona):** guardar todos los handles en un page metafield y hacer `shop.metaobjects.TYPE[handle_from_metafield]` falla por la misma razon. Esto fue el bug del Content Hub: HC-022 aparecia 8 veces porque era el ultimo lookup valido cuando los handles fuera del cap fallaban a ghost.

**Why:** Aprendido a mas no poder durante el rebuild del Content Hub el 2026-05-01. Sesion completa de debugging porque el "fix" del metafield workaround creaba MAS bugs que el problema original.

**How to apply:** Si necesitas listar mas de 50 metaobjects en una page de Shopify, NO uses Liquid loops. Usa **Storefront API client-side**:
1. Habilita `storefront: PUBLIC_READ` en el metaobject definition
2. Crea un Storefront access token via Admin REST `POST /storefront_access_tokens.json` (es publico, expone-able en JS)
3. Liquid template = solo shell HTML con placeholders `<div data-grid-status="X"></div>`
4. JS al final del template hace `fetch('/api/2025-01/graphql.json', { headers: { 'X-Shopify-Storefront-Access-Token': TOKEN }, body: { query: 'metaobjects(type, first:100, after) { ... }' }})` — paginado, sin cap
5. Renderea cards client-side y popula los placeholders

Esto es lo que se hizo para el Content Hub: hc-stage, gr-stage, mg-stage en `yca1z0-wf.myshopify.com` corren v19/v4/v4 con este patron. Storefront token guardado en `_CONTENT_HUB_SHOPIFY/.env` como `STOREFRONT_TOKEN`.
