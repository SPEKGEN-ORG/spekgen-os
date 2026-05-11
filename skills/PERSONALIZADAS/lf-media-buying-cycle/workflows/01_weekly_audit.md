# Workflow 01 — Weekly audit (Lunes)

> Trigger: cada lunes 9 AM MX (cron `lf-monday-audit.yml` futuro).
> Output: 1 reporte estado cuenta + 0-N decisiones loggeadas + bandera de necesidades para resto de la semana.

---

## Objetivo

Snapshot semanal de la cuenta para:
1. Detectar saturación cuenta-nivel (CPMr alza, Freq quiebre, ROAS regresión)
2. Aplicar reglas de scaling (regla 20-72-8) sobre ads que califican
3. Decidir pausas (stop-loss canónico)
4. Setear agenda de la semana (¿hace falta refresh creative? ¿qué bucket pedir más?)

## Pre-flight

Cargar (orden estándar):
1. `_QUICK_REFERENCE.md`
2. `LOGS/LF/CALIBRATION.md`
3. `LOGS/LF/DECISIONS_LOG.md` (últimas 2 semanas)
4. `LOGS/LF/BATCH_LOG.md`
5. `LOGS/LF/MONTH_PLAN_MAY26.md`

## Procedimiento

### Paso 1 — Pull cuenta-nivel

```bash
python3 scripts/pull_meta_metrics.py --account-summary --days 7
python3 scripts/pull_meta_metrics.py --account-summary --days 30
```

Captura para cuenta:
- spend 7d / 30d
- ROAS 7d / 30d
- CPA 7d / 30d
- Frequency 7d
- CPMr 7d vs 30d (alza %)
- # ads activos

Compare contra calibración:
| Métrica | 7d real | Target Brain | Status |
|---|---|---|---|
| ROAS | X | ≥2.13× | 🟢/🟡/🔴 |
| CPA | $X | ≤$700 | 🟢/🟡/🔴 |
| Frequency | X | <2.5 | 🟢/🟡/🔴 |
| CPMr alza | X% | <30% | 🟢/🟡/🔴 |

### Paso 2 — Pull per-ad activos

```bash
python3 scripts/pull_meta_metrics.py --all-active --days 7
```

Para cada ad ACTIVO en cuenta, evaluar 4 reglas:

#### Regla A — Stop-loss canónico
Trigger: spend > 3× AOV target ($3,690) AND purchases < 2 AND CPA > 1.5× target ($1,050)
→ **PAUSA DEFINITIVA** + decisión D-NNN

#### Regla B — Reducir budget −30%
Trigger: CPA 7d > 1.25× target ($875)
→ Reducir adset daily_budget −30% + decisión D-NNN

#### Regla C — Escalar +20% (regla 20-72-8)
Trigger: ≥8 conv/día × 4 días consecutivos AND ROAS 7d sostenido ≥3× AND >72h desde último ajuste
→ Scaling +20% a las 12:00 AM hora local (programar manual o documentar para mañana) + decisión D-NNN

#### Regla D — Refresh creative (anti-amnesia)
Trigger: ad histórico rentable (>2.13× sostenido) ahora cae <breakeven AND Frequency >3.5 AND CPMr +60%
→ NO PAUSAR. Bandera para refresh creative en próximo batch (W+1). Loggear como "saturación detectada" + decisión D-NNN.

### Paso 3 — Anti-amnesia override check

Antes de aplicar Regla A (pausar), verificar:
- ¿Lifecycle previo del ad fue rentable? (BATCH_LOG block C 7d/14d)
- Si SÍ → es saturación, no loser nato → aplicar Regla D no A
- Si NO (siempre <breakeven desde día 1) → loser nato, OK pausar

### Paso 4 — Setear agenda semana

Output al final del audit: lista bullet de "necesidades del batch siguiente":

```
- [ ] Refresh: LF-XXX (saturado mes pasado, replicar concepto con nuevo Entity ID)
- [ ] Pause confirmation: LF-YYY (stop-loss aplicado lunes — dejar pausado)
- [ ] Iterate: LF-ZZZ (Hook OK, cuerpo falla — reescribir copy en próximo batch del bucket)
- [ ] Bucket bandera: PSS necesita +1 ad porque W1 mostró señal mixta
```

Esta lista alimenta workflow 03 (Brief batch) del miércoles.

### Paso 5 — Post audit deliverables

1. `LOGS/LF/AUDITS/audit_YYYY-MM-DD.md` — snapshot completo del lunes
2. `DECISIONS_LOG.md` — append D-NNN por cada acción ejecutada
3. Email cortito a Gibran (3-5 líneas, formato workflow 08)
4. Update `MONTH_PLAN_MAY26.md` si hay overrides necesarios

## Edge cases

- **Lunes lockdown weekend largo (puente)**: tratar como lunes normal pero notar en audit "datos contaminados por reduced spend Sat-Sun-Lun"
- **Cuenta sin ads activos** (transición entre batches): audit minimalista, foco en setup batch siguiente
- **Meta API down**: postponer audit hasta que vuelva, pero no demorar más de 24h

## Output template

```markdown
# LF Weekly Audit YYYY-MM-DD

## Cuenta-nivel
- Spend 7d: $X (vs target $2,310)  🟢
- ROAS 7d: Xx (vs target 2.5x)  🟡
- CPA 7d: $X (vs target $700)  🔴
- Frequency 7d: X  🟢
- CPMr alza: X%  🟢

## Decisiones tomadas
- D-NNN: ...
- D-MMM: ...

## Bandera para batch W+1
- [ ] ...
- [ ] ...

## Próximo audit: YYYY-MM-DD (lunes que viene)
```
