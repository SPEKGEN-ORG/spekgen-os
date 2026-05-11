---
name: Automation Stack Decisions
description: SPEKGEN agency automation stack — Cloud Env, Make, GHL, Vercel, GitHub decisions and limitations (2026-04-02)
type: project
---

Stack de automatizacion decidido para SPEKGEN agency (actualizado 2026-04-02):

**Claude Code Cloud Environment** — PIEZA CENTRAL para Japón. Gibran ya tiene `claude-code-default` incluido en Max Plan ($100 USD/mes). Workspace en la nube, accesible desde cualquier dispositivo (teléfono, iPad, web). Scheduled tasks remotas corren sin Mac encendida. Semana 2-7 abril: prueba completa de migración.


**Make.com** — Rol: PEGAMENTO entre servicios, NO pieza central. Conectado via MCP en Claude Code. Free tier actual (1,000 ops/mo, 2 scenarios, 15 min interval minimo). Org ID: 2681221, Team ID: 354061. Upgrade a Core ($10.59/mo) pendiente. **LIMITACION MCP:** Claude puede listar y crear scenarios, pero NO puede activar, actualizar, ni ejecutar — error "Forbidden to use token authorization". Gibran debe activar scenarios manualmente en Make.com UI (1 click). **Evaluación 2026-04-02:** Make NO está outdated pero con el stack actual (Claude Code Cloud + Meta API + GHL) su rol es conectar cosas simples sin código (GHL→Sheets, Meta→alertas email), no como orquestador principal.

**Módulos verificados en Make (2026-04-01):**
- `instagram-business` v1: Watch comments (trigger), Create comment/reply, Post photo/carousel/reel, Get insights. **NO tiene DMs.**
- `manychat` v1: Webhook trigger, Send messages/flows, Manage subscribers/tags. Requiere ManyChat Pro ($15/mo) — descartado por costo.
- Para DMs: se usará HTTP module + Instagram Graph API directo con permiso `instagram_manage_messages`.

**BLOCKER actual (2026-04-01):** Al intentar autorizar Instagram Business en Make via OAuth, no aparece la cuenta/página de HC. Diagnóstico probable: (1) IG de HC no vinculada a FB Page, (2) usuario FB sin admin en BM HealthyChu (880354658373862), (3) permisos faltantes en OAuth. ClickUp: https://app.clickup.com/t/86e0p5ake

**Ruta elegida: Make Core + Instagram API directo.** Claude arma scenarios completos. Gibran solo autoriza OAuth (1 vez) y activa scenarios (1 click cada uno).

**GoHighLevel (GHL)** — Gibran ya lo paga. Tiene comment-to-DM nativo. Gibran lo usa como fallback manual cuando Make no está listo. MCP oficial no conectado aún.

**Vercel + GitHub** — Stack para landing pages. Free tier. Aún no creado.

**Meta App SPEKGEN:** App ID 1683612316139834 bajo HealthyChu BM. Gibran trabajando en App Review con permiso `instagram_manage_messages`. ~10 días para aprobación.

**Why:** Gibran no quiere configurar workflows manualmente. Claude debe hacer todo via MCP/API. Make es la plataforma elegida porque Claude tiene MCP funcional.

**How to apply:** Para IG DM flows → GHL manual (hoy) mientras se resuelve blocker de IG en Make (mañana). Para automatizaciones futuras (email, scheduling, cross-client) → Make via MCP.
