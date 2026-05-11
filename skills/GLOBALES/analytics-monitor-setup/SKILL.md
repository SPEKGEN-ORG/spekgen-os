---
name: analytics-monitor-setup
description: >
  Configura el Analytics Monitor (GA4 + Microsoft Clarity) para un cliente nuevo
  de SPEKGEN. Cubre el checklist completo: habilitar GA4 API en GCP, dar acceso
  SA a la property, obtener API key de Clarity, crear Google Sheet de dashboard,
  crear GitHub Actions workflow y Cloud Trigger para ejecución cloud cada 2 días.
  Replica exactamente el setup de Healthy Chuchos (sesión 33, 2026-04-14) que ya
  está validado end-to-end. Activar cuando: "replica el analytics monitor para GR",
  "configura el monitor de analytics para LO FITNESS", "quiero analytics monitor
  para [cliente]", "setup analytics monitor", "instala el monitor de GA4 para X".
---

# analytics-monitor-setup

Skill para replicar el Analytics Monitor (GA4 + Clarity) de Healthy Chuchos
a cualquier cliente de SPEKGEN. El setup completo tarda ~15-20 minutos.

## Cuándo Invocar

1. "Replica el analytics monitor para GreenRay / LO FITNESS / [cliente]"
2. "Configura GA4 + Clarity para [cliente]"
3. "Quiero que [cliente] también tenga el dashboard de analytics"
4. "Setup analytics monitor para nuevo cliente"

---

## Paso 0 — Recopilar datos del cliente

Antes de empezar, necesitas estos datos. Si no están disponibles, pedirlos:

```
CLIENTE          = [nombre]          # ej: GREENRAY
CLIENT_PREFIX    = [prefijo]         # ej: gr (2-3 letras, lowercase)
GA4_PROPERTY_ID  = [ID de property]  # ej: 470503075 (ver _CONNECTIONS.md)
CLARITY_PROJECT_ID = [ID]            # ej: 3223270816013972 (ver _CONNECTIONS.md)
SHEET_ID         = [Sheet ID]        # crear nuevo si no existe
ALERT_EMAIL      = gibran.alonzo0506@gmail.com
```

**Fuente de datos:** `SPK - SPEKGEN AGENCY/_CONNECTIONS.md` tiene GA4 Property IDs y
Clarity Project IDs para LF, GR, HC.

**IDs de referencia (pre-llenados):**

| Cliente | GA4 Property ID | Clarity Project ID |
|---------|-----------------|-------------------|
| LO FITNESS | `484501054` | `2971069061151498` |
| GREENRAY | `470503075` | `3223270816013972` |
| HEALTHY CHUCHOS | `529120588` | `vy5jjgw9yi` |

---

## Paso 1 — Habilitar Google Analytics Data API en GCP

**¿Quién lo hace?** Gibran manualmente (1 minuto).

La API `analyticsdata.googleapis.com` debe habilitarse en el GCP project que usa
el service account. En SPEKGEN ese proyecto es `spekgen-sheets` (ID: `828252285603`).

**Instrucciones para Gibran:**
1. Abrir: https://console.developers.google.com/apis/api/analyticsdata.googleapis.com/overview?project=828252285603
2. Iniciar sesión con `gibran.alonzo0506@gmail.com`
3. Hacer clic en "Habilitar" si no está habilitada
4. Confirmar que aparece como "API habilitada"

> ⚠️ Si ya se hizo para HC (2026-04-14), ya está habilitada — saltar este paso.
> La API es por proyecto GCP, no por property. Una sola habilitación sirve para todos los clientes.

**Verificación:** Claude puede verificar haciendo un test fetch de GA4 con el SA.

---

## Paso 2 — Dar acceso Viewer al Service Account en GA4

**¿Quién lo hace?** Gibran manualmente (2 minutos).

El SA `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` necesita rol Viewer
en la GA4 property del cliente.

**Instrucciones para Gibran:**
1. Abrir: https://analytics.google.com/
2. Admin → Property → Property Access Management
3. Clic en "+ Agregar usuarios"
4. Email: `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com`
5. Rol: **Viewer** (Lector)
6. Desmarcar "Notificar por email" → Agregar

**Verificación:** Después de dar acceso, Claude corre un test fetch GA4 con `--skip-email --skip-sheet`.

---

## Paso 3 — Obtener API Key de Clarity

**¿Quién lo hace?** Gibran manualmente (2 minutos).

Cada proyecto de Clarity necesita su propio token JWT Bearer.

**Instrucciones para Gibran:**
1. Abrir: https://clarity.microsoft.com/projects
2. Seleccionar el proyecto del cliente
3. Configuración → Exportar datos → "Nuevo token"
4. Nombre: "SPEKGEN Analytics Monitor"
5. Copiar el token generado

**Pegar el token** en el `.env` del cliente como `CLARITY_API_KEY`.

> ⚠️ Los tokens de Clarity pueden revocarse. Si la extracción falla con 401,
> regenerar el token y actualizar el .env y el secret del GitHub Actions workflow.

---

## Paso 4 — Crear Google Sheet de Dashboard

Si el cliente no tiene un Sheet de analytics, crearlo:

1. Crear un Google Sheet nuevo en la carpeta `{CLIENTE} - SPEKGEN/10. LOGS/`
2. Nombre: `{CLIENTE} ANALYTICS DASHBOARD`
3. Compartirlo con `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` como **Editor**
4. Copiar el Sheet ID de la URL: `docs.google.com/spreadsheets/d/{SHEET_ID}/`
5. Agregar al `.env` del cliente: `{CLIENT_PREFIX}_ANALYTICS_SHEET_ID={SHEET_ID}`

> Para HC el Sheet es el mismo que usa el Meta Ads Monitor: `1LbL48DlaUfoo6-dJ2EK51CKFaTSsi-f2mqhbikEs3CI`.
> Para GR y LF pueden usar el mismo sheet del Meta Monitor si ya existe, o uno separado.

---

## Paso 5 — Configurar variables de entorno

Agregar al `.env` del cliente (si no están ya):

```bash
# Analytics Monitor
GA4_PROPERTY_ID={ga4_property_id}
GA4_PRODUCT_SLUGS={slug1},{slug2},{slug3}   # ej: artridog,dogrelax,gastrodog,omegadog
CLARITY_PROJECT_ID={clarity_project_id}
CLARITY_API_KEY={clarity_api_key}
{PREFIX}_ANALYTICS_SHEET_ID={sheet_id}
MAKE_WEBHOOK_URL=https://hook.us2.make.com/ibxf8tmx2mbeq4r6wp3rnew7x3j8y5vf
HC_ALERT_EMAIL=gibran.alonzo0506@gmail.com

# Si no tiene ya HC_SA_JSON_B64, generarlo:
# python3 -c "import base64; print(base64.b64encode(open('path/to/sa.json','rb').read()).decode())"
# Y agregar como HC_SA_JSON_B64={base64_value}
```

**Product slugs por cliente:**
- LO FITNESS: `protein-wpi,whey-crunch,pre-workout,creatine` (verificar en Shopify)
- GREENRAY: `artrix,artrix-d,fibrix,neurix,immunix` (verificar en Shopify)
- HC: `artridog,dogrelax,gastrodog,omegadog`

---

## Paso 6 — Crear GitHub Actions Workflow

Crear el archivo `.github/workflows/{client}-analytics-monitor.yml` en `g-bran/Spekgen-ops`.

**Template del workflow** (reemplazar `{CLIENT}`, `{PREFIX}`, cron de días):

```yaml
name: {CLIENT} Analytics Monitor (GA4 + Clarity)

on:
  schedule:
    # Días pares 9:07 AM Mexico (UTC-6) = 15:07 UTC
    # Ajustar a días impares si el Meta Monitor de este cliente ya usa pares
    - cron: "7 15 2-30/2 * *"
  workflow_dispatch:
    inputs:
      days:
        description: "Ventana de datos (días)"
        required: false
        default: "7"
      skip_email:
        description: "Saltar email (true/false)"
        required: false
        default: "false"

jobs:
  analytics-monitor:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install --timeout=120 --retries=3 google-analytics-data google-auth google-api-python-client
      - name: Run Analytics Monitor
        env:
          GA4_PROPERTY_ID: ${{ secrets.{PREFIX}_GA4_PROPERTY_ID }}
          GA4_PRODUCT_SLUGS: ${{ secrets.{PREFIX}_GA4_PRODUCT_SLUGS }}
          HC_SA_JSON_B64: ${{ secrets.SPEKGEN_SA_JSON_B64 }}
          CLARITY_PROJECT_ID: ${{ secrets.{PREFIX}_CLARITY_PROJECT_ID }}
          CLARITY_API_KEY: ${{ secrets.{PREFIX}_CLARITY_API_KEY }}
          HC_META_DASHBOARD_SHEET_ID: ${{ secrets.{PREFIX}_ANALYTICS_SHEET_ID }}
          MAKE_WEBHOOK_URL: ${{ secrets.MAKE_WEBHOOK_URL }}
          HC_ALERT_EMAIL: ${{ secrets.HC_ALERT_EMAIL }}
        run: |
          DAYS=${{ github.event.inputs.days || '7' }}
          SKIP=${{ github.event.inputs.skip_email || 'false' }}
          FLAGS="--days $DAYS"
          [ "$SKIP" = "true" ] && FLAGS="$FLAGS --skip-email"
          cd scripts/hc-analytics-monitor && python analytics_monitor.py $FLAGS
```

**Secrets a configurar** en `g-bran/Spekgen-ops`:

```bash
# SA JSON (ya existe como HC_SA_JSON_B64 si HC está configurado)
gh secret set SPEKGEN_SA_JSON_B64 -R g-bran/Spekgen-ops  # reusar el mismo

# Específicos del cliente
gh secret set {PREFIX}_GA4_PROPERTY_ID -R g-bran/Spekgen-ops
gh secret set {PREFIX}_GA4_PRODUCT_SLUGS -R g-bran/Spekgen-ops
gh secret set {PREFIX}_CLARITY_PROJECT_ID -R g-bran/Spekgen-ops
gh secret set {PREFIX}_CLARITY_API_KEY -R g-bran/Spekgen-ops
gh secret set {PREFIX}_ANALYTICS_SHEET_ID -R g-bran/Spekgen-ops

# Globales (ya existen si HC está configurado)
gh secret set MAKE_WEBHOOK_URL -R g-bran/Spekgen-ops
gh secret set HC_ALERT_EMAIL -R g-bran/Spekgen-ops
```

> ⚠️ Usar `printf "%s" "$VALUE" | gh secret set NAME -R repo` para secrets con
> caracteres especiales o valores largos (el flag `-b` puede truncar).
> El SA JSON B64 es el mismo para todos los clientes — reutilizar si ya existe.

---

## Paso 7 — Coordinar horarios (Meta + Analytics)

Cada cliente debe tener sus dos monitors en días alternados:

| Cliente | Meta Ads Monitor | Analytics Monitor |
|---------|-----------------|-------------------|
| HC | Días impares (`1-31/2`) | Días pares (`2-30/2`) |
| GR | Días impares (`1-31/2`) | Días pares (`2-30/2`) |
| LF | Días impares (`1-31/2`) | Días pares (`2-30/2`) |

Sheet actualizado diariamente alternando Meta y Analytics. Si el cliente no tiene
Meta Monitor en GitHub Actions, los Analytics pueden correr en cualquier día.

---

## Paso 8 — Test end-to-end

Después de configurar, hacer test manual:

```bash
# Desde el repo local
cd scripts/hc-analytics-monitor

# Setear env vars del cliente
export GA4_PROPERTY_ID="{ga4_property_id}"
export GA4_PRODUCT_SLUGS="{product_slugs}"
export CLARITY_PROJECT_ID="{clarity_project_id}"
export CLARITY_API_KEY="{clarity_api_key}"
export HC_META_DASHBOARD_SHEET_ID="{sheet_id}"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/spekgen_service_account.json"

# Test sin email y sin sheet
python analytics_monitor.py --days 7 --skip-email --skip-sheet

# Si GA4 y Clarity dan datos, test completo
python analytics_monitor.py --days 7
```

**O desde GitHub Actions:**
```bash
gh workflow run {client}-analytics-monitor.yml \
  -R g-bran/Spekgen-ops \
  --ref main \
  -f days=7 \
  -f skip_email=false
```

**Señales de éxito:**
- `[GA4] Listo — X sesiones · Y ATC · Z compras · $W MXN`
- `[Clarity] Listo — X sesiones · scroll Y% · rage Z · dead W`
- `[Sheet] Todos los tabs de analytics actualizados`
- `Email enviado a gibran.alonzo0506@gmail.com`

**Errores comunes y fixes:**
- `403 SERVICE_DISABLED analyticsdata.googleapis.com` → Paso 1 (habilitar API en GCP)
- `403 User does not have any Google Analytics account` → Paso 2 (SA Viewer en property)
- `Clarity 401` → Regenerar API key en Clarity settings
- `Clarity 429 Exceeded daily limit` → Esperar 24h, no es error del setup
- `Clarity sessions=0 con groupBy=url OK` → Ya está fixed en `clarity_fetch.py` con fallback
- SA no decodifica → Verificar que `HC_SA_JSON_B64` es base64 puro sin newlines

---

## Paso 9 — Documentar

Actualizar estos archivos:

### `SPK - SPEKGEN AGENCY/_CONNECTIONS.md`
Tabla de Clarity: agregar fila con Project ID y status del trigger.

### `{CLIENTE}/_CLIENT_CONTEXT.md`
Agregar en sección "Cloud Monitors":
```markdown
| {CLIENTE} Analytics Monitor (GA4 + Clarity) | GitHub Actions | `.github/workflows/{client}-analytics-monitor.yml` | días pares 9:07 AM | g-bran/Spekgen-ops |
```

### `{CLIENTE}/_KNOWLEDGE_BASE.md`
Agregar nota de la sesión de setup: property IDs confirmados, datos de primer run.

### Memoria
Actualizar `project_hc_meta_ads_monitor.md` (o crear `project_{client}_analytics_monitor.md`)
con Sheet ID, trigger ID/workflow, fecha de setup.

---

## Referencia Rápida — GreenRay

```bash
GA4_PROPERTY_ID=470503075
GA4_PRODUCT_SLUGS=artrix,artrix-d,fibrix,neurix,immunix   # verificar slugs reales en Shopify
CLARITY_PROJECT_ID=3223270816013972
CLARITY_API_KEY=<regenerar en Clarity settings>
GR_ANALYTICS_SHEET_ID=<crear sheet o usar el del Meta Monitor de GR>
```

Workflow: `.github/workflows/gr-analytics-monitor.yml`
Cron: `7 15 2-30/2 * *` (días pares, intercala con GR Meta Monitor en días impares si existe)

## Referencia Rápida — LO FITNESS

```bash
GA4_PROPERTY_ID=484501054
GA4_PRODUCT_SLUGS=protein-wpi,whey-crunch,pre-workout,creatine   # verificar en Shopify
CLARITY_PROJECT_ID=2971069061151498
CLARITY_API_KEY=<regenerar en Clarity settings>
LF_ANALYTICS_SHEET_ID=<crear sheet o usar el del Meta Monitor de LF>
```

Workflow: `.github/workflows/lf-analytics-monitor.yml`
Cron: `7 15 2-30/2 * *`
