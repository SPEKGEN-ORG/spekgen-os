---
name: gr-bot-update
description: Actualiza el system prompt del bot de WhatsApp/IG/FB de GREENRAY (Make scenario 4668313) Y propaga el cambio a TODOS los archivos relacionados en la carpeta del cliente (product logs, catalogos, estrategias, prompts de AI employee). Toma input en lenguaje natural, hace discovery de archivos afectados, muestra diff consolidado, ejecuta cambios atomicos, rebuild+push del bot, verifica, registra changelog. Rollback automatico si algo falla.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, mcp__18578e46-df3e-46fa-9402-ee91129bae3f__scenarios_get, mcp__18578e46-df3e-46fa-9402-ee91129bae3f__scenarios_update, mcp__18578e46-df3e-46fa-9402-ee91129bae3f__scenarios_activate, mcp__18578e46-df3e-46fa-9402-ee91129bae3f__scenarios_deactivate, mcp__18578e46-df3e-46fa-9402-ee91129bae3f__executions_list, mcp__18578e46-df3e-46fa-9402-ee91129bae3f__executions_get-detail
---

# /gr-bot-update — Propagador de Correcciones GREENRAY (bot + catalogo + logs + estrategias)

> v2.0 — Pipeline multi-archivo para corregir errores detectados en el bot WhatsApp de GREENRAY. El scope no es solo el bot: cualquier correccion de producto/precio/clasificacion se propaga a TODOS los archivos donde vive esa info (product logs xlsx, catalogo MD, estrategias, AI employee prompts, knowledge base si aplica). Atomico: o se aplica todo, o rollback completo.

## Cuando usar este skill

- Detectaste un error en una respuesta del bot → ej. "ARTRIX recomendado para reflujo cuando es antiinflamatorio"
- El usuario te manda screenshot de la FT oficial + dice "esto no cuadra con lo que dice el catalogo"
- Hay un cambio de precio / formula / producto nuevo que debe reflejarse en todos lados
- Hay que agregar/quitar una regla del bot que tambien aplica a otros touchpoints (AI employee GHL, blast copy, etc.)
- Se detecta una discrepancia entre fuentes (FT vs product log vs catalogo) y hay que decidir cual gana

**NO usar para**:
- Cambios en el theme de Shopify (usar la edicion directa de `04. WEBSITE/greenray-theme/`)
- Cambios estructurales del bot (agregar modulos, cambiar data structures) — esos son manuales en el builder
- Cambios en los PDFs operativos (FT oficiales son source of truth intocables, salvo que venga version nueva del lab)

## Argumento

Descripcion en lenguaje natural del cambio a hacer. Ejemplos:

- `/gr-bot-update "ARTRIX no es para reflujo, es antiinflamatorio osteoarticular. FT dice Curcumina 50mg + MSM 100mg + Boro 6mg + Calcio Coral 250mg + Ac Hialuronico"`
- `/gr-bot-update "agregar regla: nunca usar la palabra milagroso"`
- `/gr-bot-update "HORMO FX MEN 40+ ahora cuesta $489 en vez de $465"`
- `/gr-bot-update "agregar producto nuevo: XYZ $450 en categoria INMUNIDAD, actives: ..."`
- `/gr-bot-update "GAXALIV Enzymas quedo agotado, sacar del catalogo hasta nuevo aviso"`

Si no hay argumento → preguntar al usuario que cambio quiere hacer. Pedir screenshots de la fuente de verdad (FT, label, catalogo oficial) cuando aplique — no inventar datos.

---

## Contexto Critico

**Bot GREENRAY = LIVE** en Make scenario 4668313. Toca clientes reales en WhatsApp todos los dias. NUNCA hacer cambios sin:

1. **Discovery exhaustivo** de archivos afectados (no confiar en la memoria — siempre grep)
2. **Diff consolidado** ANTES de tocar nada
3. **Aprobacion explicita** de Gibran sobre el plan completo
4. **Cambios atomicos**: si falla la propagacion en el archivo #3, revertir tambien los archivos #1 y #2
5. **Verificar post-push** que el bot quedo `isActive: true, isinvalid: false`
6. **Rollback automatico** si algo se rompe

## Rutas Base

```
GR_ROOT         = /Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/GR - GREENRAY
PROMPT_MD       = {GR_ROOT}/08. WHATSAPP/GR_BOT_SYSTEM_PROMPT.md      (single source of truth del bot)
BUILDER_PATH    = {GR_ROOT}/08. WHATSAPP/build_gr_bot_blueprint.py    (lee del MD, rebuild blueprint)
BLUEPRINT_OUT   = /tmp/gr_bot_bp_v4.json                              (output generado)
CHANGELOG_PATH  = {GR_ROOT}/08. WHATSAPP/GR_BOT_CHANGELOG.md
BACKUP_DIR      = {GR_ROOT}/08. WHATSAPP/_builder_backups             (timestamped copies pre-edit)
MAKE_SCENARIO   = 4668313
```

## Arquitectura actual (post-refactor 2026-04-10)

- **GR_BOT_SYSTEM_PROMPT.md** = **unica fuente de verdad del prompt**. Contiene el prompt completo dentro de un bloque ` ``` `.
- **build_gr_bot_blueprint.py** = script que lee el MD, extrae el prompt via regex, y construye el blueprint JSON para Make. No tiene el prompt hardcoded.
- Para editar el prompt del bot: editar **solo el MD**. Nunca editar el builder a mano (salvo para cambios estructurales del scenario).
- El blueprint v4 se escribe a `/tmp/gr_bot_bp_v4.json` y se pushea via `scenarios_update`.

## Mapa de archivos donde vive info de productos

Cuando se corrige un producto, estas son las ubicaciones candidatas a tocar (NO todas aplican siempre — el discovery dice cuales):

| Archivo | Tipo | Rol | Edicion |
|---|---|---|---|
| `08. WHATSAPP/GR_BOT_SYSTEM_PROMPT.md` | MD | Prompt del bot LIVE | **SI** (source of truth) |
| `02. PRODUCTOS/PRODUCT_CATALOG.md` | MD | Catalogo con precios + categorias + CPA ads | SI |
| `02. PRODUCTOS/00. PRODUCT LOG GLOBAL/GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx` | XLSX | Product log curated (solo productos con FT) | SI (via openpyxl) |
| `02. PRODUCTOS/00. PRODUCT LOG GLOBAL/GR_PRODUCT_LOG_COMPLETISIMO_v1.0.xlsx` | XLSX | Log completo 68+ productos con formulas | SI (via openpyxl) — cuidado con discrepancias D-020 |
| `08. WHATSAPP/BLAST_ABRIL_2026/03. AI EMPLOYEE/PROMPT_AI_EMPLOYEE.md` | MD | Prompt del AI employee de GHL (backup del bot) | SI si aplica |
| `08. WHATSAPP/BLAST_ABRIL_2026/_ESTRATEGIA_COMPLETA.md` | MD | Estrategia del blast — contiene el mismo prompt del AI employee | SI si aplica |
| `06. SOCIAL MEDIA/GR_ESTRATEGIA_MES1_ORGANIC_FIRST.md` | MD | Estrategia organica mes 1 — territorios + angulos + stock | SI si aplica |
| `_KNOWLEDGE_BASE.md` | MD | Audit trail historico | **NO editar entries viejas**. Solo agregar entry nueva al final documentando el fix |
| `_CLIENT_CONTEXT.md` | MD | Audit trail historico de sesiones | **NO editar entries viejas**. La proxima sesion documentara el fix |
| `02. PRODUCTOS/02. FICHAS TECNICAS/FICHA *.pdf` | PDF | FT oficial del lab | **NUNCA editar** — source of truth externo |
| `00. BRAND/02. CATALOGO/CATALOGO GREENRAY 2025.pdf` | PDF | Catalogo oficial cliente | **NUNCA editar** — formato source |
| `04. WEBSITE/greenray-theme/sections/ecom-*.liquid` | Liquid | Theme de Shopify | **NO tocar** — requiere ciclo de review + git. Fuera de scope |
| `04. WEBSITE/greenray-theme/assets/ecom-*.js` | JS | Theme compilado | **NUNCA editar** |

Los 5 archivos en el medio (MDs editables) son los que el skill debe tocar cuando aplique. Los xlsx requieren openpyxl via Python — no Edit tool directo.

---

## FASE 0 — Discovery

**Objetivo**: encontrar TODOS los archivos donde vive la info que hay que corregir. No asumir — grep.

1. **Identificar el sujeto del cambio**: producto(s), regla, precio, mapeo sintoma, etc. Extraer 2-3 keywords distintivas.
   - Ej. para ARTRIX: `ARTRIX`, `articular`, `antiinflamatorio`, `reflujo` (para encontrar referencias incorrectas viejas)
   - Ej. para precio HORMO FX MEN 40+: `HORMO FX MEN 40+`, `$465`, `$489`
   - Ej. para regla nueva: keywords relevantes del dominio de la regla

2. **Grep recursivo en `{GR_ROOT}`** con cada keyword, output con contexto `-C 3`:
   ```
   Grep pattern="ARTRIX|Artrix|artrix" path="{GR_ROOT}" -C 3 output_mode="content"
   ```

3. **Categorizar los resultados** en tres buckets:
   - **EDITAR** — archivos del mapa editables donde el cambio aplica
   - **AUDIT TRAIL (NO TOCAR)** — entries historicas en `_KNOWLEDGE_BASE.md` / `_CLIENT_CONTEXT.md` / `GR_BOT_CHANGELOG.md`
   - **OUT OF SCOPE** — PDFs, theme liquid, JS compilado, archivos externos

4. **Verificar contra el mapa de arquitectura**: si un archivo del mapa editable no salio en el grep pero deberia tener el producto, investigar por que (tal vez el producto nunca se mencionaba ahi — OK). Si salio un archivo inesperado → reportar a Gibran como hallazgo.

5. **Leer el estado actual del scenario Make** para asegurar que esta sano antes de tocar nada:
   ```
   mcp__...__scenarios_get(scenarioId=4668313)
   ```
   Si `isActive: false` o `isinvalid: true` → preguntar a Gibran si quiere diagnosticar primero antes de hacer cambios encima.

---

## FASE 1 — Plan

Con los archivos identificados en Discovery, armar un plan consolidado antes de tocar nada.

1. **Por cada archivo del bucket EDITAR**, documentar:
   - Path relativo
   - Cambio especifico (old_string → new_string para MDs, celda/columna para xlsx)
   - Riesgo (bajo si es text replace literal, medio si requiere re-estructurar seccion, alto si afecta JSON/parsing)

2. **Orden de ejecucion** (importante para atomicidad):
   1. Backups de TODOS los archivos a tocar (fase 2)
   2. Edit de MDs editables (fase 3)
   3. Edit del `GR_BOT_SYSTEM_PROMPT.md` (fase 3 — el ultimo para poder rebuild inmediatamente despues)
   4. Rebuild del blueprint + push a Make (fase 4)
   5. Edit de xlsx (fase 5 — despues del bot para que no bloquee el fix critico si openpyxl falla)
   6. Log en changelog (fase 6)

3. **Validacion del plan**: antes de presentarlo, autoverificar:
   - El cambio en el MD del prompt respeta el formato del bloque ` ``` `
   - El cambio no rompe numeracion de reglas del prompt
   - Si hay un producto recategorizado, la nueva categoria existe o se crea correctamente
   - Los xlsx tienen las columnas esperadas (verificar con openpyxl antes de escribir)

---

## FASE 2 — Aprobacion Consolidada

Mostrar a Gibran el plan completo en un solo mensaje. Formato:

```
PROPUESTA DE CAMBIO: {resumen en 1 linea}

RAZON: {por que — ej. "FT oficial dice X, bot/catalogo dicen Y"}

ARCHIVOS A TOCAR: {N}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. {path/relativo/archivo1.md}   (tipo: MD, riesgo: bajo)

   ANTES:
   ```
   {old_string}
   ```

   DESPUES:
   ```
   {new_string}
   ```

━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. {path/relativo/archivo2.md}   (tipo: MD, riesgo: medio)

   ANTES:
   ```
   {old_string}
   ```

   DESPUES:
   ```
   {new_string}
   ```

━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. GR_BOT_SYSTEM_PROMPT.md       (tipo: MD-prompt, riesgo: alto — rebuild + push)
   ... (mismo formato)

━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx   (tipo: XLSX, riesgo: medio)
   Hoja: {sheet_name}
   Fila {N}, columnas afectadas: {col1: old→new, col2: old→new, ...}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

ARCHIVOS IGNORADOS (audit trail / out of scope):
- _KNOWLEDGE_BASE.md (audit historico)
- _CLIENT_CONTEXT.md (audit historico)
- 04. WEBSITE/greenray-theme/... (theme — fuera de scope)

POST-DEPLOY:
- Rebuild blueprint + push a Make scenario 4668313
- Verificar isActive: true, isinvalid: false
- Log en GR_BOT_CHANGELOG.md
- Test sugerido: "{mensaje de prueba para WhatsApp}"

Aprobar el plan completo? (si/no)
Si quieres ajustar algo especifico, dime cual archivo o seccion.
```

**Esperar aprobacion explicita**. Si Gibran dice "no" o pide ajustes → iterar el plan hasta tener version aprobada. No ejecutar parcialmente.

---

## FASE 3 — Backup

Despues de aprobacion, **antes de cualquier Edit**:

1. **Timestamp unificado** para todos los backups de esta operacion:
   ```bash
   TS=$(date +%Y%m%d_%H%M%S)
   ```

2. **Crear carpeta de backup** si no existe: `{BACKUP_DIR}/`

3. **Copiar cada archivo a tocar** al backup con el timestamp:
   ```bash
   mkdir -p "{BACKUP_DIR}/${TS}/"
   cp "{file1}" "{BACKUP_DIR}/${TS}/$(basename {file1})"
   cp "{file2}" "{BACKUP_DIR}/${TS}/$(basename {file2})"
   cp "{PROMPT_MD}" "{BACKUP_DIR}/${TS}/GR_BOT_SYSTEM_PROMPT.md"
   cp "{BUILDER_PATH}" "{BACKUP_DIR}/${TS}/build_gr_bot_blueprint.py"
   # xlsx si aplica
   cp "{xlsx_path}" "{BACKUP_DIR}/${TS}/$(basename {xlsx_path})"
   ```

4. **Guardar el TS en variable** para posible rollback.

5. **Verificar** que los copies existen (`ls "{BACKUP_DIR}/${TS}/"`). Si falla → abortar, no seguir a fase 4.

---

## FASE 4 — Ejecucion (MDs + Prompt + Rebuild + Push)

**Orden atomico**:

### 4.1 — Edit de MDs auxiliares (todos menos el prompt del bot)

Por cada archivo en el plan (excepto `GR_BOT_SYSTEM_PROMPT.md`):

1. `Read` el archivo si no se ha leido
2. `Edit` con old_string/new_string exactos
3. Verificar que el Edit no fallo (si fallo por old_string duplicado → rollback inmediato, no seguir)

### 4.2 — Edit de `GR_BOT_SYSTEM_PROMPT.md`

1. `Read` el MD
2. `Edit` con los cambios al prompt. Asegurar que:
   - El cambio esta DENTRO del bloque ` ``` ... ``` ` (si no, el builder no lo extrae)
   - La numeracion de reglas sigue consecutiva
   - El formato JSON de respuesta del bot no se rompio
   - Si se cambio el changelog al inicio del MD, el `## Changelog` sigue siendo MD valido (NO usar ``` dentro porque colisiona con el bloque del prompt)
3. Si se agrega una categoria nueva al catalogo dentro del prompt → actualizar la numeracion de categorias si existe

### 4.3 — Rebuild del blueprint

```bash
cd "{GR_ROOT}/08. WHATSAPP" && python3 build_gr_bot_blueprint.py
```

Verificar output:
- Debe imprimir `Prompt source: ...GR_BOT_SYSTEM_PROMPT.md`
- Debe imprimir `Prompt length: NNNN chars` (debe ser >500, idealmente 10k-15k)
- Debe imprimir `Blueprint size: NNNNN bytes` (esperado ~15-17 KB)

Si el builder tira `ValueError: No fenced code block found` → el Edit rompio el bloque ` ``` `. Rollback inmediato (fase 7).

Si el builder tira `ValueError: Extracted prompt is suspiciously short` → el Edit dejo el bloque casi vacio. Rollback.

### 4.4 — Verificar que el cambio esta en el blueprint

Grep en `/tmp/gr_bot_bp_v4.json` por un fragmento distintivo del cambio nuevo. Si no aparece → rollback.

```bash
grep -c "{fragmento_esperado_del_cambio}" /tmp/gr_bot_bp_v4.json
# Debe ser >= 1
```

### 4.5 — Push a Make

1. `Read` de `/tmp/gr_bot_bp_v4.json` (completo)
2. `scenarios_update(scenarioId=4668313, blueprint=<json>, name="GR AI Bot — WhatsApp/IG/FB", scheduling={"type":"immediately"})`
3. Verificar respuesta:
   - `isinvalid: false` → OK
   - `isinvalid: true` → **ROLLBACK INMEDIATO** (fase 7)
   - Si `isActive: false` despues del update → llamar `scenarios_activate(4668313)`
4. Re-verificar con `scenarios_get(4668313)` que quedo `isActive: true, isinvalid: false`

---

## FASE 5 — Ejecucion (xlsx)

Solo si hay xlsx en el plan. Ejecutar DESPUES del push del bot — asi el fix critico del bot no depende de que openpyxl funcione.

1. **Leer estructura actual** del xlsx con openpyxl para confirmar columnas y fila del producto:
   ```python
   from openpyxl import load_workbook
   wb = load_workbook(xlsx_path)
   ws = wb[sheet_name]
   # imprimir headers y fila del producto para verificar
   ```

2. **Aplicar cambios** con openpyxl:
   ```python
   ws.cell(row=N, column=M).value = new_value
   wb.save(xlsx_path)
   ```

3. **Verificar** reabriendo el xlsx y leyendo la celda modificada.

4. Si el xlsx tiene flags de discrepancia (ej. D-020 ARTRIX) → **respetar el flag**. No "reconciliar" datos que estan pendientes de validacion externa. Si el cambio requiere tocar una celda flageada → preguntar a Gibran si quiere mantener el flag o reconciliar.

5. Si openpyxl falla (MergedCell, permisos, archivo abierto en Excel) → NO rollback del bot (el bot ya esta bien). Reportar a Gibran y agregar tarea pendiente en changelog.

---

## FASE 6 — Changelog Consolidado

Log en `GR_BOT_CHANGELOG.md`. Agregar entry nueva al inicio (mas reciente arriba):

```markdown
## {YYYY-MM-DD HH:MM} — {resumen corto del cambio}

**Cambio**: {descripcion en 1-2 lineas}

**Razon**: {por que se hizo — ej. "cliente reporto que bot recomendo ARTRIX para reflujo cuando es antiinflamatorio. FT oficial confirmada."}

**Archivos tocados** ({N}):
- `08. WHATSAPP/GR_BOT_SYSTEM_PROMPT.md` → {resumen del cambio en este archivo}
- `02. PRODUCTOS/PRODUCT_CATALOG.md` → {resumen}
- `08. WHATSAPP/BLAST_ABRIL_2026/03. AI EMPLOYEE/PROMPT_AI_EMPLOYEE.md` → {resumen}
- `02. PRODUCTOS/00. PRODUCT LOG GLOBAL/GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx` → {resumen}

**Deploy**: Make scenario 4668313 via `scenarios_update`. Result: `isActive: true, isinvalid: true/false`, `lastEdit: {timestamp}`.

**Backup**: `_builder_backups/{timestamp}/` (contiene copia de los N archivos pre-edit)

**Test sugerido**:
- User: "{mensaje de prueba relevante}"
- Esperado: {que deberia responder ahora}

**Status**: ✅ Desplegado | ⚠️ Parcial (si algun xlsx fallo) | ⏪ Rollback
```

---

## FASE 7 — ROLLBACK (automatico si algo falla)

Se activa automaticamente si cualquiera de estos ocurre:
- `scenarios_update` regresa `isinvalid: true`
- `scenarios_activate` no logra activar
- El builder tira error al rebuild
- El grep de verificacion del blueprint no encuentra el cambio esperado
- Gibran dice "rollback" o "revierte" en cualquier momento

Pasos:

1. **Restaurar TODOS los archivos** desde el backup timestamped:
   ```bash
   cp "{BACKUP_DIR}/${TS}/GR_BOT_SYSTEM_PROMPT.md" "{PROMPT_MD}"
   cp "{BACKUP_DIR}/${TS}/build_gr_bot_blueprint.py" "{BUILDER_PATH}"
   # por cada otro archivo que se toco
   cp "{BACKUP_DIR}/${TS}/$(basename {file1})" "{file1}"
   # xlsx si aplica
   cp "{BACKUP_DIR}/${TS}/$(basename {xlsx_path})" "{xlsx_path}"
   ```

2. **Rebuild** del blueprint desde el backup:
   ```bash
   cd "{GR_ROOT}/08. WHATSAPP" && python3 build_gr_bot_blueprint.py
   ```

3. **Re-push** a Make con el blueprint del rollback:
   ```
   scenarios_update(4668313, blueprint=<json>, name="GR AI Bot — WhatsApp/IG/FB", scheduling={"type":"immediately"})
   scenarios_activate(4668313) si aplica
   ```

4. **Verificar** que el bot quedo en el estado pre-cambio (`isActive: true, isinvalid: false`).

5. **Log del rollback** en changelog con la razon del fallo:
   ```markdown
   ## {timestamp} — ROLLBACK
   **Motivo**: {razon especifica del fallo}
   **Cambio que se intento**: {descripcion breve}
   **Archivos revertidos**: {lista}
   **Status**: ⏪ Revertido a backup ${TS}
   ```

6. **Reportar a Gibran** con: que fallo, que version quedo activa, y sugerir siguiente paso (fix del plan + retry, o diagnostico manual).

---

## Reglas (inviolables)

- **NUNCA editar el scenario directamente en Make UI**. Siempre via MD + builder + scenarios_update.
- **NUNCA editar `/tmp/gr_bot_bp_v4.json`** manualmente. Es output generado.
- **NUNCA editar entries viejas** en `_KNOWLEDGE_BASE.md` ni `_CLIENT_CONTEXT.md` — son audit trail historico. Solo agregar entries nuevas al final (y solo si el cambio es lo suficientemente grande para amerita una nota de sesion).
- **NUNCA editar FTs oficiales** (PDFs en `02. PRODUCTOS/02. FICHAS TECNICAS/`). Son source of truth externo. Si la FT esta mal → pedir a Gibran reconciliar con el lab antes de hacer cambios.
- **NUNCA editar el theme de Shopify** (`04. WEBSITE/greenray-theme/`) desde este skill. Eso requiere ciclo de review + git + deploy aparte.
- **NUNCA tocar PDFs** (`.pdf`). Si hay que actualizar catalogo cliente, es manual con diseño.
- **Siempre backup atomico** antes de edit. Sin excepcion. Con timestamp unificado.
- **Siempre discovery exhaustivo** antes de planear. Grep todos los keywords, no confiar en memoria.
- **Siempre mostrar plan consolidado** antes de ejecutar. No ir archivo por archivo pidiendo aprobacion — un solo plan, una sola aprobacion, una sola ejecucion atomica.
- **Siempre verificar post-push**. Si `isinvalid: true` o `isActive: false`, rollback inmediato.
- **Siempre log en changelog**. Incluso cambios chicos. Incluso rollbacks.
- **Siempre sugerir mensaje de prueba** para WhatsApp al final.
- **Cuidado con discrepancias documentadas** (ej. D-020 ARTRIX FT vs completisimo). NO reconciliar unilateralmente — respetar el flag y preguntar.
- **No tocar credenciales ni webhook IDs** del blueprint sin autorizacion explicita.
- **Mantener formato JSON puro del bot**. Si se cambia el formato de respuesta, validar que sigue parseando en el modulo 4 del scenario.

---

## Cambios Comunes — Referencia Rapida

### A. Corregir clasificacion de producto (caso ARTRIX)

**Ejemplo**: "ARTRIX estaba en DIGESTIVO como reflujo, FT dice que es ANTIINFLAMATORIO OSTEOARTICULAR"

Discovery keywords: `ARTRIX|Artrix|artrix`, `reflujo`, `digestivo`, nombre de categoria nueva

Archivos probables a tocar:
- `GR_BOT_SYSTEM_PROMPT.md` — remover de seccion DIGESTIVO, agregar a nueva seccion ANTIINFLAMATORIO, actualizar mapeo sintoma, agregar regla "NUNCA ARTRIX para X"
- `PRODUCT_CATALOG.md` — mover de tabla GASTROINTESTINAL a tabla nueva ARTICULAR/ANTIINFLAMATORIO
- `PROMPT_AI_EMPLOYEE.md` y `_ESTRATEGIA_COMPLETA.md` blast — mover del bloque DIGESTIÓN a bloque ARTICULAR
- `GR_ESTRATEGIA_MES1_ORGANIC_FIRST.md` — mover del Territorio 1 (GASTRO) al Territorio 3 (DESINFLAMACION)
- `GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx` — verificar columna Línea/Categoría (puede ya estar correcta)
- `GR_PRODUCT_LOG_COMPLETISIMO_v1.0.xlsx` — verificar columna Categoría, respetar flag de discrepancia si existe

### B. Actualizar precio de producto

Discovery keywords: nombre producto + precio viejo + precio nuevo

Archivos probables:
- `GR_BOT_SYSTEM_PROMPT.md` (en catalogo)
- `PRODUCT_CATALOG.md` (tabla)
- `PROMPT_AI_EMPLOYEE.md` y `_ESTRATEGIA_COMPLETA.md` (catalogo por problema)
- `GR_ESTRATEGIA_MES1_ORGANIC_FIRST.md` (tabla de territorios si aparece)
- `GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx` (columna Precio)
- `GR_PRODUCT_LOG_COMPLETISIMO_v1.0.xlsx` (columna Precio MXN — tambien CPA Max si aplica)

### C. Agregar producto nuevo

Pedir a Gibran: FT PDF + precio + categoria + descripcion corta.

Archivos a tocar:
- `GR_BOT_SYSTEM_PROMPT.md` (agregar a categoria correcta + mapeo si aplica)
- `PRODUCT_CATALOG.md` (agregar fila a tabla correcta)
- `GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx` (agregar fila nueva con GR-PXXX siguiente)
- Considerar si aplica agregar al AI employee prompt y estrategias (usualmente SI si es producto hero)

### D. Retirar producto (out of stock)

Archivos a tocar:
- `GR_BOT_SYSTEM_PROMPT.md` (remover de catalogo, agregar a `== PRODUCTOS AGOTADOS ==`, actualizar mapeo sintoma → sugerir reemplazo)
- `PRODUCT_CATALOG.md` (marcar con ⚠️ Agotado o quitar)
- `PROMPT_AI_EMPLOYEE.md` y `_ESTRATEGIA_COMPLETA.md` (quitar del catalogo)
- `GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx` (marcar status)

### E. Agregar regla al bot

Discovery: keywords del dominio de la regla + verificar si hay otros bots/prompts que tambien deberian tener la regla

Archivos a tocar:
- `GR_BOT_SYSTEM_PROMPT.md` (agregar con numero secuencial siguiente)
- `PROMPT_AI_EMPLOYEE.md` y `_ESTRATEGIA_COMPLETA.md` blast — SI si la regla tambien aplica al AI employee (ej. reglas de tono, disclaimer medico)

### F. Cambiar mapeo sintoma → producto

Archivos a tocar:
- `GR_BOT_SYSTEM_PROMPT.md` (seccion `== MAPEO SINTOMA -> PRODUCTO ==`)
- `PROMPT_AI_EMPLOYEE.md` y `_ESTRATEGIA_COMPLETA.md` si el AI employee tambien tiene el mapeo

---

## Troubleshooting

**`scenarios_update` regresa `isinvalid: true`**
- Probablemente el Edit al MD rompio el formato (ej. caracteres especiales en el prompt, bloque ``` quebrado, backslash mal escapado).
- Rollback inmediato desde backup. Re-intentar con un Edit mas cuidadoso.

**Builder tira `ValueError: No fenced code block found`**
- El Edit al MD rompio el bloque ` ``` `. Probablemente quitaste o agregaste un ``` de mas.
- Rollback inmediato.

**Builder tira `Extracted prompt is suspiciously short`**
- El Edit dejo el bloque casi vacio (< 500 chars). Probablemente un old_string gigante que reemplazo demasiado.
- Rollback inmediato.

**El bot responde igual que antes (cambio no aplicado)**
- Verificar que el rebuild corrio: `ls -la /tmp/gr_bot_bp_v4.json` (timestamp reciente)
- Verificar que el fragmento esta en el JSON: `grep -c "{fragmento}" /tmp/gr_bot_bp_v4.json`
- Verificar que `scenarios_update` recibio el blueprint completo (no error silencioso)
- Probar con un mensaje cacheable distinto — Anthropic NO cachea system prompts entre requests, asi que el cambio deberia aplicar instantaneamente

**El bot responde en JSON malformado**
- El Edit probablemente rompio la seccion `== FORMATO DE RESPUESTA ==` del prompt.
- Rollback inmediato.
- El JSON de respuesta esperado es: `{"action": "...", "messages": [...], "products_mentioned": [...], "intent": "..."}`

**openpyxl falla en xlsx con MergedCell**
- Pattern conocido: re-crear la hoja con `wb.remove(ws)` + `wb.create_sheet()` o trabajar con celdas no mergeadas.
- NO hacer rollback del bot por esto — el bot ya esta bien. Reportar a Gibran y agregar pendiente.

**Archivo xlsx abierto en Excel al momento de escribir**
- openpyxl falla con PermissionError. Pedir a Gibran cerrar el archivo y reintentar solo la fase xlsx.

**Grep de discovery devuelve 0 resultados donde se esperaba**
- Posibles causas: product name tiene variacion de escritura (acentos, mayusculas, guion), o el producto no aparece en ese archivo.
- Probar con multiples patterns: `ARTRIX|Artrix|artrix|Artrix Capsulas`

---

## Notas

- Este skill es v2.0, refactorizado 2026-04-10 para soportar multi-archivo.
- v1.0 solo tocaba el builder (que tenia el prompt hardcoded). v2.0 trabaja con el MD como source of truth y propaga cambios a los demas archivos.
- El bot esta LIVE desde 2026-04-10 usando Claude Haiku 4.5 via Anthropic Messages API.
- Data structures Make: 334561 (Anthropic body), 333968 (GHL body), 333981 (Claude response parser).
- Si el changelog crece >1000 lineas, archivarlo a `GR_BOT_CHANGELOG_{YEAR}.md` y empezar uno nuevo.
- Los backups se acumulan en `_builder_backups/{timestamp}/`. Limpiar backups >30 dias viejos si la carpeta crece.
- Discrepancias pendientes conocidas (no auto-reconciliar):
  - **D-020 ARTRIX**: FT oficial dice Boro 6mg / Calcio Coral 250mg / cap 500mg. Completisimo xlsx dice Boro 50mg / Calcio Coral 150mg / Piperina 10mg / cap 510mg. Pendiente reconciliar con Greenmark lab.
