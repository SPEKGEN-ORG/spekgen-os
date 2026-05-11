---
name: API keys must be stored globally and never re-asked
description: Never re-ask for API keys already provided. Store globally. Maintain readable credentials map Gibran can access.
type: feedback
---

Si Gibran ya dio una API key, NUNCA volver a pedirla. Guardarla de forma que todas las sesiones la tengan disponible.

**Why:** Gibran ha dado la misma Gemini API key múltiples veces en diferentes sesiones y dentro de la misma sesión. Los archivos .env están ocultos en carpetas que Gibran no conoce ni sabe manejar. Esto le frustra profundamente.

**How to apply:**
1. Cuando Gibran dé una API key nueva, guardarla en el `.env` del cliente correspondiente Y documentar su existencia en `SPK - SPEKGEN AGENCY/_CREDENTIALS_MAP.md`
2. Para keys globales (como Gemini API), guardarla en el `.env` de CADA cliente que la necesite Y en la configuración global de Claude si es posible
3. NUNCA preguntar por una key que ya está en un .env — leer el .env primero
4. Mantener `_CREDENTIALS_MAP.md` actualizado como referencia legible para Gibran (muestra qué keys existen, dónde están, su status — pero NO los valores)
5. Si un token expira o falla, informar a Gibran con contexto: "El token de X expiró. Está en {path}/.env, línea META_TOKEN. Necesito que lo regeneres en {plataforma}"
