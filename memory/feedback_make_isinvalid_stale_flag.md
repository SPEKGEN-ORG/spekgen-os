# Make: isinvalid puede ser flag stale

## Descubrimiento (2026-04-18)

Después de pushear un blueprint válido via `scenarios_update`, Make devolvía `isinvalid: true`.
El blueprint era correcto (verificado — module 8 tenía el mapper limpio).

**Causa:** `isinvalid: true` es un flag persistente del estado anterior (un push roto).
Un push nuevo no lo limpia automáticamente.

**Fix:** Llamar `scenarios_activate` después del push. La activación valida el blueprint
y limpia el flag si es válido. Resultado: `isinvalid: false`, `isActive: true`.

**Regla operativa:**
Siempre hacer: `scenarios_update` → verificar blueprint en `scenarios_get` → `scenarios_activate`
No asumir que `isinvalid: true` post-push significa que el blueprint está mal.
