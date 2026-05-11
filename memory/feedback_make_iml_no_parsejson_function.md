---
name: Make IML has no parseJSON() function — use json:ParseJSON module instead
description: Make IML does NOT implement parseJSON() as inline function. It exists only as a separate module (json:ParseJSON). Using it inline throws runtime DataError "Function 'parseJSON' not found!". Caused HC Bot crash 2026-04-23 when module 26 customer-context injection used parseJSON(3.data).contact.customFields.
type: feedback
originSessionId: 335bed10-e44f-4566-a538-b33301229a6c
---
Make's IML function registry does NOT include `parseJSON`. JSON parsing is done via the `json:ParseJSON` MODULE, not an inline helper.

Pattern that FAILS at runtime (validates on push):
```
{{ifempty(parseJSON(3.data).contact.firstName; "")}}
{{get(map(parseJSON(3.data).contact.customFields; "value"; "id"; "<ID>"); 1)}}
```

Error:
```
DataError: Failed to map '0.value': Function 'ifempty' finished with error! Function 'parseJSON' not found!
```

**Correct pattern:** add a `json:ParseJSON` module in the flow (with a data structure that includes all fields you'll need, including nested arrays like `customFields: [{id, value}]`), then reference its parsed output directly:
```
{{ifempty(11.contact.firstName; "")}}
{{get(map(11.contact.customFields; "value"; "id"; "<ID>"); 1)}}
```
where `11` is the id of the json:ParseJSON module.

**Critical data-structure gotcha:** the data structure assigned to `json:ParseJSON` must explicitly include any field you want to access. Fields absent from the spec are silently dropped from the parsed output — even if they exist in the raw JSON. For customFields on a GHL contact, the spec needs:
```json
{
  "name": "customFields",
  "type": "array",
  "label": "Custom Fields",
  "spec": {
    "type": "collection",
    "spec": [
      {"name": "id", "type": "text", "label": "Field ID"},
      {"name": "value", "type": "text", "label": "Field Value"}
    ]
  }
}
```
(Note: `any` is not a valid type in Make data structures — use `text` even for mixed-content values; IML `map()` and `get()` handle them fine as strings.)

**Related traps (same family — functions that look like they should exist but don't):**
- `and()` / `or()` → use `&&` / `||` (see `feedback_make_iml_no_and_or_functions.md`)
- `not()` / `xor()` → use `!` / `^` or rewrite
- `char()` → use alternatives (see `feedback_make_char_function.md`)

**How to catch before push:** grep blueprints for `parseJSON(`, `and(`, `or(`, `char(`, `not(`. If they appear inside `{{...}}` mappers, they'll crash at runtime. Authoring-time safety net.

**Incident:** 2026-04-23 HC AI Bot WhatsApp (scenario 4781819) — new module 26 (v2.7 customer context injection) used `parseJSON(3.data).contact.*` for 9 mappers. First real WhatsApp inbound after deploy crashed with "parseJSON not found". Fix: updated data structure 334877 to include `customFields` spec, rewrote all 9 mappers to reference `11.contact.*` (module 11 is the existing json:ParseJSON for contact response). Uploaded via REST API (blueprint 57KB > MCP tool call size limit). Validated with activate+deactivate cycle to clear `isinvalid` stale flag.
