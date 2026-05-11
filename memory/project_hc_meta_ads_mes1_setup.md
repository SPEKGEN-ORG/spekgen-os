---
name: HC Meta Ads Mes 1 — Setup State
description: Estado de la campaña HC Mes 1 (HC-VENTAS-MES1) — 6 organic winners subidos PAUSED, budget $120/día, bloqueos pre-GO (email flows + CHUCHO10 + test purchase)
type: project
---

## Estado actual (2026-04-09, sesión 23)

**Campaña HC-VENTAS-MES1 queda PAUSED esperando GO manual de Gibran.** El setup Meta API está completo y verificado. El lanzamiento depende de bloqueos no-técnicos en Shopify.

## IDs operativos

| Asset | Value |
|---|---|
| Campaign | `HC-VENTAS-MES1` — OUTCOME_SALES — PAUSED |
| Ad Set | `HC-BROAD-MX-PURCHASE` — OFFSITE_CONVERSIONS / PURCHASE |
| Budget | `daily_budget=12000` centavos = **$120 MXN/día** |
| Audience | Broad MX, Advantage+ audience (age 18-65 — ver nota abajo) |
| Pixel | `1813096612719811` (SPEKHC-23MARZO) |
| Ad Account | `act_1626923298353925` |
| Page | `102627388012544` |
| IG | `17841430824981516` |

Los IDs exactos de Campaign/AdSet están en el `.env` del cliente (`META_CAMPAIGN_ID`, `META_ADSET_ID`).

## 6 Organic Winners subidos (PAUSED)

| # | Nombre Ads Manager | Ad ID | Producto | WCI orig | Slides |
|---|---|---|---|---|---|
| O1 | HC-AD-DOLOR-SILENCIOSO-CAROUSEL | 6911066326834 | ArtriDog | 9.81% | 3 |
| O2 | HC-AD-CURCUMINA-CAROUSEL | 6911066345034 | ArtriDog | 7.64% | 3 |
| O3 | HC-DR-OFF-CAROUSEL | 6911066358834 | DogRelax | 7.57% | 6 |
| O4 | HC-OD-OMEGA-EQUIVOCADO-CAROUSEL | 6911066375434 | OmegaDog | 7.18% | 6 |
| O5 | HC-DR-ESTRES-CAROUSEL | 6911066404634 | DogRelax | 6.41% | 6 |
| O6 | HC-GD-REGENERACION-CAROUSEL | 6911066427234 | GastroDog | 4.40% | 6 |

Cobertura producto: ArtriDog 2 · DogRelax 2 · OmegaDog 1 · GastroDog 1. Status: PAUSED, effective_status IN_PROCESS (Meta ad review automático). **3 ads legacy del plan v1 (HC-DR-001, HC-GD-001, HC-AD-001) quedan PAUSED** en el mismo ad set.

## Decisiones técnicas tomadas en sesión 23

1. **Age 18-65 (no 25-55) en Advantage+ audience.** Meta API rechaza `age_max<65` con Advantage+ audience activo (error subcode 1870189). El algoritmo trata age como suggestion, no filter, y optimiza hacia conversión igual.
2. **`degrees_of_freedom_spec.standard_enhancements` NO se envía en creative.** Meta lo deprecó (error subcode 3858504). Si hay que desactivar features individuales, se hace en Ads Manager UI después.
3. **`instagram_user_id` DENTRO de `object_story_spec`** (regla crítica, no al root del creative).
4. **UTMs únicos por ad** en main link y child attachments: `?utm_source=meta&utm_medium=paid&utm_campaign=hc-ventas-mes1&utm_content={slug}`.
5. **CTA SHOP_NOW (Comprar)** uniforme en los 6.

## Script reutilizable

`HC - HEALTHY CHUCHOS/HC - 10. LOGS/02. META API SCRIPTS/hc_mes1_full_setup.py` — Idempotent, 4 fases (A pausa legacy, B fix budget, C sube winners, D verifica). Se puede re-correr para agregar ads nuevos — Meta deduplica imágenes por hash.

## Bloqueos pre-GO (lado cliente, no-técnicos)

1. **Crear código CHUCHO10** en Shopify Discounts (10% off primer pedido)
2. **Activar 4 Shopify Email flows** (copy completo en `HC_ESTRATEGIA_360_v1.md`):
   - Welcome (CHUCHO10)
   - Cart Abandonment (PATITA5)
   - Post-Purchase (COMBO10)
   - Win-Back (RECARGA10 / AMIGO15)
3. **Test purchase end-to-end** (checkout → confirmación → email welcome dispara)
4. **Decisión:** cuando Gibran dé el GO, activar desde Ads Manager UI o via API (script puede extenderse con `phase_e_activate`).

## Why

Plan v2.0 (organic-first): solo escalamos a paid lo que ya demostró funcionar en orgánico. Los 6 ads son posts orgánicos publicados con WCI validado (4.4%–9.81%) subidos como carruseles independientes. La lógica de "no lanzar hasta que el funnel esté armado" protege el budget de $4K MXN contra leaks obvios (sin email = sin LTV; sin test purchase = sin señal de que el checkout no está roto).

## How to apply

- **Antes de dar GO:** verificar que los 4 bloqueos estén resueltos. No activar ads sin esto.
- **Para re-correr el script** (agregar ads nuevos, cambiar budget): el .env ya tiene todas las vars. `python hc_mes1_full_setup.py` es idempotent.
- **Kill criteria** (primera semana viva): CTR>1%, CPC<$8, Frec<2.5, Purchases>0 en 5 días. Si no, pausar y revisar hook/landing. Detalle en `PLAN_CAMPAÑA.md`.
- **Review semanal** (cada lunes): pausar 2 peores, dejar budget a top 4, considerar agregar videos Monse si están listos.
- **Quiz budget ($1,000 MXN reservado):** activar Semana 2 si los ads de conversión generan data. Campaña separada HC-QUIZ-LEADS.

## Archivos operativos relacionados

- `HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/00. ESTRATEGIA/PLAN_CAMPAÑA.md` — plan v2.0 con tabla de winners + kill criteria
- `HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/03. CHECKLIST/PRE_LANZAMIENTO.md` — checklist con 6 ads marcados como subidos
- `HC - HEALTHY CHUCHOS/HC_ESTRATEGIA_360_v1.md` — copy de los 4 email flows pendientes de activar
- `HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/01. ESTATICOS/O{1-6}_*/CAPTION.md` — copy fuente de los 6 ads
- `HC - HEALTHY CHUCHOS/_CLIENT_CONTEXT.md` — session 23 entry con detalle completo
