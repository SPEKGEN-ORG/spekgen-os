---
name: Make REST API scenarios PATCH requires blueprint without top-level scheduling/interface
description: Make REST API PATCH /scenarios/{id} rejects blueprint if it includes top-level keys `scheduling` or `interface` — those are separate payload fields. Unlike MCP scenarios_update (which in past tests required full shape), the REST API strips them. Also: MAKE_API_TOKEN saved in SPK .env for direct uploads that exceed MCP tool size limits.
type: feedback
originSessionId: 335bed10-e44f-4566-a538-b33301229a6c
---
When uploading a Make.com scenario blueprint via REST API `PATCH /api/v2/scenarios/{id}` with a Personal API Token (Authorization: `Token <uuid>`), the `blueprint` value must be a JSON-encoded string of an OBJECT with exactly these top-level keys:

- `flow` (array)
- `name` (string)
- `metadata` (object)

It must NOT contain `scheduling` or `interface` at the top level. Those go as SEPARATE top-level fields of the PATCH payload:

```json
{
  "blueprint": "{\"flow\":[...],\"name\":\"...\",\"metadata\":{...}}",
  "scheduling": "{\"type\":\"immediately\"}"
}
```

Note both `blueprint` and `scheduling` are **strings of JSON**, not objects.

**Errors encountered (2026-04-23 HC AI Bot WhatsApp recovery):**
- `additionalProperty: 'scheduling'` → pop `scheduling` from blueprint, pass as separate field
- `additionalProperty: 'interface'` → pop `interface` from blueprint too (interface is managed via `PUT /scenarios/{id}/interface` separately)

**When to use REST API instead of MCP `scenarios_update`:**
- Blueprint > ~40KB (MCP tool call has output token cap; subagents cannot pass large objects verbatim without corruption risk)
- Recovery from corrupted uploads (subagent placeholder substitution)
- Any scripted batch operations

**Token location:** `SPK - SPEKGEN AGENCY/.env` as `MAKE_API_TOKEN` (UUID format, us2 zone).

**Post-upload routine:** after a successful PATCH, `isinvalid` may remain `true` as a stale flag. Call `scenarios_activate` then `scenarios_deactivate` (or just activate if you want it running) to re-validate and clear the flag. See also: `feedback_make_isinvalid_stale_flag.md`.
