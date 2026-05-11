---
name: Make text:empty/notempty filter no matchea valores undefined
description: En Make, filtros text:empty y text:notempty NO matchean cuando el path resuelve a undefined (no string). Solución: envolver con ifempty() y comparar contra sentinel string.
type: feedback
originSessionId: 67a863d5-0a96-4359-a688-ea39c041bdec
---
Make's `text:empty` y `text:notempty` filter operators NO se evalúan correctamente cuando el path del campo resuelve a `undefined` (no string). El filtro es tratado como "no aplica" → la ruta entera se SKIPPEA, sin importar la dirección. Esto significa que un par de filtros opuestos (`text:notempty` + `text:empty`) sobre el mismo campo PUEDE saltarse AMBAS rutas si el campo no existe.

**Why:** Bug detectado 2026-05-07 en HC scenario 4780569 (HC - Pago Confirmado Almacén). Pedido #1037 corrió con response 518KB válido del edge function (con tracking_number presente como string), pero las dos rutas (success con `text:notempty` y fallback con `text:empty`) AMBAS se saltaron — solo 2 ops en lugar de 3. El equipo de almacén no recibió el correo con la guía. Test posterior con order_id=0 (response sin tracking_number) tampoco disparó el fallback.

**How to apply:**
- Cuando filtres en Make sobre un campo que viene de un módulo HTTP con `parseResponse:true`, NUNCA confíes en `text:empty/notempty` directamente sobre el path.
- En su lugar, envolver con `ifempty()` y un sentinel string: `{{ifempty(3.data.tracking_number; "__NO_TRACK__")}}` con operador `text:equal "__NO_TRACK__"` (fallback) o `text:notequal "__NO_TRACK__"` (success).
- Aplica especialmente a respuestas grandes con gzip+parseResponse, donde el behavior de Make es flaky.
- Pattern alternativo: usar `numeric:greaterthan 0` sobre `length(field)` también funciona, pero `ifempty+text:equal` es más legible.

Fix completo en HC 4780569 push 2026-05-07T21:05:27Z (commit equivalente: backup `_BACKEND_SUPABASE/make_backups/scenario_4780569_20260507-140103_pre_router_fix.json`). Validado E2E: ops=2 (bug) → ops=3 (fix) en test con order_id=0.
