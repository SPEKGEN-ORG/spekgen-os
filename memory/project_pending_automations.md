---
name: Pending automations — batch upload, auto-publisher
description: Auto-publisher DONE (Make+Vercel). /publish-post DONE. Batch upload pending.
type: project
---

Automatizaciones: auto-publisher y /publish-post completados.

**Why:** Reducir trabajo manual y preparar para autonomia Japon (30 abril).

## 1. Skill `/publish-post` — COMPLETADO 2026-04-03
- Skill creada e instalada en `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/publish-post/`
- Publica contenido de @gibran.alonzo.ecom directamente a IG+FB via Meta API
- Flow: local images -> Supabase Storage (public) -> Meta API
- LIMITACION: Scheduling via API no funciona (whitelist error). Solo publicacion inmediata.
- Probado: 7 posts publicados exitosamente (GA-005 a GA-012)

## 2. Auto-Publisher — COMPLETADO 2026-04-08
Sistema de doble capa, 100% cloud, funciona sin compu/Claude:

**Capa 1 — Make.com Scenario (principal):**
- Scenario ID: 4682719 ("SPEKGEN Auto-Publisher (All Clients)")
- Carpeta: SPEKGEN — Agency (226102)
- Frecuencia: cada 60 minutos
- Accion: POST a `https://spekgen-hub.vercel.app/api/auto-publish` con Bearer token
- Sin filtro de cliente: publica posts de TODOS los clientes (HC, GR, futuros)
- Status: ACTIVO

**Capa 2 — Vercel Cron (backup):**
- Configurado en `vercel.json` del repo spekgen-hub
- 2 crons: 11 AM MX (17 UTC) + 5 PM MX (23 UTC)
- Usa GET handler agregado al endpoint (commit 89aab74)
- Vercel envia `Authorization: Bearer {CRON_SECRET}` automaticamente

**Endpoint `/api/auto-publish`:**
- Soporta GET (Vercel Cron) y POST (Make/manual)
- Busca posts `approved` (date_planned=hoy, time_planned<=ahora) + `scheduled` (publicar ahora)
- Publica IG carousel + FB multi-photo
- Notificaciones email en exito/fallo
- Auth: Bearer spekgen-sync-cron-2026 (env var CRON_SECRET en Vercel)

**Maximo retraso:** 1 hora desde hora programada (Make cada 60 min).

**Scenario anterior HC (ID 4657645, cada 3h):** Posiblemente redundante ahora. El nuevo scenario 4682719 cubre todos los clientes.

**Scheduled task local `hc-daily-autopublisher`:** Desactivada. Ya no se necesita.

## 3. Skill `/upload-to-hub` batch — PENDIENTE
- Subir multiples posts al Content Hub de un solo comando
- Input: "sube MG-001, MG-002, MG-003"
- Lee calendario xlsx, encuentra folders de Drive, crea content items batch en Supabase
