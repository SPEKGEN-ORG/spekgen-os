# F24 — Gatillo instantáneo de sincronización (Apps Script)

Esta guía conecta el Sheet **INVENTARIO F24** con GitHub para que, cuando el
dueño edite precios/stock/promos en vivo, el bot se sincronice **al momento**
(con un colchón de ~60 segundos) en lugar de esperar al cron que corre 2×/día.

> El script vive en `apps_script_trigger.gs` (esta misma carpeta). Pega ese
> archivo en el editor de Apps Script del Sheet siguiendo los pasos de abajo.

---

## ⛔ ANTES DE EMPEZAR — NO ACTIVAR TODAVÍA

**No crees el trigger ni pegues el token hasta que el operador dé luz verde.**

Hay un cron que ya corre 2 veces al día contra el repo. Activar este gatillo
sin coordinarlo puede disparar sincronizaciones encimadas. Deja todo listo,
pero **espera la confirmación del operador** para el paso final (paso 4).

---

## Datos que vas a usar

| Dato | Valor |
|---|---|
| **Repo** | `SPEKGEN-ORG/spekgen-os` |
| **Workflow** | `f24_promos_sync.yml` |
| **Sheet** | INVENTARIO F24 (`1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U`) |

---

## Paso 1 — Crear el GitHub Token (fine-grained PAT)

1. Entra a GitHub → tu foto (arriba a la derecha) → **Settings**.
2. Abajo en el menú izquierdo: **Developer settings**.
3. **Personal access tokens** → **Fine-grained tokens** → botón **Generate new token**.
4. Llena así:
   - **Token name:** `f24-sheet-trigger`
   - **Expiration:** 1 año (o lo que prefieras; anota la fecha para renovarlo).
   - **Resource owner:** selecciona **SPEKGEN-ORG**.
   - **Repository access:** elige **Only select repositories** → marca **spekgen-os**.
   - **Permissions** → **Repository permissions** → busca **Actions** → ponlo en
     **Read and write**.
5. Clic en **Generate token** y **copia el token** (empieza con `github_pat_...`).
   Guárdalo a la mano; solo se muestra una vez.

> Si SPEKGEN-ORG pide aprobación de admin para el token, apruébalo desde la
> configuración de la organización (o pídele al admin que lo apruebe).

---

## Paso 2 — Abrir el editor de Apps Script y pegar el script

1. Abre el Sheet **INVENTARIO F24**.
2. Menú **Extensiones** → **Apps Script**.
3. Si hay código de ejemplo (`function myFunction() {}`), bórralo.
4. Abre el archivo `apps_script_trigger.gs` de esta carpeta, **copia todo su
   contenido** y pégalo en el editor.
5. Clic en el ícono de **guardar** (💾) — ponle nombre al proyecto, ej. `F24 Sync Trigger`.

---

## Paso 3 — Pegar el token en las Propiedades del script

1. En el editor de Apps Script, menú izquierdo: ⚙️ **Configuración del proyecto**
   (Project Settings).
2. Baja hasta **Propiedades del script** (Script Properties).
3. Clic en **Agregar propiedad del script** (Add script property):
   - **Propiedad (nombre):** `GH_PAT`
   - **Valor:** pega el token `github_pat_...` del Paso 1.
4. Clic en **Guardar propiedades del script**.

> El token NO va dentro del código — solo aquí. Así no queda expuesto si se
> comparte el script.

---

## Paso 4 — Crear el trigger instalable onEdit  ⚠️ (solo con luz verde del operador)

> ⚠️ Este es el paso que **enciende** el gatillo. No lo hagas hasta que el
> operador confirme.

1. En el editor de Apps Script, menú izquierdo: ⏰ **Activadores** (Triggers).
2. Botón **Agregar activador** (Add Trigger), abajo a la derecha.
3. Configura:
   - **Función que se ejecutará:** `onEditTrigger`
   - **Implementación:** `Head`
   - **Origen del evento:** `Desde una hoja de cálculo` (From spreadsheet)
   - **Tipo de evento:** `Al editar` (On edit)
4. Clic en **Guardar**.
5. Google te pedirá **autorizar** los permisos (la cuenta del dueño del Sheet).
   Acepta. Si aparece "Google no verificó esta app" → **Configuración avanzada**
   → **Ir a (nombre del proyecto)** → **Permitir**.

> Importante: el trigger debe ser **instalable** (creado aquí en Activadores),
> NO el simple `onEdit`. El simple no puede hacer llamadas autenticadas a GitHub.

---

## Paso 5 — Probar que dispara

1. En el Sheet, ve a la hoja **✍️ CAPTURA PROMOS** y edita cualquier celda
   (o en **📦 STOCK Y PROMOS** cambia un valor de la columna **E** o **F**).
2. Espera ~60–90 segundos (el debounce agrupa ediciones y dispara una sola vez).
3. Abre el repo en GitHub → pestaña **Actions** → workflow
   **F24 Promos Sync → Bot**. Debe aparecer una corrida nueva recién iniciada.
4. Si corrió: ✅ todo bien.

### Si NO disparó — revisar logs

1. Editor de Apps Script → menú izquierdo **Ejecuciones** (Executions).
2. Busca la corrida de `fireDispatch` y mira el log:
   - `falta GH_PAT` → revisa el Paso 3 (nombre exacto `GH_PAT`).
   - `HTTP 401/403` → el token no tiene permiso **Actions: Read and write**
     sobre `spekgen-os`, o falta aprobación del admin de la org.
   - `HTTP 404` → revisa que el repo (`SPEKGEN-ORG/spekgen-os`) y el nombre del
     workflow (`f24_promos_sync.yml`) sean correctos, y que el workflow ya esté
     en la rama `main`.
   - `HTTP 204` → en realidad SÍ funcionó (204 = éxito).

---

## Cómo funciona (resumen)

- Cada edición relevante reinicia un temporizador de ~60s (debounce).
- Si haces 10 ediciones seguidas, se dispara **una sola** sincronización al final.
- El disparo hace un `workflow_dispatch` en `main`, que corre el mismo workflow
  del cron pero bajo demanda (modo `--apply`, igual que el cron normal).
- El cron de 2×/día **sigue activo** como red de seguridad; este gatillo solo
  adelanta la sincronización cuando hay cambios en vivo.
