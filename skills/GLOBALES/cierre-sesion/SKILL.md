---
name: cierre-sesion
description: Cierra la sesión actual actualizando los 4 destinos de persistencia en paralelo — Delivery Hub (delivery_data.json + rebuild HTMLs), _CLIENT_CONTEXT.md del cliente trabajado, daily note de Obsidian, y memoria si aplica. Diseñado para que el Hub NUNCA quede stale. Activar cuando Gibran diga "platano", "platáno", "/cierre-sesion", "cierra la sesión", "actualiza el hub", "platano que hicimos hoy", "cierre", "vamos a cerrar", "cierra todo", o cuando detectes que una tarea cierra naturalmente y vale persistir lo hecho. Lee _CLIENT_CONTEXT.md del cliente PRIMERO como source of truth — NUNCA infiere estado desde batch.json o factory outputs (bug del piloto 6-may).
---

# /cierre-sesion

Persiste lo hecho en la sesión a los 4 destinos en paralelo, regenera el Delivery Hub, y revela el HTML en Finder.

## Cuándo se dispara

- Gibran dice "platano" / "platáno" / "/cierre-sesion" / "cierra"
- Tarea importante terminó y vale persistir (proactivo — no esperar el platano)
- Después de cualquier batch de ads producido + uploaded
- Después de cerrar/perder un prospecto
- Después de un entregable cliente-facing (PDP, página, reporte, automation nueva)

## Regla #1 (la lección del piloto 6-may)

**Lee `_CLIENT_CONTEXT.md` del cliente trabajado PRIMERO** y úsalo como source of truth. NUNCA infieras el estado desde `batch.json` / `factory/dashboard.html` / archivos de producción intermedia — esos pueden estar `DRAFT` cuando el real ya está `ACTIVE` en Meta (o viceversa). Solo el `_CLIENT_CONTEXT.md` documenta el outcome final ejecutado.

Si `_CLIENT_CONTEXT.md` está stale (no tiene la sesión de hoy), primero **actualízalo tú** y luego sí úsalo para alimentar el resto.

## Los 4 destinos (en orden)

### 1. `_CLIENT_CONTEXT.md` del cliente

Path: `{CLIENTE}/_CLIENT_CONTEXT.md`, sección `## Última Sesión`.

Si ya está actualizado (caso: cliente lo escribió en su propia sesión skill, ej. `/lf-media-buying-cycle`), respétalo y úsalo como input. Si está stale, append nuevo bloque:

```markdown
### Sesión YYYY-MM-DD — {título corto}

**Qué se hizo:**
- bullet 1
- bullet 2

**Decisiones:**
- decisión + razón

**Pendientes:**
- [ ] tarea abierta
```

### 2. `delivery_data.json` — Delivery Hub

Path: `SPK - SPEKGEN AGENCY/SPK - 17. TRACKER/delivery_data.json`.

**Estructura canónica (todos los clientes desde 6-may 2026):**

```json
{
  "code": "LF",
  "cycles": [
    { "label": "Mes Abril", "dates": "...", "status": "closed", "note": "...", "services": [...] },
    { "label": "Mes Mayo",  "dates": "...", "status": "current", "note": "...", "services": [...] }
  ],
  "bonus_delivered": [...],
  "critical_pre_payment": [...],
  "pending_detail": [...]
}
```

**Updates típicos en una sesión:**

- **Sumar a `delivered`:** SOLO si el entregable está LIVE/ACTIVE/UPLOADED/PUBLISHED. DRAFT/WIP/listo-sin-subir cuenta como `in_progress`.
- **Mover de `in_progress` → `delivered`:** cuando se ejecuta el upload final.
- **Sumar a `bonus_delivered`:** entregables fuera del scope contractual (skills nuevos, monitores, infra, fixes operativos cross-cliente). Formato: `"Nombre breve (DD-mes): contexto en una línea"`.
- **Update `note` del cycle current** si cambió el estado del mes.
- **Update `phase` y `owner_notes` del cliente** si cambió la situación grande.

**Meta del archivo (siempre):**

```json
"meta": {
  "month": "Mayo 2026",
  "last_updated": "YYYY-MM-DD",
  "updated_by": "Claude · {resumen ≤80 chars de qué pasó esta sesión}",
  ...
}
```

**Distinción crítica `delivered` vs `in_progress`:**

| Estado real | Categoría JSON |
|---|---|
| Ad ACTIVE en Meta | `delivered` |
| Ad UPLOADED PAUSED en Meta | `delivered` (ya está allá) |
| Ad producido status DRAFT en batch.json | `in_progress` |
| Ad WIP sin imagen final | `in_progress` |
| Post LIVE en IG/FB | `delivered` |
| Post `status=approved` esperando hora cron | `in_progress` |
| Post `status=review` en hub | `in_progress` |
| PDP publicada en Shopify | `delivered` |
| PDP en branch sin merge | `in_progress` |
| Skill nueva creada + commiteada | `bonus_delivered` (rara vez es contractual) |
| Monitor cron live en GH Actions | `bonus_delivered` (a menos que sea uno contratado) |

### 3. Daily note Obsidian

Path: `_OBSIDIAN/02 - DAILY NOTES/YYYY-MM-DD.md` (fecha de hoy real).

Si no existe, créala con el header `# YYYY-MM-DD — {Día}` y secciones `## Clientes trabajados hoy` + `## Sesiones`.

**Update:**
1. Append a `## Clientes trabajados hoy`: `- {CLIENTE} — {título corto sesión}`
2. Append a `## Sesiones`: bloque completo con `### {CLIENTE} — {título}`, **Qué se hizo / Decisiones / Pendientes / Archivos creados**.

Los `- [ ]` en Pendientes aparecen en el Tasks Board de Obsidian — usar para todo lo que quede abierto.

### 4. Memoria (selectivo)

Path: `~/.claude/projects/-Users-gibranalonzo-Library-CloudStorage-GoogleDrive-gibran-alonzo0506-gmail-com-My-Drive-2-01--CLIENTS-OFFICIAL/memory/`.

Solo escribir si la info será útil en SESIONES FUTURAS (no este turno):
- ✅ Bug nuevo descubierto (feedback_*)
- ✅ Decisión arquitectural (project_*)
- ✅ Estado nuevo de cliente que no es derivable del código (project_{cliente}_*)
- ❌ Lo que ya está en `_CLIENT_CONTEXT.md` (no duplicar)
- ❌ Resultado one-off de la sesión (eso es para Obsidian)

Si escribes memoria nueva, agregar entrada en `MEMORY.md` (≤200 chars).

## Workflow del cierre (orden de ejecución)

```
1. Detectar cliente(s) trabajados — preguntar si ambiguo
2. LEER _CLIENT_CONTEXT.md del/los cliente(s) — source of truth
3. Si _CLIENT_CONTEXT está stale → actualizar PRIMERO (sección Última Sesión)
4. Update delivery_data.json:
   - meta.last_updated = hoy
   - meta.updated_by = resumen 1 línea
   - Por cliente trabajado: update services counts en cycle current
   - Si hay infra/skills/monitores → bonus_delivered
5. Append daily note Obsidian (Clientes trabajados hoy + bloque sesión)
6. Memoria solo si valor futuro
7. cd al tracker + /usr/bin/python3 build_hub.py
8. open -R delivery_hub.html (revelar en Finder)
9. Resumen al usuario: qué se actualizó + pendientes que quedaron
```

## Comandos clave

**Rebuild del Hub:**
```bash
cd "SPK - SPEKGEN AGENCY/SPK - 17. TRACKER" && /usr/bin/python3 build_hub.py
```

**Validar JSON antes de rebuild:**
```bash
python3 -c "import json; json.load(open('SPK - SPEKGEN AGENCY/SPK - 17. TRACKER/delivery_data.json')); print('JSON OK')"
```

**Revelar Hub en Finder:**
```bash
open -R "SPK - SPEKGEN AGENCY/SPK - 17. TRACKER/delivery_hub.html"
```

**Backup defensivo antes de editar JSON (opcional para cambios grandes):**
```bash
cp "SPK - SPEKGEN AGENCY/SPK - 17. TRACKER/delivery_data.json" \
   "SPK - SPEKGEN AGENCY/SPK - 17. TRACKER/delivery_data.json.bak.$(date +%Y%m%d-%H%M%S)"
```

## Important: usar `/usr/bin/python3` para el build

`build_hub.py` importa PIL desde `build_evidence_report.py`. PIL solo está instalado en `/usr/bin/python3` (3.9), NO en `/opt/homebrew/bin/python3` (3.14). Mismo issue cross-repo (memoria `feedback_python_paths.md` si existe).

## Edge cases

- **Sesión cross-client (varios clientes):** iterar pasos 1-4 por cada cliente, hacer 5-8 una sola vez al final.
- **Sesión de agencia pura (skills, infra, sin cliente concreto):** skip pasos 1-3, ir directo a `bonus_delivered` agency-wide o crear sección agency en `delivery_data.json` (no existe todavía — flag al usuario si necesario).
- **Sesión sin entregables nuevos (solo exploración/discusión):** skip Hub update, solo Obsidian + memoria si vale.
- **Cierre de mes (cobro pasó):** marcar cycle `current` → `closed` y crear nuevo cycle `current` con services reseteados. Usar `_migrate_to_cycles.py` como referencia del patrón reset.
- **Conflicto entre lo que veo en archivos vs lo que dice `_CLIENT_CONTEXT.md`:** confiar en `_CLIENT_CONTEXT.md` Y avisar al usuario para que valide.

## Anti-patrones

- ❌ Inferir estado de ads desde `batch.json` (status=DRAFT puede estar obsoleto — el ad puede estar ACTIVE en Meta)
- ❌ Sumar a `delivered` algo que no está LIVE
- ❌ Duplicar info entre `_CLIENT_CONTEXT.md` y memoria
- ❌ Crear bloque de sesión en daily note sin "Pendientes" (el Tasks Board los necesita)
- ❌ Hacer rebuild del Hub sin validar JSON antes (un comma faltante rompe los 5 HTMLs)
- ❌ Olvidar `open -R` al final (el usuario necesita ver el resultado revelado en Finder — memoria `feedback_reveal_in_finder.md`)

## Historial

- **6-may 2026:** Skill creada tras piloto manual de cierre LF. Lección #1 incorporada: source of truth = `_CLIENT_CONTEXT.md`, no batch.json. Migración LF/GR/MG a `cycles[]` ejecutada en el mismo turno.
