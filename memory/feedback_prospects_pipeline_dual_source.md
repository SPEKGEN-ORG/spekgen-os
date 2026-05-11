---
name: Operations Hub pipeline reads from JSON not xlsx
description: Pipeline dashboard del Operations Hub lee del JSON canonical, NO del xlsx. Leads que nacen en xlsx están invisibles hasta importación manual.
type: feedback
originSessionId: da1ea852-33c3-4508-b8cc-7503488f1d6d
---
El dashboard `SPK - 18. OPERATIONS HUB/pipeline.html` lee leads de `PROSPECTOS/_data/contactos_por_revisar.json` (canonical), NO del `SPEKGEN_PROSPECTOS.xlsx`. El xlsx es un mirror sincronizado **solo en una dirección**: cuando se edita un lead desde el dashboard, `server.py:_sync_xlsx_for_lead` matchea por Place ID y actualiza la fila xlsx. NO existe el flujo inverso (xlsx→JSON).

**Why:** descubierto 2026-04-29 cuando Yerena, Aventuras Naturales y Terraza RealMar (creados en xlsx vía cold-call) tenían mockup+propuesta LIVE pero no aparecían en pipeline. Los 3 estaban en xlsx con Status="Interesado" pero ausentes del JSON. Adicionalmente la taxonomía de Status no coincide: xlsx usa `Pendiente|Llamé|Interesado|Mandé WA|...` (cold-calls v1), pipeline usa `Mockup Listo|Msg 1 Enviado|Reunion Agendada|Esperando Respuesta|Cerrado Ganado|Cerrado Perdido`. STATUS_MAP en `server.py:468` traduce pipeline→xlsx pero no al revés.

**How to apply:**
- Si Gibran reporta "X prospecto no aparece en el pipeline" → primero verificar que esté en `_data/contactos_por_revisar.json` (no asumir que xlsx es la fuente).
- Si está en xlsx pero NO en JSON → agregarlo manualmente al JSON con shape: `id` (P-XXXX), `business`, `industry`, `status` (bucket pipeline válido), `mockupUrl`/`mockupHandle`/`propuestaHandle`, `qualifiesForMockup: true`, `archived: false`. Backup antes de editar.
- Si ya está en ambos pero el bucket es incorrecto → mejor que Gibran lo mueva desde el dashboard (sync xlsx automático). Si se hace por código, actualizar AMBOS.
- Pendiente: armar `_tools/sync_xlsx_to_json.py` que detecte filas xlsx con `Mockup URL` poblada y Place ID no en JSON → auto-import con mapeo `Status xlsx → bucket pipeline`. Resuelve el gap raíz.
- El JSON tiene 4241+ entries (mayoría status `Identificado` archivados). Solo ~10-18 son pipeline activos.

**Update 2026-05-06:**
- Status terminal renombrado: `Cerrado Ganado` → `WIN`, `Cerrado Perdido` → `LOST` (server.py + pipeline.html). STATUS_MAP actualizado. Filtro "Activos" ahora solo excluye LOST (incluye WIN porque sigue vivo para delivery/factura/retainer).
- Agregadas columnas WIN/LOST siempre visibles en kanban + botones explícitos `✓ WIN` / `✕ LOST` en cards con prompt de `priceClosed` y `dealType`.
- Caso real B&B (LP-1371) graduó del cold-call al outreach activo el mismo día — requirió escritura manual a AMBOS sources (xlsx row 211 + JSON entry). El gap `_tools/sync_xlsx_to_json.py` sigue pendiente.
