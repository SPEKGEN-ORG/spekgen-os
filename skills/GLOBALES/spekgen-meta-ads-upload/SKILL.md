---
name: spekgen-meta-ads-upload
description: >
  Sube ads a Meta (Facebook/Instagram) via Marketing API v21.0 para cualquier
  cliente de SPEKGEN. Maneja los 3 tipos de creative: (1) estático single
  image, (2) carrusel, (3) Dynamic Creative con asset_feed_spec. Aplica
  automáticamente los parches críticos aprendidos en producción: Instagram
  account correctamente seleccionado en dropdown del UI, UTMs con macros de
  Meta, pixel en promoted_object del ad set, Advantage+ audience con age_min≤25.
  También incluye modo fix para reparar ads existentes cuyos creatives tienen
  IG almacenado top-level en vez de dentro de object_story_spec.
  Activar para: "sube X-AD-NNN a Meta", "crea la campaña Y en Meta", "arregla
  el IG del ad Z", "fix IG en todos los ads de la campaña", "crea ad set con
  Advantage audience", o cualquier trabajo de Meta Ads API.
---

# spekgen-meta-ads-upload

Skill global para operaciones de Meta Ads API cross-client (LF, GR, HC, MG,
Gibran Ecom). Encapsula las lecciones aprendidas y previene los errores que
causaron rework en sesiones anteriores.

## Regla de Oro — Por qué existe esta skill

**NUNCA crear creatives ad-hoc con curl o scripts one-off.** Usar siempre
`scripts/meta_upload.py` o el builder de creative spec. Si lo haces ad-hoc,
te vas a olvidar de algo crítico (ej: `instagram_user_id` dentro de
`object_story_spec`) y los ads salen rotos. Validamos esto en producción:
7 ads de GREENRAY tuvieron que ser reemplazados completos porque la IG
dropdown salía vacía en el UI de Ads Manager.

---

## Cuando Invocar

Siempre que Gibran pida cualquiera de:

1. **Subir un ad**: "sube GR-AD-005", "crea el ad HC-012 en Meta"
2. **Crear campaña**: "crea la campaña GR_CONV_ABR26 con X budget"
3. **Crear ad set**: "crea un ad set con Advantage audience"
4. **Reparar ad existente**: "el IG no aparece seleccionado", "fix UTMs en los ads"
5. **Inspeccionar estado**: "qué tienen los ads de campaña X"

---

## Las 7 Reglas Críticas (memorízalas)

| # | Regla | Por qué |
|---|-------|---------|
| 1 | `instagram_user_id` va **dentro de** `object_story_spec`, NO top-level | Top-level guarda el dato pero el UI dropdown lee desde `object_story_spec.instagram_user_id`. Si no está ahí, el dropdown sale vacío. |
| 2 | `instagram_actor_id` **NO se usa nunca** — siempre `instagram_user_id` | Los system user tokens cross-BM rechazan `instagram_actor_id` con "(#100) must be a valid Instagram account id". `instagram_user_id` funciona. |
| 3 | Pixel va en `promoted_object` del **ad set**, no en `tracking_specs` del ad | `tracking_specs` en el ad payload devuelve "Invalid parameter". |
| 4 | Advantage+ audience requiere `targeting_automation: {advantage_audience: 1}` Y `age_min ≤ 25` | Sin esto: "advantage_audience flag required". Con `age_min > 25`: "age_min can't be higher than 25 with Advantage+". |
| 5 | Dynamic Creative ad set: **1 ad por ad set**, y asset_feed_spec necesita `ad_formats: ["SINGLE_IMAGE"]` | Si metes 2 ads en ad set de DC → "Cannot have more than one ad in given Dynamic Creative Ad Set". Sin `ad_formats` → "Invalid parameter". |
| 6 | Traffic campaign attribution: solo `[{"event_type": "CLICK_THROUGH", "window_days": 1}]` | Traffic no acepta attribution windows más largos. |
| 7 | `url_tags` en el creative (no en el ad). Macros OK: `{{campaign.name}}`, `{{ad.name}}`, `{{adset.name}}` | `url_tags` es campo del adcreative, no del ad. Es inmutable después de crear el creative — para editar hay que crear creative nuevo. |

---

## Estructura Canónica — `object_story_spec`

### Estático (single image)

```json
{
  "page_id": "{PAGE_ID}",
  "instagram_user_id": "{IG_USER_ID}",
  "link_data": {
    "link": "https://cliente.com/producto",
    "message": "Copy principal...",
    "name": "Headline",
    "description": "Sub-description",
    "image_hash": "{HASH}",
    "call_to_action": {"type": "SHOP_NOW"}
  },
  "instagram_story_attachment": {
    "link_data": {
      "link": "https://cliente.com/producto",
      "image_hash": "{HASH_9X16}",
      "call_to_action": {"type": "SHOP_NOW"}
    }
  }
}
```

### Dynamic Creative (asset_feed_spec)

`object_story_spec` queda mínimo, el contenido va en `asset_feed_spec`:

```json
// object_story_spec
{
  "page_id": "{PAGE_ID}",
  "instagram_user_id": "{IG_USER_ID}"
}

// asset_feed_spec (separate param)
{
  "ad_formats": ["SINGLE_IMAGE"],
  "images": [{"hash": "H1"}, {"hash": "H2"}, {"hash": "H3"}, {"hash": "H4"}],
  "bodies": [{"text": "Copy variación 1"}, {"text": "Copy variación 2"}],
  "titles": [{"text": "Headline A"}, {"text": "Headline B"}],
  "descriptions": [{"text": "Desc A"}],
  "link_urls": [{"website_url": "https://cliente.com/producto"}],
  "call_to_action_types": ["SHOP_NOW"]
}
```

Meta optimiza qué combinación mostrar por usuario.

---

## Workflow — Subir un Ad Nuevo

### STEP 0 — Leer .env del cliente

```bash
source "{CLIENT_WORKSPACE}/.env"
# Variables requeridas:
# META_TOKEN, META_AD_ACCOUNT, META_PAGE_ID, META_IG_ACCOUNT_ID (o META_IG_ACTOR_ID), META_APP_ID
# Opcional: META_PIXEL_ID
```

### STEP 1 — Verificar prerequisites con diagnóstico

```bash
python3 "{SKILL}/scripts/meta_diagnose.py" --env "/path/to/.env"
```

Esto valida:
- Token vivo (rechaza si expired)
- Ad account accesible
- Page asignada al system user
- Instagram account conectada al ad account
- Pixel activo
- Permissions del token (22 scopes esperados)
- Sanity check del último ad (verifica que instagram_user_id está en OSS)

### STEP 2 — Subir ad o crear campaña

```bash
# Subir ad individual a un ad set existente
python3 "{SKILL}/scripts/meta_upload.py" upload-ad \
  --env /path/to/client/.env \
  --spec ./ad_specs/GR-AD-001.json \
  --adset-id "23855052705260796" \
  --status PAUSED

# Crear campaign + ad sets + ads de golpe
python3 "{SKILL}/scripts/meta_upload.py" create-campaign \
  --env /path/to/client/.env \
  --plan ./campaign_plan.json \
  --status PAUSED
```

### STEP 3 — Verificar IG y UTMs

```bash
python3 "{SKILL}/scripts/meta_upload.py" verify-ad \
  --env /path/to/client/.env \
  --ad-id "23855052704800796"
```

Output esperado:
```
✅ creative_id: 2346781862521520
✅ instagram_user_id INSIDE object_story_spec: 17841474779124860
✅ url_tags set: utm_source=meta&utm_medium=paid_social&...
```

Si alguno sale ❌, usar `fix-creative`.

### STEP 4 — Fix ads rotos (si aplica)

```bash
# Reemplaza creative del ad con uno nuevo que tenga IG + UTMs correctos
python3 "{SKILL}/scripts/meta_upload.py" fix-creative \
  --env /path/to/client/.env \
  --ad-id "23855052704800796"

# O fix todos los ads de una campaña
python3 "{SKILL}/scripts/meta_upload.py" fix-creative \
  --env /path/to/client/.env \
  --campaign-id "23855052698520796" \
  --all
```

Esto crea un creative nuevo, lo apunta al ad, y deja el viejo huérfano.

---

## Diagnóstico Rápido — Cuando el IG Dropdown Sale Vacío

**Síntoma:** Abres el ad en Ads Manager, sección "Identidad", dropdown de
"Cuenta de Instagram" muestra el dropdown vacío aunque ya asignaste
Instagram.

**Causa raíz:** `instagram_user_id` está top-level en el creative (o no
está), pero NO dentro de `object_story_spec`. El UI lee SOLO desde
`object_story_spec.instagram_user_id`.

**Verificación:**

```bash
curl -s -G "https://graph.facebook.com/v21.0/{CREATIVE_ID}" \
  -d "access_token=${META_TOKEN}" \
  -d "fields=object_story_spec{instagram_user_id},instagram_user_id" | \
  python3 -m json.tool
```

Si ves:
```json
{
  "object_story_spec": { /* sin instagram_user_id */ },
  "instagram_user_id": "17841..."
}
```
→ Está mal. Hay que recrear el creative.

Lo correcto es:
```json
{
  "object_story_spec": {
    "page_id": "...",
    "instagram_user_id": "17841...",
    "link_data": { ... }
  }
}
```

**Fix:** ver STEP 4 arriba.

---

## Referencia de Errores Comunes

| Error | Causa | Fix |
|---|---|---|
| `Param instagram_actor_id must be a valid Instagram account id` | Usaste `instagram_actor_id` con system user token cross-BM | Cambiar a `instagram_user_id` |
| `Cannot have more than one ad in given Dynamic Creative Ad Set` | Ad set de DC tiene 1 ad máximo | Crear ad set nuevo para el segundo ad |
| `advantage_audience flag required` | Faltó `targeting_automation` en targeting | Agregar `targeting_automation: {advantage_audience: 1}` |
| `age_min can't be higher than 25 with Advantage+` | `age_min > 25` con Advantage+ | Bajar a 18 o 25 |
| `attribution_spec` error en Traffic | Traffic no acepta 7-day click | Usar solo CLICK_THROUGH 1-day |
| `Invalid parameter` en asset_feed_spec | Falta `ad_formats` | Agregar `ad_formats: ["SINGLE_IMAGE"]` |
| `tracking_specs` rechazado en ad | Pixel va en ad set, no en ad | Mover a `promoted_object` del ad set |
| "(#190) This method must be called with a Page Access Token" | Endpoints legacy de page requieren page token | Obtener token de `/{PAGE_ID}?fields=access_token` |

---

## Archivos del Skill

| Archivo | Propósito |
|---|---|
| `scripts/meta_upload.py` | Script canónico: upload-ad, create-campaign, verify-ad, fix-creative, list-campaigns |
| `scripts/meta_helpers.py` | Funciones reutilizables: build_object_story_spec, api_post, fix_creative_ig, etc. |
| `scripts/meta_diagnose.py` | Diagnóstico de prerequisites (token, page, IG, pixel) |
| `REFERENCE.md` | Referencia completa de la API: specs, targeting, attribution, UTMs, debugging |

---

## Changelog

| Fecha | Versión | Cambios |
|---|---|---|
| 2026-04-09 | v1.0 | Creación inicial. Extrae lecciones de sesión GREENRAY 08-09/04: IG dropdown fix, UTM macros, Dynamic Creative, Advantage+ audience. Reemplaza el approach ad-hoc con curl por un script canónico. |
