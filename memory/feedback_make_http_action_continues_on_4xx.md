---
name: Make HTTP module v3 con handleErrors=false continúa flow aunque haya 4xx/5xx
description: HTTP `http:ActionSendData` v3 con `parameters.handleErrors=false` NO detiene el scenario en HTTP 4xx/5xx — los módulos siguientes corren con data parcial/vacía. Sólo un filter explícito en módulo siguiente impide ejecución.
type: feedback
originSessionId: 35260a28-0365-4b13-99d0-cb2bb8960ecf
---
**Comportamiento descubierto (HC pedido #1035, 2026-04-30):**

Make HTTP module `http:ActionSendData` v3 con `"handleErrors": false`:
- Si el HTTP devuelve 200 → módulos siguientes corren normal
- Si el HTTP devuelve 422/500/etc → **módulos siguientes TAMBIÉN corren** con data del response (vacía o parcial). NO detiene el flow.
- `handleErrors: true` lanzaría el scenario a "errored" y permitiría error handler routes, pero no es el default

**Caso real:** Make 4780569 HC pedido #1035 — edge function devolvió 422 (Skydropx rechazó dirección), Make siguió al módulo Gmail y mandó email "PAGO CONFIRMADO · GUÍA LISTA" con todos los campos en blanco (`{{3.data.tracking_number}}` resolvió a string vacío).

**Fix canónico:** poner filter en módulo siguiente con condición sobre un campo crítico del response:
```json
"filter": {
  "name": "Sólo si datos válidos",
  "conditions": [[
    {"a": "{{3.data.tracking_number}}", "o": "text:notempty"}
  ]]
}
```

Y agregar módulo paralelo con filter opuesto (`text:empty`) que dispare alerta a humanos cuando el campo no llegó.

**Regla de oro:** todo módulo HTTP en Make debe tener filter en el módulo siguiente que valide al menos un campo crítico del response. Nunca confiar en que `handleErrors:false` detiene el flow — no lo hace.

**Aplica a:** todos los scenarios SPEKGEN que llamen a edge functions / APIs externas (HC orders, GR bot, MG webhooks, etc). Auditar y agregar filters defensivos donde no existan.
