---
name: Make IML no and()/or() functions — use && and ||
description: Make IML does not have and()/or() functions. Using them inside if() throws "Function 'and' not found!" at runtime. Caused HC Bot outage 2026-04-23.
type: feedback
originSessionId: 335bed10-e44f-4566-a538-b33301229a6c
---
Make's IML does NOT implement `and(...)` or `or(...)` as functions. Boolean composition is done with the operators `&&` and `||` inside `if(cond; then; else)`.

Using `and(a; b)` or `or(a; b)` validates at push time (the blueprint schema accepts the string) but **fails at runtime** with a DataError when the mapper is evaluated:

```
Failed to map 'N.value': Function 'if' finished with error! Function 'and' not found!
```

**Why:** Make's parser sees `and(...)` as a function call, tries to resolve it against the IML function registry, and there is no such function. The error surfaces only when that specific mapper is actually executed — so a blueprint can sit idle looking green until the first real trigger fires and blows up.

**How to apply:**
- When composing booleans inside `{{...}}`, always use `&&` / `||`.
- Wrap each clause in parens for clarity: `{{if((a > 0) && ((b = "") || (parseDate(b) <= now)); "true"; "false")}}`
- Grep new/edited blueprints for `and(` and ` or(` before pushing — catch it at authoring time, not at first webhook hit.
- Same trap likely with other English-word logical helpers (`not(...)`, `xor(...)`); stick to operators.

**Incident:** 2026-04-23 HC AI Bot WhatsApp (scenario 4781819) module 24 (util:SetVariables) had two variables using `and()` / `or()` — `existing_mute_active` and `should_respond`. First inbound WhatsApp message after the blueprint push triggered the DataError and Gibran got a Make error notification. Fix: rewrote both expressions with `&&` / `||`. Verified with real execution + manual `scenarios_run`.
