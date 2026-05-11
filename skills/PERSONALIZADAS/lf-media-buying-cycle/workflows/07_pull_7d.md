# Workflow 07 — Pull 7d post-launch

> Trigger: 7 días después de activar un batch. Para BATCH_LF_2026-05-05-v1: ejecutar **2026-05-13 (lunes) ~9 AM MX**.
> Output: Layer 2 evaluation + decisiones de graduación a SCALE / kills definitivos / iteraciones.

---

## Objetivo

Aplicar Brain §5 Layer 2 sobre los ads del batch. Es el momento de tomar decisiones DURAS:
- Ads que cumplen → graduate a SCALE (mover de TESTING a SCALE adset)
- Ads que claramente no → KILL definitivo (PAUSE permanent)
- Ads en zona gris → ITERATE (refresh creative para próximo batch)

## Pre-flight

Cargar (orden estándar):
1. `_QUICK_REFERENCE.md`
2. `LOGS/LF/CALIBRATION.md`
3. `LOGS/LF/DECISIONS_LOG.md`
4. `LOGS/LF/BATCH_LOG.md`
5. `LOGS/LF/PULLS/72h_*.md` — comparar 72h vs 7d para detectar trayectoria

## Layer 2 thresholds (LF calibrado)

| Métrica | Threshold |
|---|---|
| Conversiones reales | ≥ 10 (statistical floor) |
| ROAS sostenido 7d | ≥ 2.13× (breakeven LF) |
| CPA 7d | ≤ $700 (target) |
| Frequency 7d | < 4.0 (Brain) |
| Spend acumulado | ≥ 2-3× CPA target ($1,400-$2,100) |

**OK GRADUATE A SCALE**: ROAS ≥ 2.5× sostenido + ≥10 conv + Frequency < 3.5
**OK CONTINUAR EN TESTING**: ROAS 2.13–2.49× + ≥5 conv + Frequency < 3.5
**ITERATE (refresh)**: ROAS <2.13× pero Hook/CTR/Hold ≥ Layer 1 OK (problema de oferta no de hook)
**KILL DEFINITIVO**: ROAS <1.0× con ≥10 conv → loser nato

## Procedimiento

### Paso 1 — Pull data

```bash
python3 scripts/pull_meta_metrics.py --days 7 --batch BATCH_LF_2026-05-05-v1
```

Output: `LOGS/LF/PULLS/7d_BATCH_LF_2026-05-05-v1_{timestamp}.json` + tabla markdown.

### Paso 2 — Evaluar Layer 2 por ad

Para cada ad activo, llenar tabla:

| ad_code | spend | conv | ROAS | CPA | Freq | Verdict |
|---|---|---|---|---|---|---|
| LF-058 | $X | X | Xx | $X | X | GRADUATE / CONTINUE / ITERATE / KILL |

### Paso 3 — Anti-amnesia check antes de KILL

Para cada candidato a KILL (ROAS <1.0× con conv suficientes):
- Lifecycle: ¿el ad fue rentable en algún momento (72h Layer 1 OK pero degrade a 7d)?
- Si sí → es saturación de Entity ID, no loser nato → ITERATE no KILL (refresh creative en próximo batch con mismo concept_angle pero distinto entity_id_signature)
- Si no (siempre <breakeven desde día 1) → KILL OK, loser nato

### Paso 4 — Ejecutar acciones

**GRADUATE**:
- Mover ad de TESTING adset a SCALE adset (o crear copia en SCALE adset, dejar original en TESTING para overlap 48h)
- Update budget SCALE +20% (regla 20-72-8) si cumple criterios de scaling
- Append D-NNN: `GRADUATE LF-NNN to SCALE — ROAS Xx 7d sostenido, +20% budget aplicado`

**ITERATE**:
- NO pausar el ad (puede seguir corriendo mientras genera data)
- Bandera para próximo brief workflow 03: refresh creative del concepto con nuevo Entity ID
- Append D-NNN: `ITERATE LF-NNN — ROAS Xx insuficiente, refresh creative en próximo batch`

**KILL DEFINITIVO**:
- PAUSE el ad
- Append D-NNN con anti-amnesia confirmation
- Bucket bandera para próximo brief: NO replicar este concept_angle

**CONTINUE**:
- Sin acción, dejar correr
- Re-evaluar workflow 07 próxima ejecución (7d adicional)

### Paso 5 — Update PROMPT_PATTERNS_LF.md (síntesis)

Cada 7d (post Layer 2), update `PROMPT_PATTERNS_LF.md` con learnings:
- Patrones que correlacionan con ROAS ≥ breakeven (con N≥3 ads)
- Anti-patterns documentados (con razón confirmada de fail)
- Validación o falsificación de hipótesis activas (ej. "Lupita+Offer >Lupita sola")
- Magic words que correlacionan con score realism alto

### Paso 6 — Update MONTH_PLAN

Si las graduaciones/kills cambian el mix planeado de las semanas siguientes, update `MONTH_PLAN_MAY26.md` sección Overrides.

### Paso 7 — Update BATCH_LOG bloque C

```bash
python3 /path/to/factory-batch/scripts/generate_batch_log.py {batch_dir} --block ABC
```

Métricas 7d capturadas en `batch.json` antes (paso 1) → BATCH_LOG actualiza automático.

## Output esperado

1. `LOGS/LF/PULLS/7d_BATCH_NNN_YYYY-MM-DD.md` (tabla evaluada)
2. N x append a `DECISIONS_LOG.md` (graduaciones/kills/iters)
3. Update `BATCH_LOG.md` bloque C
4. Update `PROMPT_PATTERNS_LF.md` (learnings cross-batch)
5. Update `MONTH_PLAN.md` Overrides si aplica
6. Email handoff a Gibran (workflow 08)

## Próxima ejecución

7d siempre desde fecha de upload. Para BATCH_LF_2026-05-05-v1 (uploaded 2026-05-06): **2026-05-13 (lunes) ~9 AM MX**.
