---
name: lf-media-buying-cycle
description: Operación 100% autónoma de Meta Ads para LO FITNESS. Encapsula el ciclo completo (audit → brief → upload → monitor → report) según Brain + AUTONOMY_RULEBOOK. Activa cuando Gibran diga "audita LF", "pull metrics LF", "qué pasó con los ads de LF", "reporte LF", "decide siguiente batch LF", "mes plan LF", "monitor LF", o cualquier operación de Meta Ads del cliente LO FITNESS. NO usar para production de creativos (esa es /factory-batch).
---

# LF — Media Buying Cycle

Skill de operación autónoma de Meta Ads para LO FITNESS. Cubre todo el ciclo del media buying *excepto* la producción de creativos (esa vive en `/factory-batch`).

## Cuándo invocar

- Auditoría semanal (lunes): `audita LF`, `qué tal van los ads`, `weekly audit LF`
- Pull de métricas: `pull 72h LF-066`, `metrics LF últimos 7d`, `cómo va LF-058 a 72h`
- Decisiones operativas: `pausa LF-NNN`, `escala LF-MMM +20%`, `refresh creative LF-XXX`
- Brief de batch nuevo: `brief week 2 LF`, `qué ads producir esta semana`, `commit batch LF`
- Reporte de status: `reporte LF`, `qué pasó esta semana`, `email a gibran`
- Plan mensual: `plan mes LF`, `mes plan junio`, `siguiente mes`

## NO invocar para

- Producir creativos (prompts SCALIST, generar imágenes) → `/factory-batch`
- Subir ads a Meta API ad-hoc → script directo o `/spekgen-meta-ads-upload`
- Cambiar landing page o pricing → fuera de scope (rulebook)

## Pre-flight obligatorio (siempre, sin excepción)

Antes de ejecutar cualquier acción, leer EN ORDEN:

1. `SPK - MEDIA BUYING OPS/_QUICK_REFERENCE.md` — thresholds operativos (regla 20-72-8, escalera Frequency, Hook Rate, etc.)
2. `SPK - MEDIA BUYING OPS/LOGS/LF/CALIBRATION.md` — números reales LF (AOV $1,230, breakeven $578/2.13×, target $700/2.5×)
3. `SPK - MEDIA BUYING OPS/LOGS/LF/DECISIONS_LOG.md` — anti-amnesia (qué se decidió antes y por qué)
4. `SPK - MEDIA BUYING OPS/LOGS/LF/AUTONOMY_RULEBOOK.md` — autoridad + kill switches
5. `SPK - MEDIA BUYING OPS/LOGS/LF/BATCH_LOG.md` — historial de ads producidos
6. `SPK - MEDIA BUYING OPS/LOGS/LF/MONTH_PLAN_MAY26.md` (o el del mes activo) — plan vigente

Si la acción toca pricing/bundles:
- Pull `lofitness.club/products.json` y comparar contra `LF - 02. PRODUCTOS/00. PRODUCT LOG GLOBAL/LF_PRICING_REFERENCE.xlsx`
- Si hay gap → re-snapshot xlsx → registrar en `VALIDATION_LOG`

## Workflows disponibles (v0.2 — todos documentados)

Cada workflow es un procedure documentado en `workflows/`. Leer el específico antes de ejecutar.

| Workflow | Cuándo | Doc |
|---|---|---|
| Weekly audit | Lunes 9 AM MX | `workflows/01_weekly_audit.md` ✅ |
| VoC mining | Martes 10 AM MX | `workflows/02_voc_mining.md` ✅ |
| Brief batch | Miércoles 10 AM MX | `workflows/03_brief_batch.md` ✅ |
| QA pre-upload | Jueves (post images ready) | `workflows/04_qa_pre_upload.md` ✅ |
| Friday upload + activate | Viernes 10 AM MX | `workflows/05_friday_upload.md` ✅ |
| Pull 72h post-launch | 3d post-batch | `workflows/06_pull_72h.md` ✅ |
| Pull 7d post-launch | 7d post-batch | `workflows/07_pull_7d.md` ✅ |
| Send 3-day report | Cron cada 3 días | `workflows/08_send_report.md` ✅ |
| Monthly plan | Primer lunes del mes | `workflows/09_monthly_plan.md` ✅ |

> **Próximo paso de evolución:** GH Actions cron jobs (Japan-proof) que disparen los workflows cron-based (06, 07, 08, 01). Pendiente de sesión dedicada — necesita git repo + secrets + email config.

## Cadencia operativa estándar

```
LUN  workflows/01_weekly_audit          → audit + decisiones (pausas/scaling/kills)
MAR  workflows/02_voc_mining            → VoC + 2-3 ángulos PDA nuevos para próximo batch
MIÉ  workflows/03_brief_batch           → brief de batch siguiente (no genera, solo conceptualiza)
JUE  workflows/04_qa_pre_upload         → QA images + EMQ audit (cuando hay batch en cola)
VIE  workflows/05_friday_upload         → upload + activación + horizontal scaling
SÁB-DOM  LOCKDOWN — sin edits
```

Workflows trigger por evento (no día):
- 72h post-batch → `workflows/06_pull_72h`
- 7d post-batch → `workflows/07_pull_7d`
- Cron cada 3 días → `workflows/08_send_report`
- Primer lunes del mes → `workflows/09_monthly_plan`

## Scripts disponibles (`scripts/`)

| Script | Propósito | Inputs | Output |
|---|---|---|---|
| `pull_meta_metrics.py` | Pulls per-ad metrics last N days from Meta Marketing API | `--days N --ad-ids x,y,z` o `--all-active` | JSON + tabla markdown |

(Más scripts irán llegando: `audit_account.py`, `commit_decision.py`, `send_report.py`, `activate_cascade.py`)

## Logging obligatorio post-acción

Toda acción ejecutada se loguea append-only en el doc apropiado:

| Acción | Loguear en |
|---|---|
| Decisión Meta (pausa/scale/refresh) | `LOGS/LF/DECISIONS_LOG.md` (formato D-NNN canónico) |
| Calibración nueva que contradiga Brain | `LOGS/LF/CALIBRATION.md` |
| Patrón aprendido cross-batch | `LOGS/LF/PROMPT_PATTERNS_LF.md` (síntesis 7d) |
| Pricing pre-flight realizado | `LF_PRICING_REFERENCE.xlsx` hoja `VALIDATION_LOG` |
| Plan mensual ajustado | `LOGS/LF/MONTH_PLAN_{MMMYY}.md` (override section) |
| Reporte enviado | append a `LOGS/LF/REPORTS/` con copia HTML |

## Autoridad operativa (resumen del rulebook)

| Acción | Sin permiso? |
|---|---|
| Pausar ad por stop-loss canónico | ✅ |
| Escalar +20% (regla 20-72-8) | ✅ |
| Crear nuevos ads dentro del split | ✅ |
| Lanzar concepto nuevo fuera del split | ✅ (loggeo) |
| Subir budget cuenta arriba de $333/d | ✅ (loggeo) |
| Pausar TODA la cuenta | ❌ email a Gibran |
| Cambiar landing/pricing en Shopify | ❌ NUNCA |

Detalle completo: `LOGS/LF/AUTONOMY_RULEBOOK.md`.

## Versión

- `v0.1` — 2026-05-06 — Skeleton inicial. Workflows 01 + 06 + script `pull_meta_metrics.py`.
- `v0.2` — 2026-05-06 — Todos los 9 workflows documentados (02-09 added). Próximo: GH Actions cron Japan-proof.
