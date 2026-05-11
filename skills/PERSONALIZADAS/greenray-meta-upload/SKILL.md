---
name: greenray-meta-upload
description: >
  Uploads a GREENRAY ad to Meta Ads Manager via Marketing API v21.0. Reads credentials
  from .env automatically, resolves the images path from the CLIENTS AD LOG (sheet
  "📋 GREENRAY ADS") product data, uploads both 1:1 (1080×1080px) and 9:16 (1080×1920px)
  images, creates the AdCreative with correct FB+IG placements and destination URL,
  creates the Ad (PAUSED by default), updates the AD LOG with Meta IDs (columns AT=creative_id,
  AU=ad_id) and status "Activo", and updates 🔄 ROTACIÓN CREATIVA with the assigned
  audience and activation date.
  Activate for: "sube el GR-0XX a Meta", "súbelo", "corre el upload de greenray",
  "sube el GREENRAY ad", "publicar el GR-0XX", or any request to upload a GREENRAY ad
  to Meta Ads Manager.
---

## Base Paths

```
WORKSPACE      = /Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive/CLIENTS/GREENRAY OFFCIAL
PRODUCTS_BASE  = {WORKSPACE}/PRODUCTOS
AD_LOG         = /Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive/CLIENTS/LF - LO FITNESS/LF - 07. LOGS/01. ADS LOG/SPEKGEN_CLIENTS_AD_LOG_v2.0.xlsx
AD_LOG_SHEET   = 📋 GREENRAY ADS
META_SCRIPTS   = {WORKSPACE}/05. LOGS/02. META API SCRIPTS/
CLIENT_CONFIG  = {WORKSPACE}/_SKILLS/meta-upload/client-config.json
```

> **Nota:** El AD LOG es el archivo unificado `SPEKGEN_CLIENTS_AD_LOG_v2.0.xlsx` en la
> carpeta de LO FITNESS. GREENRAY usa el sheet `📋 GREENRAY ADS`.

---

## Credentials — `.env` file at `{META_SCRIPTS}/.env`

```
META_TOKEN       = System User Access Token (non-expiring)
META_AD_ACCOUNT  = act_XXXXXXXXXXXXXXXXX
META_PAGE_ID     = XXXXXXXXXXXXXXXXX
META_PIXEL_ID    = XXXXXXXXXXXXXXXXX
META_IG_ACTOR_ID = XXXXXXXXXXXXXXXXX   ← Instagram account ID de GREENRAY
META_ADSET_ID    = <target ad set ID>
META_CAMPAIGN_ID = <target campaign ID>
```

Si el `.env` no existe todavía, usar `.env.template` como base y pedir a Gibran que llene
las credenciales reales.

---

## GREENRAY Product Folder Structure

```
PRODUCTOS/
├── GASTROINTESTINALES/
│   ├── GAX-ALIV/
│   │   └── 05 - META ADS/
│   │       ├── ANGULO 1 - Acidez/
│   │       │   └── IMAGENES/         ← *_SQ.jpg (1:1) + *_VERT.jpg (9:16)
│   │       └── ANGULO 2 - Estómagos Sensibles/
│   │           └── IMAGENES/
│   └── PROTOCOLO GAXALIV/
│       └── 05 - META ADS/
│           ├── BATCH 1 - 1080 X 1080/  ← 1:1 carousel slides
│           └── BATCH 1 - 1080 X 1920/  ← 9:16 carousel slides
└── [OTHER_CATEGORIES]/
```

Para resolver la ruta de imágenes, leer columna **V** (Ruta Archivo Imagen) del AD LOG.
Si está vacía, buscar con glob en `{PRODUCTS_BASE}/` según producto (columna K) y ángulo
(columna J).

---

## AD LOG Column Reference — Sheet "📋 GREENRAY ADS"

| Col | Letter | Campo |
|-----|--------|-------|
| 1  | A  | ID (GR-001, GR-002, ...) |
| 11 | K  | Producto(s) |
| 12 | L  | Landing Page URL (clean, sin UTMs) |
| 14 | N  | Headline (primer headline si hay varios separados por \|) |
| 15 | O  | Copy Principal (Primary Text A) |
| 16 | P  | Copy Corto (Primary Text B) |
| 17 | Q  | CTA |
| 22 | V  | Ruta Archivo Imagen |
| 23 | W  | Status → set to "Activo" after upload |
| 27 | AA | utm_content value (sin leading ?) |
| 46 | AT | Meta Creative ID ← write here |
| 47 | AU | Meta Ad ID ← write here |

---

## Workflow — Steps In Order

### STEP 0 — Check .env exists

```bash
ls "{META_SCRIPTS}/.env"
```

If missing: tell Gibran to copy `.env.template` → `.env` and fill credentials before
proceeding. DO NOT continue without valid credentials.

---

### STEP 1 — Verify Prerequisites

Before running the upload, confirm:
- [ ] AD LOG exists at the path above
- [ ] Row for `{AD_ID}` exists in sheet `📋 GREENRAY ADS`
- [ ] Status is "En Producción" (not Draft)
- [ ] Column L has the clean landing URL
- [ ] Column AA has the utm_content value
- [ ] Images exist at the path in column V (or resolved via glob)
- [ ] **Both** 1:1 AND 9:16 images are present

```bash
# Check image files
ls "{PRODUCTS_BASE}/{CATEGORIA}/{PRODUCTO}/05 - META ADS/{ANGULO_O_BATCH}/"
```

If 9:16 images are missing, warn Gibran before proceeding — Stories/Reels won't work.

---

### STEP 2 — Dry Run First (always)

```bash
python3 "{META_SCRIPTS}/upload_to_meta_gr.py" \
  --ad-id "{AD_ID}" \
  --status PAUSED \
  --dry-run
```

Show the dry run output to Gibran and confirm before proceeding.

---

### STEP 3 — Run Real Upload

After Gibran confirms:

```bash
python3 "{META_SCRIPTS}/upload_to_meta_gr.py" \
  --ad-id "{AD_ID}" \
  --status PAUSED
```

**Always default to `--status PAUSED`** — upload for review, activate manually in Ads Manager.

The script automatically:
1. Reads credentials from `.env`
2. Gets product from AD LOG sheet `📋 GREENRAY ADS` (column K)
3. Resolves images folder from column V
4. Uploads 1:1 images (for FB + IG Feed)
5. Uploads 9:16 images (for FB + IG Stories/Reels)
6. Creates AdCreative with `instagram_user_id` linked (GREENRAY IG account)
7. For **carrusel**: builds `instagram_story_attachment` with 9:16 child_attachments for Stories/Reels
8. For **estático**: builds `instagram_story_attachment` with 9:16 image_hash for Stories/Reels
9. Sets `destination_type: WEBSITE` with clean URL in `link` + UTMs in `url_tags`
10. Creates Ad with PAUSED status
11. Updates AD LOG: columns AT (creative_id), AU (ad_id), W ("Activo"), E (date)

---

### STEP 3B — Actualizar 🔄 ROTACIÓN CREATIVA

Right after upload succeeds, update the rotation tracker:

```python
import openpyxl, datetime

AD_LOG = "{AD_LOG}"
ad_id  = "{AD_ID}"  # e.g. "GR-001"

wb = openpyxl.load_workbook(AD_LOG)
ws_rot = wb["🔄 ROTACIÓN CREATIVA"]
ws_aud = wb["🎯 AUDIENCIAS META"]

# Find GREENRAY audience — look for GR-AUD-XXX rows
audience_name, audience_id, audience_size, umbral = (
    "GREENRAY_Intereses_GastrointestinalMX", "GR-AUD-001", 800, 2.5)

for row in ws_aud.iter_rows(min_row=5, values_only=True):
    if row[0] and str(row[0]).startswith("GR-AUD-"):
        audience_name = row[1] or audience_name
        audience_id   = row[0]
        try:
            audience_size = int(row[6]) if row[6] and str(row[6]).isdigit() else audience_size
        except:
            pass
        try:
            umbral = float(row[15]) if row[15] else 2.5
        except:
            pass
        break

# Find ad row in ROTACIÓN CREATIVA (col B = Ad ID)
today_str = datetime.date.today().strftime("%d/%m/%Y")
updated = False
for row in ws_rot.iter_rows(min_row=5):
    if row[1].value == ad_id:
        row[6].value  = audience_name
        row[7].value  = audience_id
        row[8].value  = audience_size
        row[9].value  = today_str
        row[13].value = umbral
        row[21].value = today_str
        updated = True
        break

wb.save(AD_LOG)
print(f"  🔄 ROTACIÓN CREATIVA: {'✅ Actualizado' if updated else '⚠️ Fila no encontrada — revisar manualmente'}")
```

---

### STEP 4 — Present Results

```
✅ {AD_ID} — subido a Meta exitosamente

📢 AD CREADO (GREENRAY):
─────────────────────────────────────
Meta Ad ID:      {ad_id}
Meta Creative:   {creative_id}
Status:          PAUSED (revisar antes de activar)
Imágenes 1:1:    {N} subidas
Imágenes 9:16:   {N} subidas
AD LOG:          Actualizado (AT, AU, W, E) — sheet 📋 GREENRAY ADS
🔄 Rotación:     Activada (audiencia + fecha asignadas)

🔗 Ver en Ads Manager:
   https://adsmanager.facebook.com/adsmanager/manage/ads
```

Ask:
> **"¿Activar el ad ahora o revisarlo en Ads Manager primero?"**

---

## Script Setup — upload_to_meta_gr.py

> **Status:** Script pendiente de crear. Copiar `upload_to_meta.py` de LO FITNESS
> `{LF_WORKSPACE}/1. OFFICIAL FOLDER/07. LOGS/02. META API SCRIPTS/upload_to_meta.py`
> como base y adaptar:
> - `AD_LOG_PATH` → nuevo AD LOG v2.0
> - `AD_LOG_SHEET` → `"📋 GREENRAY ADS"`
> - `IMAGE_BASE_PATH` → `PRODUCTS_BASE` de GREENRAY
> - `LO_FITNESS_INSTAGRAM_ACTOR_ID` → `GREENRAY_INSTAGRAM_ACTOR_ID` (desde .env)
> - Función `resolve_image_path()` → adaptar para estructura `05 - META ADS/` de GREENRAY
> - Función `get_utm_content()` → leer columna AA del sheet correcto

---

## Common Errors and Fixes

| Error | Causa | Fix |
|-------|-------|-----|
| `.env` no encontrado | Primer uso — no se ha configurado | Copiar `.env.template` → `.env` y llenar credenciales |
| "App in development mode" | Meta app no publicada | developers.facebook.com → app → Publicar → Live |
| "You don't have required permission" (subcode 1341012) | System user sin acceso a página GREENRAY | Business Manager → Usuarios del sistema → SPEKGENAUTOADS → Agregar activos → Páginas → GREENRAY |
| No images found | Ruta incorrecta o imágenes no guardadas | Verificar STEP 1 — columna V del AD LOG |
| "Invalid parameter" at ad creation | `tracking_specs` en ad payload | Remover — pixel va a nivel Ad Set |
| 9:16 images missing | Solo se guardaron imágenes cuadradas | Crear/guardar versión 9:16 antes del upload |

---

## Meta API Constraints — Critical Rules (inherited from lo-fitness-meta-upload)

| Regla | Por qué |
|-------|---------|
| **No `degrees_of_freedom_spec`** | Deprecated en v21.0 — error_subcode 3858504 |
| **No `tracking_specs` in ad payload** | "Invalid parameter" — pixel va a nivel Ad Set |
| **`instagram_user_id` en `object_story_spec`** | Sin esto el ad muestra "Sin cuenta de Instagram" |
| **`link` = URL limpia (sin UTMs)** | UTMs en `link` van a campo incorrecto |
| **`url_tags` = string UTM (sin `?` inicial)** | Campo "Seguimiento / Parámetros de URL" de Meta |
| **Upload 1:1 Y 9:16** | Solo 1:1 → Stories/Reels muestran crop incorrecto |
| **`instagram_story_attachment` en `object_story_spec`** | Requerido para estático Y carrusel |
| **`destination_type: WEBSITE`** | Garantiza campo "Destino" correcto en Ads Manager |

---

## Changelog

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2026-03-09 | v1.0 | Creación inicial — adaptado de lo-fitness-meta-upload v1.2. GREENRAY-specific paths, AD LOG sheet reference, product folder structure. Script `upload_to_meta_gr.py` pendiente de crear (copiar de LO FITNESS y adaptar). |
