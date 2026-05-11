---
name: Make scenarios_update requires full blueprint shape
description: scenarios_update requires name+flow+metadata+scheduling+interface; a blueprint with only flow+metadata returns 500 Internal Server Error even though validate_blueprint_schema rejects the full shape
type: feedback
originSessionId: 3a9fb5be-5b36-4397-870f-d6f45e992e8d
---
Make's MCP exposes two tools con comportamiento contradictorio:

- `validate_blueprint_schema` rechaza top-level keys extra (`name`, `scheduling`, `interface`) con error `"blueprint must NOT have additional properties"`. Solo acepta `flow` + `metadata`.
- `scenarios_update` REQUIERE los 5 keys (`name`, `flow`, `metadata`, `scheduling`, `interface`). Si mandas solo `flow` + `metadata` devuelve 500 Internal Server Error sin mensaje claro.

**Why:** Cost ~30 min de debugging en sesión 2026-04-20 actualizando scenario 4780569 (HC Pago Confirmado Almacén) a v5. Probé la versión "clean" (flow+metadata) que pasaba el validator pero fallaba en update. La versión con todos los keys pasó sin problema.

**How to apply:**
1. Skip `validate_blueprint_schema` si vas directo a update — el validator no refleja lo que el update endpoint acepta.
2. Para `scenarios_update`: siempre enviar la shape completa tal como la devuelve `scenarios_get` (name, flow, metadata, scheduling, interface).
3. Para debuggear errores del update: empezar con un test mínimo (reemplazar HTML gigante con `<html>test</html>`) para aislar si es tamaño o shape.
4. Para rollback: `scenarios_get` trae el blueprint completo en la shape correcta. Guarda el JSON como backup antes de cualquier update.
