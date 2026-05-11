---
name: Make IML inside JSON body bodies breaks escape
description: Never embed switch()/if() with quoted args inside jsonStringBodyContent — use SetVariables upstream
type: feedback
---

Make HTTP v4 `jsonStringBodyContent` field cannot contain IML expressions that use quoted string arguments (e.g. `{{switch(1.action; "approve"; "approved"; ...)}}`). The double level of JSON escaping (`\"` inside the stored body value) collides with IML's own parser and produces "The provided JSON body content is not valid JSON" at runtime. The body looks valid on disk but fails when executed.

**Why:** JSON body storage requires `"` to be written as `\"`, but IML function args expect plain `"`. Make's IML parser reads the escaped `\"` as literal chars, not string delimiters.

**How to apply:**
- Add a `util:SetVariables` module BEFORE the HTTP call.
- Compute any switch/if/ifempty result as a variable — the variable's `value` input is a plain field (no JSON escape context), so plain quotes in the expression work fine.
- In the HTTP body, reference `{{<moduleId>.<varName>}}` only — no embedded expressions with quoted args.
- Resolved a blocker on scenario 4706750 (SHOPIFY — Content Hub Actions) on 2026-04-10 by adding module id=10 util:SetVariables with `new_status`, `comment_category`, `feedback_clean`, `client_name_clean`.
- `{{1.item_id}}` or `{{1.action}}` (bare refs, no function args) ARE fine inside jsonStringBodyContent.
