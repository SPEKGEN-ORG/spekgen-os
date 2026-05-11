---
name: Shopify metaobjectCreate default status es DRAFT — Liquid solo expone ACTIVE
description: Pitfall crítico. Tras crear un metaobject vía GraphQL metaobjectCreate, su capabilities.publishable.status queda en DRAFT. shop.metaobjects.TYPE.values en Liquid NO expone DRAFT — solo ACTIVE. El portal muestra lista vacía aunque el metaobject exista. Fix: siempre aplicar metaobjectUpdate con status ACTIVE tras crear.
type: feedback
originSessionId: cc9a53ea-14de-469a-9ef4-f9341518672d
---
**Pitfall.** Cuando creas un metaobject vía GraphQL mutation `metaobjectCreate`, Shopify lo marca con `capabilities.publishable.status: DRAFT` por default. Esto significa que en Liquid del storefront, `shop.metaobjects.TYPE.values` **NO lo incluye** — solo devuelve los que están `ACTIVE`.

**Síntoma.** Portal cliente muestra una tab vacía ("Aún no hay X publicados") aunque el metaobject acaba de crearse exitosamente. El `GET /metaobjects` directo via API sí lo muestra, pero el Liquid no. Da la falsa impresión de que el template está roto.

**Fix canónico.** Siempre que crees un metaobject que deba ser visible en storefront, aplicar inmediatamente después:

```graphql
mutation ($id: ID!, $metaobject: MetaobjectUpdateInput!) {
  metaobjectUpdate(id: $id, metaobject: $metaobject) {
    metaobject { id handle capabilities { publishable { status } } }
    userErrors { field message code }
  }
}
```

Con variables:
```json
{
  "id": "gid://shopify/Metaobject/...",
  "metaobject": { "capabilities": { "publishable": { "status": "ACTIVE" } } }
}
```

**Mejor aún:** hacerlo en la misma mutation `metaobjectCreate` pasando `capabilities` desde el inicio. Si tu MetaobjectInput schema no lo acepta en create, hacerlo en 2 pasos (create + update).

**Aplica a todos los metaobject types:** `content_item`, `client_document`, `contracted_service`, `content_comment` (Content Hub HC y futuros portales LF/GR/MG/Gibran Ecom).

**Costo de descubrimiento:** 1 sesión de diagnóstico + 20+ segundos de cache CDN esperando a ver si era timing issue. Detectado 2026-04-20 en sesión Content Hub hc-vault refactor cuando tab "Mis reportes" aparecía vacía aunque `client_document` existía con los 7 fields correctos.

**Cache nota:** tras cambiar DRAFT→ACTIVE, Shopify CDN tarda ~15-20s en reflejar en HTML servido. Cache-bust querystring y `Cache-Control: no-cache` header NO invalidan (es app-level caching). Esperar y recurl.

**Regla permanente:** Integrar patrón `create + publish ACTIVE` en todo script que crea metaobjects desde ahora:
- `upload_post_to_hub.py` (content_item) — verificar si ya lo hace
- Futuro `/publish-monthly-report` cuando Gibran termine de ajustar (client_document) — integrar
- Cualquier script de bulk seed de contracted_service por cliente nuevo
