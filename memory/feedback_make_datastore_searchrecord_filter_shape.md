# Make datastore:SearchRecord filter shape

`mapper.filter` es **array de arrays** (outer=OR, inner=AND), NO `{logic, conditions}`.

Shape correcta:
```python
"mapper": {
    "filter": [
        [  # AND group
            {"a": "field_name", "o": "text:equal", "b": "value"},
            {"a": "num_field",  "o": "number:less", "b": "6"}
        ]
    ]
}
```

- `a` = key del UDT (field name del data structure), plain string (no `{{}}`)
- `o` = operator FULLY QUALIFIED: `text:equal`, `text:notequal`, `text:contain`, `number:less`, `number:greater`, `number:greaterorequal`, `date:greater`, `boolean:equal`, `array:contain`, `exist`, `notexist`...
- `b` = valor (puede ser literal o `{{Nmodule.field}}`)

**`limit` va en `parameters`, NO en `mapper`.**

Wrong shape que falla con `TypeError: filterRoot.map is not a function`:
```python
"filter": {"logic": "and", "conditions": [{"field":..., "operator":"eq", "value":...}]}
```

Para descubrir operators válidos: `app-module_get` (format=instructions) sobre `datastore:SearchRecord`. Para validar antes de push: `validate_module_configuration`.

Causó 3 fallas en HC Abandoned Cart Scenarios B y C 2026-04-24 (1 email de error cada 15 min de B).
