---
name: Content Hub en Shopify — portal HC canónico en /pages/hc-vault con hc-v13
description: Portal HC live en /pages/hc-vault (único handle canónico permanente, template_suffix hc-v13). 11 tabs con hash routing español (#pendientes, #aprobados, #reportes, #servicios, etc). Tab Mis Reportes + Servicios contratados. Both hc-vault y hc-stage pages apuntan al mismo template_suffix para cubrir bookmarks viejos.
type: project
originSessionId: cc9a53ea-14de-469a-9ef4-f9341518672d
---
El Content Hub v2 (spekgen-hub.vercel.app) migrado a Shopify desde 2026-04-11. Store `yca1z0-wf.myshopify.com` (Horizon, theme 159715688705).

## Estado 2026-04-20 (sesión 41) — Refactor final con hc-vault canónico

**URL canónica permanente HC:** `https://spekgen.com/pages/hc-vault` (también accesible vía `https://yca1z0-wf.myshopify.com/pages/hc-vault`).

**Template activo:** `templates/page.hc-v13.liquid` (170787 chars, cache-bust tag `2026-04-20-reports-tab-hashrouting-v13`).

**Pages Shopify apuntando a hc-v13:**
- `hc-vault` (gid://shopify/Page/133254906113) — canónico
- `hc-stage` (gid://shopify/Page/133255069953) — histórico, mantiene contenido idéntico via mismo template_suffix

**Single-handle rule:** `hc-vault` NO cambia nunca. Iteraciones del template solo versionan `template_suffix` (hc-v13 → hc-v14 → …). Anti-patrón anterior (crear hc-vault-v2 por cambios de diseño) queda deprecado. Las versiones viejas poisoned siguen listadas en el case block para que `client_slug` resuelva a `hc` si alguien llega por bookmark antiguo.

## Tabs (11 total) con hash routing bidireccional español

| Tab (data-tab) | Hash visible | Panel |
|---|---|---|
| `pending` | `#pendientes` | content_item.status = review |
| `draft` | `#en-produccion` | content_item.status = draft |
| `approved` | `#aprobados` | content_item.status = approved |
| `scheduled` | `#programados` | content_item.status = scheduled |
| `published` | `#publicados` | content_item.status = published |
| `rejected` | `#rechazados` | content_item.status = rejected |
| `changes` | `#cambios` | content_comment asociados |
| `calendar` | `#calendario` | vista calendar de content_item |
| `reports` | `#reportes` | client_document con category in [report_monthly, report_weekly] |
| `documents` | `#documentos` | client_document (otras categorías) |
| `services` | `#servicios` | contracted_service |

JS: mapping `TAB_TO_HASH` + reverso `HASH_TO_TAB`. `window.history.replaceState` al click, `window.addEventListener('hashchange')` para deep-link/refresh.

## Metaobjects activos

- **`content_item`** (22 campos): posts orgánicos. Incluye `media_image_urls: list.url`, `ig_post_url: url`, `fb_post_url: url`, `date_published: date_time`.
- **`content_comment`** (6 campos): feedback/cambios solicitados por cliente.
- **`client_document`**: reportes + docs. Fields: `client`, `category` (report_monthly/report_weekly/contract/payment/brief/other), `title`, `description`, `file_url`, `date`, `badge`.
- **`contracted_service`**: servicios contratados por cliente. 8 entries HC.

**⚠️ CRITICAL metaobject pitfall:** Se crean en `capabilities.publishable.status: DRAFT` por default. Liquid `shop.metaobjects.TYPE.values` SOLO expone los `ACTIVE`. Si un portal muestra lista vacía cuando el metaobject existe, revisar status primero. Fix: `metaobjectUpdate` con `capabilities: { publishable: { status: ACTIVE } }`.

## Primer reporte cargado en Mis Reportes

- Metaobject id: `gid://shopify/Metaobject/388824498433`
- Handle: `hc-reporte-mes1-marzo-abril-2026`
- client=hc, category=report_monthly, badge="Mes 1"
- file_url: `https://spekgen.com/hc-reporte-marzo-abril-visual`
- Status: ACTIVE (manualmente tras create en DRAFT)

## Page route vs UrlRedirect

Shopify page match gana contra redirect table. Redirect `/pages/hc-stage → /pages/hc-vault` creado (id 484836016385) pero NO dispara mientras hc-stage page exista. Workaround: ambas pages → mismo template_suffix (hc-v13) → contenido idéntico. Solo hard-delete de hc-stage activaría el redirect.

## Cache CDN

App-level caching. Cambios a metaobjects tardan ~15-20s en propagarse al HTML servido. Cache-bust `?v=$(date +%s)` y header `Cache-Control: no-cache` NO invalidan — es caching detrás del CDN. Esperar + recurl es el único camino.

## Source files / scripts

- Local template source: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/theme/page.content-hub.liquid` (editado y subido como `page.hc-v13.liquid`)
- Upload pipeline para posts: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/upload_post_to_hub.py` (portal_url hardcodeado = `hc-vault` desde sesión 41, antes era `hc-stage`)
- Shopify client helper: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/shopify_client.py` — paths GraphQL/REST SIEMPRE con leading `/` (sin slash concatena mal al base URL)

## Make scenario para acciones del cliente

- **Make scenario 4706750** ("SHOPIFY — Content Hub Actions")
- Webhook: `https://hook.us2.make.com/tjmc0lxbm57syhifsv136m2db842u2pr`
- Flujo: webhook → webhookRespond (CORS) → HTTP OAuth (JSON) → SetVariables (new_status, comment_category, feedback_clean, client_name_clean) → Router: (A) metaobjectUpdate status siempre, (B) metaobjectCreate content_comment si action contiene "changes"

## Auto-publish para posts aprobados

- Make scenario 4682719 (hourly): consulta metaobjects con status `approved` + hora llegada, publica a IG/FB via Meta API
- Vercel cron backup 11am + 5pm MX (gap nocturno 17:01-10:59 cubierto solo por Make — SPOF conocido)

## Otros clientes pendientes

- **GR + MG LIVE 2026-04-24:** `spekgen.com/pages/gr-stage` y `/pages/mg-stage` (200 OK). Template `page.content-hub.liquid` parameterizado por handle; suffixes `gr-v1` y `mg-v1`. Backfill ejecutado via `08_backfill_from_meta.py` — GR 12 posts desde 2026-03-30, MG 11 posts (incluye dupes MG-H007..H011). Aprobador en ambos: gibran.alonzo0506@gmail.com (Gibran como "cliente" stress-test).
- **Pages pendientes:** LF (`lofit-live`), Gibran Ecom. HC-GR-MG es piloto validado tri-cliente.

## Dashboard interno agencia (2026-04-24)

- **URL:** `https://spekgen.com/pages/clientes` (bookmark Gibran). Page id `133676925185`, template_suffix `clientes`.
- 3 cards → `/pages/hc-stage`, `/pages/gr-stage`, `/pages/mg-stage`. Logo SPEKGEN auto-swap black/white según tema. Toggle light/dark con `localStorage['spk-theme']` + script pre-paint anti-flash.
- Template: `theme/page.clientes.liquid` con `{% layout none %}` (HTML standalone, sin chrome de Horizon).
- Script: `04_setup_clientes_dashboard.py` (idempotente, sube 2 logos binarios via `attachment` base64 + template + page upsert). Re-run para iterar.
- `noindex,nofollow` meta → no aparece en Google.

## Assets del tema

- `assets/spekgen-logo-white.png`, `assets/spekgen-logo-black.png`, `assets/hc-logo.png`
- Subidos via REST API base64 attachment

## Why hc-vault y no hc-stage

hc-stage existía como piloto pero hc-vault fue declarado canónico en sesión 41 tras diagnóstico de split de templates (hc-vault en hc-v9, hc-stage en hc-v11). hc-vault ganó porque es el nombre que Gibran comunica a los clientes y el que aparece en emails de notificación. Alternativa futura: borrar hc-stage hard, consolidar a 1 sola page + redirect activo.
