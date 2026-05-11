---
name: Make IML char() function does not exist
description: Make IML has no char() function — use alternative approaches for newline/CR handling in replace chains
type: feedback
---

Make IML does NOT have a `char()` function. Using `char(13)` or `char(10)` in SetVariables or any IML expression causes: `Function 'replace' finished with error! Function 'char' not found!`

**Why:** Discovered on 2026-04-13 when scenario 4706750 (SHOPIFY — Content Hub Actions) failed on ALL webhook calls after being reactivated. The `copy_for_gql` variable used `replace(replace(replace(replace(1.new_copy; "\\"; "\\\\"); char(13); ""); char(10); "\\n"); "\""; "\\\"")`). The `char()` calls broke the entire SetVariables module, blocking approve/reject/edit_copy for the Content Hub portal. Cost: ~10 failed executions, wasted operations.

**How to apply:**
- Never use `char()` in Make IML expressions
- For JSON-safe string escaping in SetVariables, only handle `\` and `"` escaping: `replace(replace(ifempty(val; ""); "\\"; "\\\\"); "\""; "\\\"")`
- For newline handling: rely on Make's jsonStringBodyContent auto-handling, or use GraphQL variables which handle newlines natively
- Always wrap nullable fields in `ifempty(field; "")` before passing to replace chains
- Fixed by removing `char()` calls from `copy_for_gql` variable in scenario 4706750
