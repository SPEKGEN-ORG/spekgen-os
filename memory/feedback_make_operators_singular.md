---
name: Make filter operators are SINGULAR
description: In Make (Integromat) filters, text operators are named SINGULAR not plural. text:contains / text:notcontains DO NOT EXIST and fail silently.
type: feedback
---

**Rule**: For ANY filter in Make, use SINGULAR operator names: `text:contain`, `text:notcontain`, `text:equal`, `text:notequal`, `text:pattern`, `text:notpattern`.

**Why**: On 2026-04-10 I spent 3+ hours debugging the GR WhatsApp bot pause-tag filter believing Make had an architectural limitation with arrays in filter context. I tried `array:notcontains`, `SetVariable2`, `json:ParseJSON` wrapper, direct `join()`, schema gymnastics. Nothing worked. The actual root cause was that `text:notcontains` (PLURAL) is not a valid Make operator — the correct name is `text:notcontain` (SINGULAR). The plural operators fail silently: the filter always evaluates false and silently blocks every route, WITHOUT any validation error, error log, or UI hint. This cost literally hours of the $300 Claude budget.

Evidence captured in datastore 89882 diagnostic records (since deleted):
- `DIAG_OP_NOTCONTAIN_BP` with `text:notcontain` → passed
- `DIAG_OP_CONTAIN_BLAST` with `text:contain` → passed
- `DIAG_OP_PATTERN_BLAST` / `DIAG_OP_NOTPATTERN_BP` → passed (pattern operators also work)

The `join(array; "|")` + SINGULAR operator pattern is the canonical way to filter against a contact's tag array in Make — it DOES work in filter context and does NOT need SetVariable2/ParseJSON wrappers.

**How to apply**: When writing a Make blueprint filter condition in any builder script (`build_*_blueprint.py`) or editing via scenarios_update, the `"o"` field of a condition must use singular forms. Before pushing, grep the blueprint for `text:contains` / `text:notcontains` / `text:equals` — those are typos. If a filter mysteriously blocks every route and no module downstream executes, suspect a plural operator name BEFORE architectural debugging.

Canonical patterns:
```python
# Contains check (route fires only if tag present)
{"a": "{{join(11.contact.tags; \"|\")}}", "o": "text:contain", "b": "bot test"}

# Not-contains check (route fires only if tag absent)
{"a": "{{join(11.contact.tags; \"|\")}}", "o": "text:notcontain", "b": "bot-pausado"}
```

Applies to: all Make scenarios, all clients (GR/HC/LF/MG/Gibran Ecom), all builder scripts.
