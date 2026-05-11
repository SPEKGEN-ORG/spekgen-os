# Workflow 06 — Pull 72h post-launch

> Trigger: 72 horas después de activar un batch nuevo.
> Para BATCH_LF_2026-05-05-v1: ejecutar **2026-05-09 (jueves) ~9 AM MX**.
> Output: tabla markdown + decisión por ad (continuar / iterar / pausar).

---

## Objetivo

Confirmar señales Layer 1 del Brain §5 sobre los ads nuevos:

| Métrica | Threshold OK |
|---|---|
| Hook Rate (3s/Imp) | ≥ 20% |
| Hold Rate (15s/3s) | ≥ 15% |
| CTR (link) | ≥ 2% |
| Frequency 7d | < 2.5 |
| CPMr | < $340 MXN |

Si los 5 cuadran → ad pasa Layer 1, sigue corriendo. Si alguno falla → diagnóstico (ver decisión más abajo).

## Pre-flight

Cargar (orden):
1. `_QUICK_REFERENCE.md` — thresholds
2. `LOGS/LF/CALIBRATION.md` — números reales LF
3. `LOGS/LF/DECISIONS_LOG.md` — historia
4. `LOGS/LF/BATCH_LOG.md` — qué ads están corriendo
5. `LOGS/LF/MONTH_PLAN_MAY26.md` — plan vigente para entender contexto del batch

## Procedimiento

### Paso 1 — Pull data

Usar `scripts/pull_meta_metrics.py`:

```bash
python3 scripts/pull_meta_metrics.py --days 3 --batch BATCH_LF_2026-05-05-v1
```

Output: `LOGS/LF/PULLS/72h_YYYY-MM-DD.json` + tabla markdown impresa.

### Paso 2 — Evaluar Layer 1 por ad

Para cada ad activo, llenar:

| ad_code | spend | impr | freq | hook | hold | CTR | CPM | purch | ROAS | Layer 1 verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| LF-058 | $X | X | X | X% | X% | X% | $X | X | Xx | OK / FALLA |

**Verdict rules:**
- 5/5 thresholds → `OK CONTINUAR`
- Hook<15% AND CTR<1% → `FALLA TERMINAL → PAUSAR + iterar visual` (loser nato)
- Hook≥20% pero CTR<1% → `HOOK OK CUERPO FALLA → reescribir guion (no hook)`
- CPMr alto + Freq<2 → `EXPANSIÓN OK aún temprana — esperar 7d`
- Freq>3 a 72h → `velocidad fuera de regla — escalado natural anormal, investigar`

### Paso 3 — Decidir & loggear

Para cada ad con verdict ≠ "OK CONTINUAR":

1. Anti-amnesia check: ¿es saturación de creative previo o loser nato? (Brain §5)
2. Aplicar regla apropiada:
   - Loser nato: pausar
   - Saturación sospechada: dejar correr 48h más (a menos que stop-loss canónico)
   - Hook fail: bandera para refresh visual en próximo batch
   - Cuerpo fail: bandera para reescribir copy
3. Append decisión a `DECISIONS_LOG.md` formato D-NNN

### Paso 4 — Implicación para batch siguiente

Update `MONTH_PLAN_MAY26.md` sección "Reglas de override":
- Si bucket falla en W1 → próximo batch NO escala ese bucket
- Si bucket arrasa (≥3× ROAS) → próximo batch dobla iteraciones del concepto ganador
- Si producto X falla específicamente → ese SKU sale del split por 2 semanas

### Paso 5 — Output a Gibran

Email cortito (3-5 líneas) con:
- Headline: spend cuenta 72h vs target
- Top performer (ad_code + ROAS + acción sugerida)
- Worst performer (ad_code + razón + acción tomada)
- Implicación para week 2 brief
- Link al pull JSON completo

## Output esperado

1. `LOGS/LF/PULLS/72h_YYYY-MM-DD.json` (raw data)
2. `LOGS/LF/PULLS/72h_YYYY-MM-DD.md` (tabla evaluada)
3. Append a `DECISIONS_LOG.md` (1+ entradas D-NNN)
4. Append a `BATCH_LOG.md` block C de cada ad (métricas 72h capturadas)
5. Email a Gibran (template `templates/report_email_72h.html` cuando exista)

## Edge cases

- **<10 conv totales en 72h**: data insuficiente para Layer 2, pero Layer 1 (Hook/CTR/Freq) sí se puede leer. Reportar pero NO tomar decisión de pause.
- **CBO arbitró todo a 1 ad**: revisar si floor `daily_min_spend_target` está respetando — si no, bandera para subir floor en `DECISIONS_LOG`.
- **Meta API down/timeout**: reintentar 3× con backoff. Si sigue, postponer pull 6h y email a Gibran "pull retrasado por API issue".

## Próxima ejecución scheduled

Para BATCH_LF_2026-05-05-v1: **2026-05-09 jueves ~9 AM MX**.
