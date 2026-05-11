# Make `scenarios_update` puede congelar el cron `indefinitely`

**Descubierto:** 2026-05-02 (HC Abandoned Cart Scheduler stuck 22h tras F-RECORDER-DEDUPE)

## Bug

Cuando se ejecuta `scenarios_update` (vía MCP o API REST) sobre un scenario activo con `scheduling.type=indefinitely`, Make recalcula incorrectamente el `nextExec`. En vez de ser `now + interval`, lo programa muy lejos en el futuro (observado: 22-28 horas después en lugar de 15 minutos). El cron queda freezado durante ese gap aunque blueprint sea válido.

## Síntoma

- `scenarios_get` retorna: `isActive:true`, `isPaused:false`, `isinvalid:false`, blueprint OK
- Pero `executions_list` muestra que NO hay ejecuciones automáticas durante muchas horas
- `nextExec` field tiene timestamp lejano (no `now + interval`)
- Records que deberían procesar quedan stuck

Caso real HC: F-RECORDER-DEDUPE hizo `scenarios_update` al Scheduler 4845938 (cambio limit 100→500) el 2026-05-01 16:22 UTC. Última ejecución auto fue 15:33 UTC (49min antes del modify). Después: 0 ejecuciones durante 22h. `nextExec` quedó en 2026-05-02 21:18 UTC. Resultado: leo0857cgjj y bovdikagrig stuck en M1 con age 27h cuando debían estar en M2.

## Fix

Después de cualquier `scenarios_update` a scenario con cron `indefinitely`, ejecutar:

```
scenarios_deactivate(scenarioId)
scenarios_activate(scenarioId)
```

Esto fuerza a Make a recalcular `nextExec` correctamente desde `now`. Cron retoma ritmo normal (próxima ejecución dentro de `interval`).

## SOP nuevo

**Patrón obligatorio cuando modifiques cualquier scenario Make con cron:**

1. `scenarios_get` (capture current state)
2. Backup blueprint a archivo
3. `scenarios_update` (apply changes)
4. **`scenarios_deactivate` + `scenarios_activate`** ← step crítico
5. `scenarios_run` (manual trigger para confirmar funciona)
6. `executions_list` (verificar se ejecutó)

Sin step 4, posible que el scenario quede freezado por horas hasta el próximo `nextExec` calculado mal.

## Patrón relacionado

Similar a `feedback_make_isinvalid_stale_flag.md`: un push válido NO siempre limpia flags/timestamps stale dejados por estados previos. Make tiene varios lugares donde el state interno puede divergir del blueprint declarado.

## Tooling

- MCP `mcp__18578e46-...__scenarios_deactivate` y `scenarios_activate` están disponibles
- Si MCP no está disponible, REST API: `POST /api/v2/scenarios/{id}/deactivate` y `POST /api/v2/scenarios/{id}/activate` con header `Authorization: Token <MAKE_API_TOKEN>`
