---
name: HC attribution gap is structural, not technical
description: Diagnóstico 2026-05-01 — Pixel+CAPI HC funcionan bien. Gap Shopify-vs-Meta atribución viene de tráfico orgánico FB sin UTM, no de bug técnico
type: project
originSessionId: 64219331-5058-4b5d-b1f2-d0e66c03f256
---
Diagnóstico 2026-05-01 (order #1035, $531 DOGRELAX, sin UTM, no atribuida en Meta Ads Manager):

**Estado técnico HC: TODO BIEN.**
- Pixel `1813096612719811` vivo, last_fired updates frecuentes
- CAPI activo via Shopify FB app (data sharing=Maximum, set 2026-03-23)
- fbq browser-side activo, first_party_cookie enabled
- Purchase events llegan al pixel (2 en 48h)
- GA4 (G-V2FL067WSM) y Clarity (vy5jjgw9yi) tracking OK

**Por qué el gap (16 ads, $1,780 spend, 1 attributed purchase vs 27 GA4 purchases):**
- Shopify lee fuente desde HTTP `Referer` (ej. `l.facebook.com`), NO desde UTMs
- Tráfico orgánico FB (post/bio/story/comment/share) no tiene UTMs → llega como "Facebook" en Shopify pero sin nada que Meta pueda atribuir
- Clarity 30 abr por Source: 39 sesiones `meta` (ads) vs 29 sesiones FB orgánico (`facebook` + `facebook.com` + `l.facebook.com`)
- Meta solo atribuye purchases si hubo click/view de ad en ventana de atribución

**Why:** Es FUNCIONAMIENTO NORMAL. El gap de atribución refleja que HC tiene equity orgánico — no es un bug.

**How to apply:**
- Si Gibran reporta "Meta no atribuyó esta venta": NO asumir que algo está roto. Primero verificar referrer/UTMs de la sesión.
- NO construir monitor cross-source completo (Shopify×Meta×GA4×Clarity) por defecto — solo si CAPI/pixel se rompen seguido.
- Acciones de revenue con más impacto que el monitor: (1) UTMear links orgánicos en bio FB/IG, stories, posts, (2) subir match quality CAPI (email/phone hasheado), (3) atender recomendaciones del Meta Ads Manager.
- Versión mínima del monitor (alarma "CAPI muerto" + "Pixel sin firing >4h") sí vale la pena para Japón — 1h setup.

**Helpers diagnósticos creados** en `HC - HEALTHY CHUCHOS/10. LOGS/02. META API SCRIPTS/`:
- `diagnose_attribution_1035.py` — pixel events by type + ad insights + pixel ownership
- `diagnose_capi_split.py` — intentos source aggregation (algunos requieren permisos extra)
- `diagnose_ga4_clarity_1035.py` — GA4 purchases by hour/source + Clarity por Source. **Bug menor:** GA4 path SA viejo. Fix pendiente: usar `HC_SA_JSON_B64` decode + `from_service_account_info` en vez de `GOOGLE_APPLICATION_CREDENTIALS`.

Reusable: estos scripts sirven cross-client (LF, GR, MG) cambiando solo IDs.
