# Workflow 09 — Monthly plan (primer lunes del mes)

> Trigger: primer lunes de cada mes ~10 AM MX.
> Output: `LOGS/LF/MONTH_PLAN_{MMM_YY}.md` con 30 ads contractuales mapeados a weeks 1-4.

---

## Objetivo

Crear el plan operativo mensual: 30 ads/mes contractuales mapeados a (ad_code → producto → bucket → adset → hipótesis) por semana. **Reemplaza al MONTH_PLAN del mes anterior** (que ya cumplió su función).

## Pre-flight

Cargar:
1. `_QUICK_REFERENCE.md`
2. `LOGS/LF/CALIBRATION.md` — calibración actualizada del mes pasado
3. `LOGS/LF/DECISIONS_LOG.md` — winners/losers del mes pasado
4. `LOGS/LF/BATCH_LOG.md` — historial completo
5. `LOGS/LF/PROMPT_PATTERNS_LF.md` — learnings cross-batch consolidados
6. `LOGS/LF/MONTH_PLAN_{mes_pasado}.md` — qué se cumplió, qué quedó pendiente
7. `LOGS/LF/REPORTS/` — últimos 3 reports (status cuenta)
8. Catálogo Shopify live (productos disponibles, stock)

## Procedimiento

### Paso 1 — Recap mes pasado

Calcular del mes que termina:
- Total ads producidos vs 30 contractuales (cumplimiento %)
- Ads por bucket (vs split target 50/27/13/10)
- Top 5 winners (ROAS más alto sostenido)
- Bottom 5 (kills + iteraciones que fallaron)
- Cuenta-nivel: spend / ROAS promedio / CPA promedio / mejor semana / peor semana

Append a `LOGS/LF/MONTH_RECAP_{mes_pasado}.md`.

### Paso 2 — Resolver ajustes al split

Default split: 50% OFFER + 27% LUPITA+AUTH + 13% PSS + 10% WILDCARDS.

Override si data del mes pasado lo indica:
- Bucket dominante (ROAS >3× sostenido) → +5% del split, restar de bucket que perdió dinero
- Bucket fail (ROAS <breakeven con N≥5) → −5%, distribuir a winners
- WILDCARDS siempre mantener mínimo 2 (volumen para descubrir nuevos formatos)

Brain §3 dice: bajo Andromeda 2026 la creatividad es la segmentación → más volumen creativo > mejor segmentación.

### Paso 3 — Resolver productos en juego

Pull live `lofitness.club/products.json`. Para el mes:
- Productos `available=True` con stock saludable: candidatos
- Productos winners mes pasado (top sellers + top ROAS): priorizar para Pack 4 / kits
- Productos NUEVOS (lanzamiento): asignar 2 ads para test inicial
- Cosméticos: minimum 2 ads/mes (mantener categoría viva)
- AGOTADOS o low-stock: excluir explícitamente

### Paso 4 — Mapear 30 ads a weeks

Distribución default 7-8 ads/semana:
- Week 1: 7 ads, mix sample (1 por bucket + 2-3 OFFER)
- Week 2: 7 ads, fill gaps + replicate winners de Week 1 si Layer 1 OK
- Week 3: 8 ads, scale winners + introducir cosméticos
- Week 4: 8 ads, finalizar split + 1-2 wildcards

Para cada ad: ad_code (siguiente número), producto, bucket, adset destino, hipótesis testeable, cierre de gap (qué falta cumplir del split).

### Paso 5 — Identificar productos OUT-of-scope

Productos que NO entran al mes:
- AOV bajo (<$200) — ROAS unitario imposible bajo CPA target
- Out-of-stock confirmado
- Productos en pause estratégico (mensaje legal, COFEPRIS issue, etc.)
- Pricing tier alto (>$3K) sin ad set TOFU adecuado

Loggear out-of-scope con razón.

### Paso 6 — Reglas de override del plan

Documentar las 4-5 condiciones que sobrescriben el plan mid-month:
- Layer 1 (72h) detecta loser → bucket no escala
- Layer 2 (7d) detecta winner ROAS ≥3× → escalar inmediato + doblar iteraciones
- Stockout / pricing change → reemplaza producto en su slot
- CPM cuenta sostenido alto → pausa total + refresh estratégico

### Paso 7 — Render `MONTH_PLAN_{MMM_YY}.md`

Template (basarse en `MONTH_PLAN_MAY26.md` como referencia canónica):
- Header con recap mes pasado + decisiones tomadas
- Tabla split mensual (target vs distribución)
- 4 secciones (Week 1, 2, 3, 4) con tabla de ads
- Tally final por bucket
- Cosméticos coverage
- Reglas de override
- Productos out-of-scope con razón

Path: `LOGS/LF/MONTH_PLAN_{MMM_YY}.md` (ej. `MONTH_PLAN_JUN26.md`).

### Paso 8 — Email a Gibran

Resumen 1-página del plan mensual (no el plan completo, eso vive en MD). Incluye:
- Total ads + spend planeado
- Top 5 hipótesis del mes
- Cosméticos timeline
- Pregunta puntual si hay decisiones de override (ej. "split ajustado a 55/22/13/10 por mes pasado — confirma?")

## Edge cases

- **Mes con festivos / Buen Fin / Black Friday**: agregar 5-8 ads extra para campaña promocional (fuera del 30 base). Loggear como "Festividad N: ads extra"
- **Lanzamiento producto nuevo mid-month**: reservar 2-3 slots de week 3-4 para el nuevo producto
- **Decisión estratégica de Gibran (ej. pivot a TikTok Ads)**: postpone planning hasta nuevo brief estratégico

## Output esperado

1. `LOGS/LF/MONTH_PLAN_{MMM_YY}.md` (plan completo)
2. `LOGS/LF/MONTH_RECAP_{mes_pasado}.md` (recap del cierre)
3. Email a Gibran con resumen + pregunta puntual si aplica
4. Append a `DECISIONS_LOG.md`: `D-NNN: MONTH_PLAN {MMM_YY} aprobado, split X/Y/Z/W, 30 ads mapeados`
