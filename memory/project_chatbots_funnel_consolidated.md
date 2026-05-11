---
name: SPEKGEN chatbots funnel consolidado
description: spekgen.com/chatbots es el único funnel de Chatbots desde 2026-05-07. f1.spekgen.com/automatiza queda pending decommission/redirect.
type: project
originSessionId: 2307f97b-b108-497d-9b58-e24169bbffd6
---
**Hecho 2026-05-07:** Consolidación del funnel de Chatbots en un solo URL canónico.

- **Antes:** dos URLs simultáneos — `f1.spekgen.com/automatiza` (GHL Funnel) + `spekgen.com/pages/chatbots-v4f503e` (Shopify info page).
- **Ahora:** **`spekgen.com/chatbots`** es el único. Handle versionado actual: `chatbots-v4a8b46`. Source: `WEBSITE/pages/chatbots.html`. Publisher: `python3 _publish_pages.py chatbots`.

**Estructura del funnel (orden):** Hero (H1 "Activa un Bot de Ventas en WhatsApp en 72 horas" + badge "★ 4.5/5 · 150+ empresas Jalisco") → Ejemplos en acción (3 videos GHL `<video>` directos desde `assets.cdn.filesafe.space`, autoplay muted loop) → Problema → Cómo funciona → Capacidades → Canales → Casos de uso → Dashboard unificado (kanban mockup) → Promesa → FAQ ("72hrs piloto + 7-10d versión completa") → CTA WhatsApp+email.

**Decisión clave:** sin form GHL inline. CTAs apuntan directo a WhatsApp (`wa.me/523339829069`) o `mailto:hola@spekgen.com`. Gibran prefiere fricción cero — no quiere form de calificación pre-llamada.

**Why:** SEO (autoridad dominio root spekgen.com) + tracking limpio (GA4/Pixel/CAPI ya viven en Shopify) + un solo lugar que rankea + menos infra que mantener. Eliminado riesgo de duplicación cross-canal y dilución de conversiones.

**How to apply:**
- Si Gibran pide "mejorar el funnel chatbots" o "actualizar la página chatbots" → editar `WEBSITE/pages/chatbots.html` y republicar. NO crear nuevos URLs paralelos.
- Si pregunta "dónde está el funnel de chatbots" → `spekgen.com/chatbots` (no `f1.spekgen.com/automatiza`).
- Si pregunta sobre subdomain `f1.spekgen.com` → pendiente de decommission. El redirect 301 `f1/automatiza → spekgen.com/chatbots` se configura desde panel GHL (Funnels & Websites → Settings → Domain redirect), no desde Shopify.

**Pendientes:**
- Configurar redirect 301 desde panel GHL.
- Validar/depurar badge "150+ empresas en Jalisco · 4.5/5" — heredado de f1, falta confirmar si la cifra es real o requiere ajuste conservador.
- Apagar subdomain f1.spekgen.com una vez confirmado tracking limpio.
