---
name: publish-prospect
description: Publica mockup+propuesta de un prospecto a spekgen.com con URLs públicas limpias (spekgen.com/{slug}mockup y /{slug}propuesta). Sube imágenes al CDN de Shopify, oculta el chrome del tema, versiona el handle por hash de contenido para bypass del page_cache poisoning de Shopify. Úsalo cada vez que termines mockup+propuesta de un prospecto nuevo y Gibran quiera mandar el link público.
---

# /publish-prospect

Infra reusable para publicar mockup + propuesta de cualquier prospecto a `spekgen.com`.
Gibran va a procesar 2-4 prospectos/día = 10-20 deploys/semana. **No hacer esto a mano.**

## Cuándo usar

- Después de terminar el mockup HTML del sitio + propuesta HTML de un prospecto
- Gibran dice "publica X a spekgen" o "súbele el link a spekgen"
- El prospecto ya tiene carpeta en `SPK - SPEKGEN AGENCY/PROSPECTOS/{NOMBRE}/`

## Pre-requisitos

El prospecto debe tener:

```
SPK - SPEKGEN AGENCY/PROSPECTOS/{NOMBRE}/
├── mockup_website/
│   ├── index.html              ← default; override con --mockup
│   └── assets/                 ← default; override con --assets
└── propuesta/
    └── PROPUESTA_{X}.html      ← pasar con --propuesta
```

Credenciales Shopify: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/.env` (se usa la misma app que Content Hub).

## Uso

```bash
cd "SPK - SPEKGEN AGENCY/PROSPECTOS"
python3 _publish_prospect.py \
    --slug enlace \
    --prospect-dir "ENLACE TELECOMUNICACIONES - LA PAZ" \
    --propuesta "propuesta/PROPUESTA_ENLACE.html" \
    --brand "Enlace Telecomunicaciones"
```

Flags:
- `--slug` (requerido) — prefijo limpio para las URLs. `enlace` → `spekgen.com/enlacemockup` + `spekgen.com/enlacepropuesta`
- `--prospect-dir` (requerido) — ruta a la carpeta del prospecto (absoluta o relativa)
- `--mockup` (default `mockup_website/index.html`) — HTML del mockup
- `--propuesta` (requerido) — ruta relativa al HTML de la propuesta
- `--assets` (default `mockup_website/assets`) — carpeta de imágenes del mockup
- `--brand` (requerido) — nombre de la marca, se usa en el `<title>` de la page

## Qué hace el script

1. Autentica a Shopify (OAuth client_credentials vía `ShopifyClient` de Content Hub)
2. Lee caché local `{prospect-dir}/.spekgen_publish_cache.json` para no re-subir imágenes
3. Para cada HTML (mockup + propuesta):
   - Recorre `src="..."` y `url(...)` → resuelve archivo local → sube a Shopify Files API (staged upload + `fileCreate` + poll `READY`) → obtiene URL CDN → reemplaza en el HTML
   - Extrae `<head>` (preserva `<script>`, `<style>`, `<link>`) + envuelve el `<body>` en `<div id="spekgen-prospect-wrap">`
   - Antepone `CHROME_HIDER_CSS` que oculta header/footer de Horizon + quita constraints de width
4. Crea pages con handle **versionado por hash de contenido**: `{slug}mockup-v{sha256[:6]}` (bypass del page_cache poisoning de Shopify)
5. Crea/actualiza URL redirects `spekgen.com/{slug}mockup` → `/pages/{slug}mockup-v{hash}`
6. Limpia versiones viejas (borra pages `{slug}mockup-v*` que no sean la actual)

Al final imprime los 2 links públicos listos para mandar al prospecto.

## Arquitectura técnica (por qué así)

- **Versionado por hash:** Shopify tiene un bug conocido de `PageDetailsController:page_cache` que sirve HTML stale aunque la page se actualice vía admin. El workaround documentado (`feedback_shopify_page_cache_poisoning.md`) es **usar un handle nuevo cada vez que cambia el contenido**. El hash sha256[:6] del body_html es la clave — si el contenido no cambia, el handle es el mismo (idempotente); si cambia, nuevo handle + nuevo redirect → nueva entrada en el cache.
- **Wrapper `#spekgen-prospect-wrap`:** el tema Horizon mete el body dentro de `<rte-formatter>` que tiene `display: inline` por default. Sin wrapper, las secciones block-level dentro colapsan. El wrapper es `display: flex; flex-direction: column; align-items: center` para que páginas fixed-width (propuesta A4) se centren y contenido full-bleed (mockup hero) se estire.
- **Caché de imágenes:** `file_hash(sha256[:16])` como key. Subir los mismos assets en cada re-run sería lento (staged upload + poll READY = ~3s por imagen). El .gitignore o equivalente debería ignorar `.spekgen_publish_cache.json`.

## Output esperado

```
[1/5] Auth Shopify...
    ✓ My Store (https://spekgen.com)
    cache: 11 files

[2/5] Processing mockup (index.html)...
    ✓ 0 uploaded, 11 cached, 2 remote skipped
    body size: 41 KB

[3/5] Processing propuesta (PROPUESTA_ENLACE.html)...
    ✓ 0 uploaded, 1 cached, 1 remote skipped
    body size: 33 KB

[4/5] Creating/updating Shopify pages...
    ✓ created page id=133480XXXXXX handle=enlacemockup-v82363c
    ✓ created page id=133480XXXXXX handle=enlacepropuesta-vc24a04

[5/5] Creating/updating URL redirects...
    ↻ updated redirect /enlacemockup → /pages/enlacemockup-v82363c
    ↻ updated redirect /enlacepropuesta → /pages/enlacepropuesta-vc24a04

    Cleaning stale versions...
    🗑  deleted stale page handle=enlacemockup-vf5d1a0

DONE — links públicos listos para mandarle al prospecto:
  https://spekgen.com/enlacemockup
  https://spekgen.com/enlacepropuesta
```

## Troubleshooting

**Contenido se ve en blanco:** probable que el wrapper no esté envolviendo bien. Revisa que `<body>...</body>` esté presente en el HTML (no usar HTMLs fragmentarios).

**Imágenes rotas:** chequea `.spekgen_publish_cache.json` — si tiene URLs viejas que ya no existen en Shopify, bórralo para forzar re-upload.

**Header del tema visible:** si un update de Horizon cambia selectors, actualiza `CHROME_HIDER_CSS` en `_publish_prospect.py`. Inspecciona con `curl -sL https://spekgen.com/{slug}mockup | grep -i 'header\|announcement'` y luego agrega el selector nuevo.

**Se pierde el link:** los redirects son únicos por `path`. Si alguien crea manualmente un redirect `/enlacemockup` que apunte a otro lado, el script lo sobrescribe en el siguiente run. No hay riesgo de duplicación.

## Ruta del script

`SPK - SPEKGEN AGENCY/PROSPECTOS/_publish_prospect.py`

Depende de: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/shopify_client.py` y `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/.env`.
