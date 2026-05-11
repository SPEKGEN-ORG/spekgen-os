---
name: LF Analytics Monitor (GA4 + Clarity)
description: LO FITNESS analytics cloud monitor — GitHub Actions, días pares 9:07 AM MX, Sheet 1x0ei-hGN…, LIVE 2026-04-14
type: project
originSessionId: 3ceb1165-acd2-4d03-a25b-a17a39c21373
---
LF Analytics Monitor desplegado 2026-04-14 como Japan-proof infra.

**Why:** Gibran vuela a Japón ~30 abril sin WiFi 21 días. Monitoreo GA4 + Clarity debe correr autónomo en la nube, mismo patrón que HC y GR.

**How to apply:**
- Workflow: `g-bran/Spekgen-ops/.github/workflows/lf-analytics-monitor.yml`
- Cron: `7 15 2-30/2 * *` (días pares 9:07 AM MX — alterna con GR en impares)
- Reutiliza `scripts/hc-analytics-monitor/analytics_monitor.py` (env-driven, `CLIENT_LABEL=LF` en subject email)
- GA4 Property: 484501054 · Clarity: 2971069061151498
- Product slugs (top 5 GA4 30d): purify, omega-3, citrato-de-potasio, fit-max, activer-metafit
- SA: `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` (Viewer GA4 ✅, Editor Sheet pendiente)
- Reusa secret `GR_SA_JSON_B64` (mismo SA cross-client)
- Secrets LF configurados: `LF_GA4_PROPERTY_ID`, `LF_GA4_PRODUCT_SLUGS`, `LF_CLARITY_PROJECT_ID`, `LF_CLARITY_API_KEY`, `LF_ALERT_EMAIL`
- Failure notification: POST a `MAKE_WEBHOOK_URL` con `html_body` (no `html`)

**Shopify pull agregado 2026-04-14:** secrets `LF_SHOPIFY_CLIENT_ID/SECRET/SHOP` (OAuth client_credentials, app "SPEKGEN Theme Manager"). Test run: 1 orden · $1,485 MXN · AOV $1,485 (7d). Escribe a tabs Shopify_Overview, Shopify_History, Shopify_Products.

**⚠️ Discrepancia crítica GA4 vs Shopify:** GA4 reporta 0 compras, Shopify reporta 1 orden real en misma ventana. El evento `purchase` no se está disparando en el theme Sense de LF. Revisar gtag/dataLayer antes de confiar en el ROAS de los reportes automáticos.

**Estado:** ✅ LIVE desde 2026-04-14. Sheet ID `1x0ei-hGNUHw0_-joMnqtUiIIOhcjXgba-LI3Qhrvv1s` (LF_Analytics_Monitor_Dashboard). Primera corrida manual exitosa: 135 sesiones · 24 ATC · 0 compras · 7 tabs escritos · email enviado en 51s. Primera corrida automática: 2026-04-16 9:07 AM MX.

**Nota:** SA no pudo crear Sheet (storageQuotaExceeded sin shared drive) — si se replica a otro cliente, Gibran debe crear el sheet manualmente y compartir con SA como Editor antes del setup.
