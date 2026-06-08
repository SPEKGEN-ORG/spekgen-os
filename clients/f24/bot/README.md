# F24 Bot — Pipeline de Promos (cloud)

Sincroniza las **promos activas** del bot de WhatsApp de Ferre24 desde un Google Sheet,
las aplica a Shopify y redeploya el cerebro en Make. Corre solo (GitHub Actions, Japan-proof).

## Fuente de verdad
Sheet **INVENTARIO F24** (`1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U`), pestaña
**🔥 PROMO ACTIVA**. El equipo de F24 marca promos en "📦 STOCK Y PROMOS" → esa pestaña se
auto-llena. Una sola edición del equipo se propaga a Shopify y al bot.

## Pipeline (orden obligatorio)
1. `sync_f24_promos.py --apply` — lee PROMO ACTIVA → aplica precio promo + tachado a Shopify
   (solo SKUs con Precio Promo que existan en Shopify) + tag `msi-912` a elegibles 9/12 +
   escribe `F24_BOT_KNOWLEDGE/promos_active.json` y `_promo_state.json` (para revertir al expirar).
2. `build_f24_knowledge.py` — regenera `CATALOG_INDEX.md` / `catalog.json` con precio promo + MSI.
3. `build_f24_bot_blueprint.py` — arma el blueprint de Make con el knowledge nuevo.
4. `deploy_f24_bot.sh dev <ver>` — PATCH al scenario Make 5258612.

Local: corre los 4 en orden desde la carpeta del bot en Drive (usa los `.env` locales).
Cloud: el workflow `.github/workflows/f24_promos_sync.yml` los corre 2x/día con secrets.

## Gate 9/12 MSI (MercadoPago Cuenta B)
Solo SKUs con `9` o `12` en la escalera "Meses MSI" reciben el tag `msi-912` en Shopify.
El edge function `f24-process-order` exige ese tag para permitir `payment_method=msi_promo`;
si no, cae a checkout normal (hasta 6 MSI). El precio promo ya vive en Shopify, así que
draft order y link MercadoPago cobran correcto automáticamente.

## Secrets de GitHub Actions (Settings → Secrets → Actions)
| Secret | Valor (de dónde) |
|---|---|
| `F24_SHOPIFY_SHOP` | `.env` F24 → `SHOPIFY_SHOP` |
| `F24_SHOPIFY_CLIENT_ID` | `.env` F24 |
| `F24_SHOPIFY_CLIENT_SECRET` | `.env` F24 |
| `F24_SHOPIFY_API_VERSION` | `.env` F24 (ej. `2024-10`) |
| `F24_SHOPIFY_PRIMARY_DOMAIN` | `.env` F24 (`ferre24.com.mx`) |
| `F24_GHL_API_KEY` | `.env` F24 → `GHL_API_KEY` (PIT) |
| `F24_ANTHROPIC_API_KEY` | `.env` F24 → `ANTHROPIC_API_KEY` |
| `MAKE_API_TOKEN` | `.env` SPK AGENCY → `MAKE_API_TOKEN` |
| `GCP_SA_JSON` | contenido completo de `spekgen_service_account.json` |

> Nunca se commitea el blueprint generado (`_BLUEPRINTS/`) — lleva llaves embebidas. Ver `.gitignore`.
