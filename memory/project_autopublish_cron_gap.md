---
name: Auto-publish cron gap risk
description: Vercel crons solo 11 AM y 5 PM MX — gap de 18h cubierto solo por Make cada 1h. Riesgo Japan-proof
type: project
---

El auto-publisher de spekgen-hub tiene cobertura incompleta:

**Infraestructura actual (verificada sesión 24, 2026-04-09):**
- Vercel crons en `vercel.json`: `0 17 * * *` (11 AM MX) + `0 23 * * *` (5 PM MX) — llaman `/api/auto-publish` vía GET con Bearer CRON_SECRET
- Make scenario 4682719 "SPEKGEN Auto-Publisher (All Clients)": cada 60 min, llama el mismo endpoint
- Lógica endpoint: busca `status='approved' AND date_planned=today AND time_planned<=now` + `status='scheduled'` (publicar-ahora)

**El gap:**
- Entre 17:01 y 10:59 MX (≈18 horas), Vercel NO dispara ningún cron
- Si cliente aprueba en ese rango → depende 100% de Make (single point of failure)
- Si `date_planned<today` el post queda huérfano para siempre — no hay fallback

**Evidencia real (HC-011, 2026-04-09):**
- Cliente aprobó ~21:00 MX → Make pescó a las 21:04 MX → publicó OK
- Funcionó de milagro — Vercel no iba a ayudar hasta 11 AM del día siguiente, y para entonces `date_planned != today` → endpoint lo hubiera ignorado

**Why:** Cuando Gibran esté en Japón sin WiFi 21 días, si Make falla o el Meta token vence, posts aprobados tarde quedan atascados sin forma de auto-recuperarse.

**How to apply:** Antes de que Gibran vuele (deadline ~2026-04-30), aplicar **dos fixes**:
1. Agregar cron Vercel a las 22:00 MX (`0 4 * * *`) al `vercel.json` — cubre el caso "aprobación nocturna del cliente"
2. Modificar query de auto-publish en `/Users/gibranalonzo/Developer/spekgen-hub/app/api/auto-publish/route.ts` líneas 233-238 para incluir posts atrasados: `status='approved' AND date_published IS NULL AND date_planned <= today` (en vez de `=today`). Evita que un post aprobado tarde quede huérfano si el cron de ese día ya pasó.

Ambos fixes son <10 líneas, <10 minutos. Registrados en sesión 24 de HC `_CLIENT_CONTEXT.md` y KB.
