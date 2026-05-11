---
name: Content Intel System replication blueprint
description: Blueprint canónico para replicar el sistema de scraping de HC a otros clientes (SPEKGEN, GR, LF, MG, Gibran Ecom). Docs completos en el repo.
type: project
originSessionId: 212e36ac-5550-4693-ac20-3d31f9d628db
---
Sistema de inteligencia competitiva autónomo (scraper diario) construido 2026-04-10/14 con HC como piloto. Vendible como add-on $2.5K-7.5K MXN/mes por cliente.

**Blueprint canónico:**
`~/Desktop/repos/Spekgen-ops/scripts/content-scraper/REPLICATION_BLUEPRINT.md`

**Pointer en Drive:**
`SPK - SPEKGEN AGENCY/SPK - 07. BLUEPRINTS/CONTENT_INTEL_SYSTEM_v1.md`

**Status por cliente:**
- HC: ✅ Live desde 2026-04-14
- GR, LF, MG, SPEKGEN, Gibran Ecom: ❌ Pendiente replicar

**How to apply:**
- Cuando Gibran pida "replicar el scraper a {cliente}" → abrir REPLICATION_BLUEPRINT.md y seguir Fase 1 (pedir inputs) → Fase 2 (setup técnico) → Fase 3 (entrega) → Fase 4 (memoria)
- El único archivo que cambia por cliente es `configs/{cliente}.json` — todo el pipeline es cliente-agnóstico
- Costo infra: ~$13 USD/mes por cliente
- Pricing add-on: $2.5K (básico) / $4.5K (pro) / $7.5K (elite) MXN/mes

**Why guardar esto:**
Sistema robusto y replicable. No reinventar. Cada replicación debe seguir el mismo blueprint para mantener consistencia y poder debuggear cross-client.

**Content marketing asociado:**
Ideas GA-043, GA-044, GA-045 agregadas a `GIBRAN_CONTENT_IDEAS.xlsx` (2026-04-14) — posicionar el servicio como "Content Intelligence as a Service" en @gibran.alonzo.ecom.
