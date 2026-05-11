---
name: Delivery Services — Nueva línea SPEKGEN (Bundle Delivery+Bot)
description: Línea SPEKGEN mayo 2026. Bundle Uber Eats + bot WhatsApp atención. Foco La Paz. Pricing piloto reducido. Stack Last.app + bot HC/GR adaptado. Carpeta DELIVERY SERVICES.
type: project
originSessionId: fa394a30-0084-40b6-8dfc-c6430716e9fb
---

# Delivery Services — Línea de servicio (2026-05-02)

## Origen
Conversación con prospecto Yerena (DS-001, vet La Paz, mockup spekgen.com/pages/yerenamockup-v30cf35). Necesidades #1 reveladas: delivery (Uber/Rappi/DiDi) + bot atención WhatsApp. NO website. Eso disparó research de 4 deep researches Gemini y creación carpeta `SPK - SPEKGEN AGENCY/DELIVERY SERVICES/`.

## Pivote 2026-05-02 — Bundle Delivery + Bot
Yerena casi no le interesa website, le interesa delivery + bot atención. Cambia oferta principal a **Bundle Delivery + Bot WhatsApp**. Razones:
- Bot tiene costo marginal cero para SPEKGEN (stack HC v2.8.2 y GR v1.2 ya en producción).
- Conexión bot ↔ delivery = círculo virtuoso (bot manda links Uber Eats con códigos).
- Mayor ticket por cliente, mejor cierre.

## Hallazgos clave del research
- Carga real al comercio en plataformas: ~38.5% (no solo 25-30% comisión).
- Rappi liquida MENSUAL — drena cash flow PyME. Uber/DiDi semanal.
- Uber Eats Marketplace API documentada (4-8 sem integración). Rappi Developer Portal accesible. DiDi Food NO tiene API pública (forzado a middleware).
- Tarifa activación Uber Eats "hasta $5K MXN" según research — variable, NO certero. Validar al alta.
- **Agregador elegido: Last.app** — $1,000-$2,900 MXN/mes/local, SaaS puro sin tarifa por orden, marcas virtuales ilimitadas, API abierta, CFDI nativo.
- Estrategia "Caballo de Troya": migrar clientes de plataformas a DTC propio en Tier 3 (mes 7+).

## Estructura carpeta
```
SPK - SPEKGEN AGENCY/DELIVERY SERVICES/
├── _BRIEF_EJECUTIVO.md           ← entry point
├── RESEARCH/                      ← 4 deep researches (txt)
├── 01. STRATEGY/la_paz_market_brief.md
├── 02. SERVICE CATALOG/service_tiers_pricing.md
├── 03. TECH STACK/aggregator_decision.md
├── 06. PROSPECTS/_prospects_log.md
└── 07. PILOT_YERENA/
    ├── pilot_plan.md
    └── whatsapp_yerena.md
```

## Service Tiers (v0.2 — pricing piloto reducido)
Pricing para **primeros 5 clientes** en La Paz (vs precio estándar futuro):

- **Tier 0 Audit:** $1,500 MXN one-time
- **Tier 1 Solo Delivery:** $4,500 setup, sin retainer (vs estándar $8-12K)
- **Tier 2 Bundle Delivery+Bot ⭐:** $5,500 setup + escalonado $2,500→$4,500→$5,500/mes (vs estándar $12-18K + $4.5-6.5K/mes). Total año 1: ~$56,500 MXN.
- **Tier 3 Multi+DTC:** upgrade desde Tier 2 mes 7+. +$12K setup + $7,500/mes + 3% success fee.

**Subir a precio estándar desde cliente #6 si tasa cierre primeros 5 ≥60% y ROI cliente ≥1.5x.**

## Piloto Yerena (DS-001) — Bundle
- Setup: $5,500 MXN
- Mes 1-3: $2,500/mes
- Mes 4-6: $4,500/mes
- Mes 7-12: $5,500/mes
- Total año 1: ~$56,500 MXN
- A cambio: testimonio video + 3 referidos + permiso caso de estudio
- Vigencia oferta: 15 mayo 2026
- Plataforma única arranque: Uber Eats. DiDi mes 4+ si tracción.
- Bot: 8-10 flujos vet (triage síntomas, agenda, catálogo, recordatorio vacunas, redirect Uber Eats)
- KPIs día 90: ≥15 pedidos/sem, rating ≥4.3, cancel <3.5%, bot resuelve ≥50% sin humano, ROI ≥1.5x
- Tablet: ya en compra por Yerena (no pass-through)
- WhatsApp: número dedicado ya activo (bot va sobre ese)
- Plan completo: `07. PILOT_YERENA/pilot_plan.md`
- WhatsApp listo para mandar: `07. PILOT_YERENA/whatsapp_yerena.md`

## Targets
- Pre-Japón (mayo): cerrar Yerena, NO firmar 2do cliente
- Japón (mayo-junio): Yerena en operación con SOP autónomo
- Post-Japón (julio+): firmar 4-5 clientes Tier 2 piloto La Paz, luego subir a precio estándar
- 12 meses: 8-12 clientes activos, ARR target ~$50-65K MXN/mes adicional → cierra gap a meta $100K combinado con HC/LF/GR/MG

## ICPs ranqueados
- ICP A: restaurantes/fondas locales La Paz, ticket >$150 MXN, RFC vigente
- ICP B: mascotas (vet, pet shop) — Yerena ancla, Rappi Mundo Mascotas
- ICP C: hoteles boutique / restaurants premium turísticos (Tier 3)

## Anti-ICP
- Cadenas con corporativo en CDMX, sin RFC, ticket <$120 MXN, dueños hostiles a subir precios en app

## Riesgos top
1. Operativamente intenso vs ads/contenido — si firmamos 5 sin SOP automatizado, Gibran se ahoga
2. Dependencia única de Last.app — Plan B Deliverect cuando 5+ clientes
3. CFDI/SAT bloquea onboarding si cliente no tiene RFC vigente
4. COFEPRIS — productos veterinarios con receta NO elegibles para delivery, segmentar catálogo

## Skills a construir
- `/delivery-onboard` — input cliente → output catálogo Last.app + prompts Gemini foto + SEO copy + checklist RFC
- `/delivery-daily-pulse` — alerta reembolsos/cancelaciones consecutivas/ratings drop por cliente

## Stack reutilizado (cero costo marginal)
- Bot: HC v2.8.2 (scenario 4781819 PROD) y GR v1.2 — clonar y adaptar a vet
- Foto AI: `/factory-batch` skill con Gemini
- GHL multi-location para CRM y comms
- Make para scenarios alertas/reports
- Google Sheets para dashboards

## Referencias relacionadas en memoria
- project_yerena_outreach.md (origen comercial Yerena)
- project_japan_autonomy_deadline.md (deadline Japón)
- project_clients_overview.md (clientes actuales)
- project_hc_bot_live.md (stack bot HC base reusable)
- project_gr_whatsapp_bot_state.md (stack bot GR base reusable)
