# Shopify Horizon: OG/SEO meta tags se emiten desde `snippets/meta-tags.liquid`

**Source:** sesión 2026-05-07 (OG metadata para spekgen.com).

## Lo que pasó

Inyecté un bloque de `<meta property="og:image" ...>` en `layout/theme.liquid`, justo antes de `{{ content_for_header }}`. El HTML servido en el storefront tenía mi bloque visible (en línea ~1419), pero **WhatsApp/FB seguían usando los OG tags viejos**.

## Por qué no ganaba

`layout/theme.liquid` línea 28 ya tiene:

```liquid
{%- render 'meta-tags' -%}
```

Ese snippet (`snippets/meta-tags.liquid`) emite TODOS los OG tags estándar (`og:title`, `og:description`, `og:site_name`, `og:image`, `twitter:*`, `<title>`, `meta description`). Mi bloque inyectado venía DESPUÉS en el HTML. Los scrapers de OG (FB, WhatsApp, LinkedIn, Slack, Telegram) **usan la primera ocurrencia** que encuentran. → mi bloque era ignorado.

## Solución correcta

Editar `snippets/meta-tags.liquid` directamente. Estructura del snippet:

1. Bloque `{%- liquid ... %}` que asigna `og_title`, `og_description`, `og_url`, `og_type` con condicionales por `request.page_type`. **Aquí van los overrides:**

   ```liquid
   if request.page_type == 'index'
     assign og_title = 'SPEKGEN — Agencia de Marketing Digital con IA'
     assign og_description = '...'
   endif
   ```

2. Hardcoded `<meta property="og:site_name" content="{{ shop.name }}">` — si el shop name de la tienda staging es feo (ej. "My Store"), reemplazar por hardcode (`content="SPEKGEN"`). Cambiar el shop name real en Settings afecta facturas y emails — mejor no.

3. Bloque condicional para og:image: `{% if page_image %}...{% elsif page.metafields.seo.image_url %}...{% endif %}`. Para tener un fallback global (cualquier página que no tenga su propia imagen), agregar `{%- else -%}` con la URL del CDN:

   ```liquid
   {%- else -%}
     <meta property="og:image" content="https://cdn.shopify.com/.../og-image.png">
     <meta property="og:image:secure_url" content="...">
     <meta property="og:image:width" content="1200">
     <meta property="og:image:height" content="630">
     <meta property="og:image:type" content="image/png">
     <meta name="twitter:image" content="...">
   {%- endif -%}
   ```

## Regla operativa

> Cualquier override de OG/SEO en una tienda Horizon va en `snippets/meta-tags.liquid`, **no** en `theme.liquid`.

## Cache de propagación

Después de un PUT a theme assets, el HTML del storefront sigue cacheado por Shopify CDN ~5-15 min. Tocar `templates/index.json` ayuda pero no garantiza invalidación inmediata. Para forzar refresh del cache de Meta/WhatsApp después de propagar, usar Facebook Sharing Debugger > "Scrape Again".

## Aplicabilidad

Cualquier tienda con tema Horizon (incluye stores HC/GR/MG/LF si en algún momento migran a Horizon). Para temas legacy (Sense, Dawn, etc.) verificar si tienen el mismo patrón snippet — la mayoría sí.
