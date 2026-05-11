---
name: Make google-email module name + connection shape
description: Módulo Gmail en Make es google-email:sendAnEmail v4, connection via __IMTCONN__ en parameters (no mapper)
type: feedback
originSessionId: b9dde52e-4521-430b-9a97-7254c30853ac
---
Módulo correcto de Gmail en Make es `google-email:sendAnEmail` v4 — NO `google-email:ActionSendEmail` (ese nombre hace fallar scenarios_update con "account is not compatible").

Shape correcta del módulo:
```json
{
  "module": "google-email:sendAnEmail",
  "version": 4,
  "mapper": {
    "to": ["email@x.com"],
    "subject": "...",
    "content": "<html>...</html>",
    "bodyType": "rawHtml"
  },
  "parameters": {"__IMTCONN__": 8183100}
}
```

La connection va en `parameters.__IMTCONN__`, NO como campo libre.

Connections Gmail activas team 354061:
- `8183100` = spekgen.ai@gmail.com (usada en 5 scenarios de notificaciones)
- `8183080` = gibran.alonzo0506@gmail.com

**Why:** Intenté crear módulo con nombre inventado `ActionSendEmail` y Make rechazó con error de compatibility. Perdí ~30 min debuggeando. Fix: siempre inspeccionar un scenario que ya usa el módulo antes de inventar nombres.

**How to apply:** Cuando agregues un módulo nuevo a un blueprint via scenarios_update, primero `scenarios_get` en otro scenario que use ese módulo y copia la shape exacta (module name + version + parameters + mapper).
