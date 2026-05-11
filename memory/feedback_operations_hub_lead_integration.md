# Operations Hub — Cómo integrar un lead nuevo

Server vive en `SPK - 18. OPERATIONS HUB/server.py` puerto **8765**. Source de verdad: `PROSPECTOS/_data/contactos_por_revisar.json`.

## Status enum (STRICT)

```python
PIPELINE_STATUSES = [
  "Mockup Listo", "Msg 1 Enviado", "Msg 2 Enviado", "Msg 3 Enviado",
  "Llamada Hecha", "Reunion Agendada", "Reunion Hecha", "Esperando Respuesta",
  "Cerrado Ganado", "Cerrado Perdido"
]
PIPELINE_EXCLUDED = {"Identificado", "Falso Producto", "", None}
```

Los leads con status fuera de `PIPELINE_STATUSES` o en `PIPELINE_EXCLUDED` **no aparecen** en `/api/pipeline` ni en el dashboard `pipeline.html`.

`STATUS_MAP` traduce a Status del xlsx (Pendiente / Mandé WA / Llamé / Interesado / Cerrado / Rechazado). El xlsx usa el dashboard viejo `_tools/dashboard.html`.

## Botón "Hub" en card

Aparece sólo si el lead tiene `hubUrl` (camelCase). Format esperado:
```
file:///<absolute path URI-encoded>/_prospectos/<NEGOCIO>/<_NEGOCIO_HUB.html>
```
`server.py:436` con `_hub_url_to_http()` lo convierte a `/prospects/<encoded path>` y sirve el HTML como ruta HTTP local.

Convención de filename: `_<NEGOCIO>_HUB.html` (prefijo `_`, mayúsculas). Ej: `_DUARTE_HUB.html`, `_FERRE24_HUB.html`, `_GREENROSSE_HUB.html`.

## Checklist para nuevo lead → visible en Hub

1. JSON `_data/contactos_por_revisar.json`:
   - `archived: false`
   - `status` ∈ `PIPELINE_STATUSES` (NO "Interesado", NO "Identificado")
   - `business`, `phone`, `whatsapp`, `industry`, `tier`
   - `mockupUrl` (string URL pública)
   - `propuestaUrl` (string URL pública)
   - `hubUrl` (file:// URI-encoded path absoluto)
   - `meetingDate`, `meetingTime`, `meetingMode`, `meetingLocation` si hay cita
   - `followUpDate` (YYYY-MM-DD)
   - `lastUpdate` (YYYY-MM-DD)

2. xlsx `SPEKGEN_PROSPECTOS.xlsx`:
   - **NO** correr `_tools/build_xlsx.py` que trunca el resto.
   - Append manual con openpyxl, headers actuales: `Batch | Fecha | # | ID | Negocio | Giro | Teléfono | WA | Rating | Reseñas | Zona | Web Check | Status | Variante | Notas | Mockup URL | Fecha Llamada | Próx. Seg. | Maps URL | Place ID`

3. Hub server hot-reloads del JSON en cada request — solo refresh ⌘R en el dashboard.

## Recovery del xlsx
Si `build_xlsx.py` truncó: `cp SPEKGEN_PROSPECTOS.bak_refresh_b7_20260430_142848.xlsx SPEKGEN_PROSPECTOS.xlsx` y re-edit con openpyxl.
