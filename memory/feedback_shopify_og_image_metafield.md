# Shopify OG Image via Page Metafield (theme.liquid patch)

**Origen**: 2026-04-28 — Mariscos Los Laureles WhatsApp preview no mostraba logo.
**Status**: implementado y working. Aplica a TODA page futura en spekgen.com.

## El problema

Las pages de Shopify no tienen propiedad nativa de "featured image". El theme Horizon (`snippets/meta-tags.liquid`) usa `page_image` (Liquid global) que es **null para pages estándar**, solo se popula para products/articles.

Resultado: WhatsApp/FB/Twitter previews quedan SIN imagen. Solo og:title + og:description (que Shopify auto-genera).

## La solución (one-time setup, ya hecho)

### 1. Patch del theme `snippets/meta-tags.liquid`

Agregada cláusula `elsif` para fallback en pages:

```liquid
{%- if page_image -%}
  ...og:image normal...
{%- elsif request.page_type == 'page' and page.metafields.seo.image_url -%}
  <meta property="og:image" content="{{ page.metafields.seo.image_url }}">
  <meta property="og:image:secure_url" content="{{ page.metafields.seo.image_url }}">
  <meta name="twitter:image" content="{{ page.metafields.seo.image_url }}">
{%- endif -%}
```

### 2. Metafield definition registrada (one-time)

Via GraphQL `metafieldDefinitionCreate`:
- Owner type: `PAGE`
- Namespace: `seo`
- Key: `image_url`
- Type: `single_line_text_field`
- Display name: "SEO Image URL"

ID: `gid://shopify/MetafieldDefinition/191296569601`

Sin esta definition, el theme NO reconoce `page.metafields.seo.image_url` aunque exista el metafield.

### 3. Auto-set en `_publish_prospect.py`

Después de upsert de page, el script:
1. Busca `logo.*` en `.spekgen_publish_cache.json` (CDN URL)
2. Llama `set_page_og_image(sc, page_id, logo_cdn_url)`
3. Función verifica si metafield existe; si no, lo crea; si valor diferente, lo actualiza

Aplica automáticamente a TODOS los prospectos que tengan `assets/logo.{jpg,png,webp,...}` en su carpeta. Sin trabajo manual.

## Verificación post-publish

```bash
curl -sL "https://spekgen.com/{slug}mockup" | grep -i "og:image"
```

Debería mostrar:
```
property="og:image"
content="https://cdn.shopify.com/.../logo.jpg?v=..."
```

## WhatsApp preview cache

Si link ya fue compartido sin og:image, WhatsApp cachea la versión vieja por 24-48h. Para forzar refresh:

1. **Facebook debugger** (recomendado): https://developers.facebook.com/tools/debug/?q={URL} → "Scrape Again"
2. **URL nuevo**: agregar `?v=2` al link → WhatsApp lo trata como nuevo
3. **Esperar**: cache expira solo en 24-48h

## Trigger para leer este file

Cualquier task que mencione:
- "el preview de WhatsApp/Facebook/Twitter no muestra imagen"
- "og:image no aparece"
- "social preview" en context de Shopify
- Tema Horizon + meta tags
- Cuando se editen prospectos en `PROSPECTOS/mockup_factory/generated/`
