# Make datastore:AddRecord / UpdateRecord — fields MUST nest under `data`

`datastore:AddRecord` y `datastore:UpdateRecord` esperan el mapper con esta forma:

```python
"mapper": {
    "key": "{{1.id}}",          # top-level — reconocido
    "overwrite": True,            # top-level — reconocido (AddRecord)
    "data": {                     # fields del data structure van AQUÍ
        "email": "{{1.email}}",
        "status": "active",
        "checkout_url": "{{1.abandoned_checkout_url}}",
        ...
    }
}
```

Si se ponen los campos al top-level (flat), Make **acepta el blueprint sin error**, la ejecución completa con status=1 **success**, pero el registro se guarda con `data: {}` vacío (solo el key queda). No hay warning. No hay error. El job aparece verde.

El `key` y `overwrite` son las únicas 2 fields top-level reconocidas — todo lo demás cae al void.

## Cómo confirmarlo

RPC `expect` del app datastore devuelve el schema real del mapper:

```bash
mcp__18578e46-...__rpc_execute
  appName=datastore, appVersion=1, rpcName=expect
  data={"datastore": <ID>}
  format=form_instructions
```

Output muestra literalmente `name: "data", type: "collection", spec: [...]` con los campos reales del data structure anidados adentro. Si ves eso → mapper.data.<field>, no mapper.<field>.

## Síntomas en runtime

- Records tienen key pero `data: {}` vacío
- Si `key` también falla (ej. `{{1.id}}` no resuelve), Make genera key de 12-char hex random (ej. `1df6c5df3f40`)
- Filter de SearchRecord con `status=active` nunca matchea → Scenario B/C nunca emails

## También: campos fuera del spec

Make silently dropea campos que no existen en el data structure. HC C scenario tenía `converted_at` que no está en el spec — se ignora. Solo usar los campos declarados en data-structure spec.

Causó bloqueo completo del flow HC Abandoned Cart 2026-04-24:
- Scenario A: 20 ejecuciones "success" con registros vacíos
- Scenario B: nunca matcheaba nada (status vacío ≠ "active")
- Scenario C: igual bug, silent drop

Fix: PATCH blueprint via REST con shape correcta → verificar registro populado con POST sintético al webhook.
