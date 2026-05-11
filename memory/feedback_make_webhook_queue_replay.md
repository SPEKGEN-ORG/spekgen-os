---
name: Make webhook queue drains on reactivation
description: Deactivated Make scenarios still queue webhook POSTs; activating replays the queue and duplicates non-idempotent downstream actions
type: feedback
originSessionId: fe847294-aee0-4b1d-aa8e-06d249f50d38
---
Make webhook endpoints aceptan y encolan POSTs aunque el scenario esté `isActive:false` / `isinvalid:true`. Al llamar `scenarios_activate`, Make replayea TODA la cola acumulada en paralelo.

**Why:** Bug de triple-posteo HC-024 (2026-04-21). Scenario 4706750 desactivado 2 días, Gibran clickeó "Aprobar" múltiples veces en ese período (cola acumulada). Al reactivar, la cola disparó 2 executions concurrentes a `publish-now`; además yo llamé curl directo después sin checar executions. Resultado: 3 publicaciones en IG + 3 en FB que Gibran tuvo que borrar manualmente.

**How to apply:**
1. **Antes de reactivar un scenario de webhook no-idempotente**, checar `executions_list` y `get` del webhook (si se puede) para ver cuántos eventos están en cola.
2. **Para scenarios que hacen acciones no-reversibles** (publicar a IG/FB, enviar emails, cobrar, etc.) considerar:
   - Agregar filter al inicio que descarte events older than N minutes (usando `{{now}}` - `{{timestamp}}`)
   - Borrar la cola antes de activar (desde Make UI: hook settings → queue → purge)
   - O cambiar a trigger tipo scheduled con data store, no webhook
3. **Nunca invocar manualmente la acción downstream (curl/script)** después de reactivar sin antes confirmar que la cola drenó limpio vía `executions_list`.
4. **Hacer el endpoint downstream idempotente cuando sea posible**: check-and-set atómico en Shopify (ej. `metaobjectUpdate` con guard: solo si status actual != 'published'/'publishing'). La función `publish-now` actualmente toma lock `status=publishing` pero no es atomic — dos llamadas en paralelo hacen lock casi simultáneo.
