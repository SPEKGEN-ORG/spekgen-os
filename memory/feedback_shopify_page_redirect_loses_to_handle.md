---
name: Shopify page route gana contra redirect table — redirect no dispara si la page existe
description: Si existe una Page con el handle X y también un UrlRedirect /pages/X → /pages/Y, Shopify sirve la page (redirect NO dispara). Redirect table solo aplica a URLs sin handle match. Workaround para mantener dos URLs sirviendo el mismo contenido: apuntar ambas pages al mismo template_suffix.
type: feedback
originSessionId: cc9a53ea-14de-469a-9ef4-f9341518672d
---
**Pitfall.** Creaste una Page con handle `hc-stage`, luego decidiste mover todo a `hc-vault` y creaste un `UrlRedirect` con `path: /pages/hc-stage` y `target: /pages/hc-vault`. **El redirect NO dispara mientras la page `hc-stage` siga existiendo.** Shopify prioriza page route match por encima del redirect table. El request a `/pages/hc-stage` sirve la page directamente sin consultar redirects.

**Síntomas.**
- Entras a `/pages/hc-stage` esperando redirect → ves la page vieja con contenido stale
- El redirect aparece creado correctamente en Shopify Admin (UrlRedirectCreate devuelve id válido)
- `curl -I /pages/hc-stage` → 200 OK (no 301/302)

**Orden real de resolución de Shopify para URLs `/pages/...`:**
1. Page match por handle → si existe, sirve con su template_suffix
2. Si no hay page match → consulta UrlRedirect table
3. Si no hay redirect → 404

**Workarounds válidos.**

**Opción A — Hard-delete de la page vieja.** `pageDelete` de `hc-stage`, entonces el redirect sí toma efecto y `/pages/hc-stage → /pages/hc-vault`. Riesgo: si hay bookmarks/emails históricos apuntando a `hc-stage` con otros recursos (anchors, parameters), se rompen durante la ventana entre delete y propagación DNS/CDN.

**Opción B — Ambas pages al mismo `templateSuffix`.** Dejas `hc-stage` y `hc-vault` existiendo, pero haces `pageUpdate` para que ambas apunten al mismo template_suffix (ej. `hc-v13`). Resultado: las dos URLs renderean contenido idéntico. El user no nota diferencia y ambos bookmarks funcionan. Este es el patrón que usamos en el Content Hub HC (sesión 41, 2026-04-20).

**Opción C — Elimina el handle conflict.** Rename de la page vieja a un handle que no conflicte (ej. `hc-stage-archived`), luego el redirect `/pages/hc-stage → /pages/hc-vault` sí dispara. Medio-intrusivo porque cambia el handle visible en Admin.

**Recomendación.** Opción B durante transición, Opción A como cleanup final cuando confirmas que nadie usa la URL vieja.

**Regla permanente.** Cuando uses `urlRedirectCreate` para mover tráfico entre pages, SIEMPRE verificar que la page `path` origen ya NO exista. Checar con:

```graphql
{ pages(first: 20, query: "handle:hc-stage") { nodes { id handle templateSuffix } } }
```

Si devuelve nodo, el redirect no va a disparar — tomar Opción A/B/C.

**Costo de descubrimiento:** 10 min confusión en sesión Content Hub hc-vault refactor (2026-04-20) cuando el redirect no disparaba. Resuelto apuntando ambas pages al mismo template_suffix.
