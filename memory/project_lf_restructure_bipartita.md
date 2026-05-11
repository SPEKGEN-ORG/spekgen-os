---
name: LF Restructura Bipartita Tier 2 (2026-05-05)
description: LF migrado a Brain §4 Bipartita. LF-SCALE-MAY26 + LF-TESTING-MAY26 con 4 ad sets ABO. Anti-amnesia rule activa. 8 ads pre-built en factory-batch esperando billing Gemini.
type: project
originSessionId: e2cf76d9-4172-48bd-9eab-e9a8e19feebb
---
## Path operativo
`SPK - SPEKGEN AGENCY/SPK - MEDIA BUYING OPS/LOGS/LF/`

## Estructura Meta nueva (2026-05-05, todo PAUSED esperando activación)

| ID | Nombre | Detalle |
|---|---|---|
| `120244794376200731` | **LF-SCALE-MAY26** | Sales CBO $230/día (70% budget) — recibe ads graduados |
| `120244794377170731` | LF_SCALE_BROAD_MX_25-65 | Ad set BROAD MX 25-65 con LF-057 dentro |
| `120244794415340731` | LF-057_KIT_LUPITA_SCALE | Clone con IG enabled (creative `1694489988398948`) |
| `120244794415860731` | **LF-TESTING-MAY26** | Sales CBO $100/día (30% budget) |
| `120244794416320731` | LF_TEST_A_KIT_OFFERS | Ad set ABO min daily $20 |
| `120244794420430731` | LF_TEST_B_PROBLEM_SOLUTION | Ad set ABO min daily $20 |
| `120244794420800731` | LF_TEST_C_LUPITA_AUTHORITY | Ad set ABO min daily $20 |
| `120244794421490731` | LF_TEST_D_WILDCARDS | Ad set ABO min daily $20 |

**Pausados:** LF-VENTAS-ABR26 (campaign `120243602635060731`) + LF-056 + LF-057 viejo.

## Calibración real LF (verificada 2026-05-05)

| Métrica | Valor |
|---|---|
| Budget MAX | $10,000 MXN/mes ($333/día) — orden Gibran |
| AOV operacional 30d | $1,230 MXN |
| Mc% asumido | 47% (pendiente confirmar COGS) |
| Breakeven CPA | $578 MXN |
| Breakeven ROAS | 2.13× |
| CPA target operacional | $700 MXN |
| ROAS target | 2.5× |
| Pre-restructura ROAS 30d | 0.69× (32% del breakeven — hemorrágica) |

## 8 ads pre-built (BATCH_LF_2026-05-05-v1)

`SPK - 15. FACTORY/ads/LF/2026-05/BATCH_LF_2026-05-05-v1/`

| Ad | Bucket | Producto | Destination ad set |
|---|---|---|---|
| LF-058 KIT_TRIO_LUPITA_RUTINA_AM | LUPITA+OFFER | Kit Trío Esencial $1,077 | C_LUPITA_AUTHORITY |
| LF-059 FITMAX_2PACK_HORMOZI_LUPITA | LUPITA+OFFER | Pack 2 Fit Max $1,076.40 | A_KIT_OFFERS |
| LF-060 METAFIT_2PACK_REFRESH | OFFER puro | Pack 2 MetaFIT $896.40 | A_KIT_OFFERS |
| LF-061 KIT_DUO_MINERAL_LUPITA | LUPITA+OFFER | Kit Dúo Mg+K $700 | C_LUPITA_AUTHORITY |
| LF-062 MAGNESIO_CALAMBRES_PSS | PROBLEM-SOLUTION | Citrato Magnesio $389 | B_PROBLEM_SOLUTION |
| LF-063 METAFIT_NO_BAJO_PESO_PSS | PROBLEM-SOLUTION | Activer MetaFIT $498 | B_PROBLEM_SOLUTION |
| LF-064 OMEGA3_INFLAMACION_LUPITA | LUPITA+AUTHORITY | Omega 3 $489 | C_LUPITA_AUTHORITY |
| LF-065 FITMAX_SNEAKY_HOOK | WILDCARD | Fit Max iMessage mock | D_WILDCARDS |

Server local en :8766 (`lf-batch-dashboard` en `.claude/launch.json`). URL: http://127.0.0.1:8766/dashboard.html

## Mix creativo mensual aprobado (30 ads contractuales)

- 50% OFFER (con/sin Lupita)
- 27% LUPITA+AUTHORITY
- 13% PROBLEM-SOLUTION refinado (con offer fix)
- 10% WILDCARDS (ratio 70/30 Brain)

## Bloqueador activo

- **Gemini billing:** Mastercard 9064 declined → balance pendiente MX$413.13 → API tier "Unavailable"
- Cuenta correcta: `metagreenlabs@gmail.com` PRO, proyecto `calm-cab-493723-k7`
- Fix: https://console.cloud.google.com/billing/01B994-F85F4D-BA7183/payment?authuser=3 → Make a payment + Add backup
- Doc: `LOGS/LF/BLOCKER_2026-05-05_gemini_billing.md`

## Estado 2026-05-06 — Bipartita Tier 2 LIVE

**7 ads UPLOADED + ACTIVE** (1 dropped: LF-065 wildcard rechazado por Gibran):

| Ad | Bucket | Adset | Meta ad_id |
|---|---|---|---|
| LF-058 | LUPITA+OFFER | C_LUPITA_AUTHORITY | 120244843921000731 |
| LF-059 | LUPITA+OFFER | A_KIT_OFFERS | 120244843922340731 |
| LF-060 | OFFER puro | A_KIT_OFFERS | 120244843924350731 |
| LF-061 | LUPITA+OFFER | C_LUPITA_AUTHORITY | 120244843925500731 |
| LF-062 | PSS | B_PROBLEM_SOLUTION | 120244843926020731 |
| LF-063 | PSS | B_PROBLEM_SOLUTION | 120244843926770731 (winner visual 9.0/10, v2 reprompt asimétrico type-forward) |
| LF-064 | LUPITA+AUTH | C_LUPITA_AUTHORITY | 120244843927790731 |

**Estructura activa:**
- LF-SCALE-MAY26 ($230/d) → LF-057 clone
- LF-TESTING-MAY26 ($100/d) → 3 adsets ACTIVE (A/B/C). D_WILDCARDS PAUSED (sin ads)
- Total: $330/d (~$9,900/mo dentro de target $10K)

**Calibración D-010:** floor `daily_min_spend_target` 4 adsets bajado de $20→$10 por error 1885648 "Min Spend > Campaign Budget". 4×$20=$80 vs $100 budget = sin headroom CBO. Floor $10 da 60% headroom.

**Próximo paso:**
1. Reporte 72h: 2026-05-09 (jueves) — capturar Hook/CTR/Freq de Layer 1
2. Reporte 7d: 2026-05-13 — Layer 2 evaluation + posibles graduaciones a SCALE
3. LF-066+ próximo batch (Web UI o API según billing) — incluye reemplazo wildcard concept
4. GH Actions cron (lf-monday-audit / wed-generate / fri-upload) + reporte cada 3d post-Japón

**Recap PDF:** `BATCH_LF_2026-05-05-v1/BATCH_LF_2026-05-05-v1_recap.pdf`

## Sistema de aprendizaje de prompts (creado 2026-05-06)

Doc internos de Claude (Gibran no abre):
- `LOGS/LF/BATCH_LOG.md` — pre-poblado con 8 entradas (bloque A). Bloques B/C se llenan al generar+lanzar.
- `LOGS/LF/PROMPT_PATTERNS_LF.md` — síntesis cross-batch cada 7d. Trackea magic words, anti-patterns, validación de hipótesis.
- `LOGS/LF/AUTONOMY_RULEBOOK.md` — autoridad + cadencia + kill switches + reporte. Acordado 2026-05-06.

Pre-flight de pricing centralizado:
- `LF - 02. PRODUCTOS/00. PRODUCT LOG GLOBAL/LF_PRICING_REFERENCE.xlsx`
  - Sheet SINGLES_WITH_PACKS: 18 productos con Pack 2 (10% off) + Pack 4 (15% off) precomputados
  - Sheet KITS: 5 kits con compare_at + ahorra
  - Sheet VALIDATION_LOG: snapshot por batch validado
  - Mecánica universal confirmada por Gibran: Pack 2 = single×2×0.9 / Pack 4 = single×4×0.85
  - Stock alerts auto: Oceane / Fitbar / Hidronex / PH Detox AGOTADOS

## Autonomy authority (2026-05-06)

Full operational control para Claude EXCEPTO:
- Pausar TODA la cuenta (kill switch global) → email obligatorio
- Cambiar landing page o pricing → NUNCA

Resto puede ejecutar autónomo: pausar ads, escalar, crear nuevos, mover a SCALE, lanzar conceptos fuera del split, subir budget arriba de $333/d. Loggeo append-only en DECISIONS_LOG.

## Sistema 3 Layers de evaluación (Brain §5 baked-in)

```
LAYER 1 (días 1-5):  Hook≥20% AND CTR≥2% AND Freq<2.5 → continúa
LAYER 2 (≥2×CPA + ≥10 conv):  ROAS≥2.13× 7d → GRADUATE; <1.0× → KILL
LAYER 3 (≥30 días):  MER cuadra → confirmado winner → escalar 20-72-8
```

## Anti-amnesia rule (universal en hooks CLAUDE.md)

Antes de pausar: saturación (rentable→degradado) → refresh creative + horizontal scaling, NO pause definitivo. Loser nato (siempre <breakeven) → pause OK.

## Validación hipótesis Gibran "Lupita+oferta funciona mejor"

Parcialmente correcta (data 30d):
- LUPITA+OFFER: 1.30× ROAS (1 ad — N=1 sample chico, NO confirma)
- OFFER (sin Lupita): 1.15× ROAS (3 ads — confirmado bucket #1)
- LUPITA solo: 0.72× (8 ads — sin offer NO convierte)
- TODOS bajo breakeven 2.13× — mes pasado fue malo en general

Implicación: doble down OFFER + validar Lupita+Offer con N≥3 (cubierto en LF-058, LF-059, LF-061).
