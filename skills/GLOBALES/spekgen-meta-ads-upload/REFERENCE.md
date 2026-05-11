# Meta Ads API — Reference for SPEKGEN

Esta referencia consolida todo lo que aprendimos durante la sesión de GREENRAY
del 08-09 abril 2026 (7 ads tuvieron que ser re-creados porque el IG salía
vacío en el dropdown). Lee esto ANTES de crear ads con API calls ad-hoc.

## Tabla de contenido

1. [Token types y sus limitaciones](#token-types)
2. [Los 3 IDs de Instagram que existen](#ig-ids)
3. [Estructura de creative por tipo de ad](#creative-structure)
4. [Targeting y Advantage+ Audience](#targeting)
5. [Attribution windows por objetivo](#attribution)
6. [Dynamic Creative — reglas especiales](#dynamic-creative)
7. [UTM tracking con url_tags](#utms)
8. [Flujo completo: campaign → adset → ad](#full-flow)
9. [Debugging: IG dropdown vacío](#ig-debugging)

---

## 1. Token types y sus limitaciones {#token-types}

### System User Token (lo que usamos en SPEKGEN)

**Dónde:** BM Agencia (SPEKGEN, `2131750914244150`) → Usuarios del sistema
→ SPEKGENAUTOADS

**Ventajas:**
- Non-expiring
- Cross-BM (funciona en ad accounts de clientes)
- Se puede asignar a múltiples ad accounts

**Limitaciones críticas:**
- **NO puede usar `instagram_actor_id`** en creatives cuando la IG es
  propiedad del Client BM. Siempre devuelve:
  `(#100) Param instagram_actor_id must be a valid Instagram account id`
- **NO puede llamar endpoints legacy de page** como
  `/{page_id}/instagram_accounts` — devuelve:
  `(#190) This method must be called with a Page Access Token`

**Solución:** usar `instagram_user_id` en vez de `instagram_actor_id`, y
obtener page access token dinámicamente cuando se necesite.

### Page Access Token

**Cómo obtenerlo:**
```bash
curl -s -G "https://graph.facebook.com/v21.0/{PAGE_ID}" \
  -d "access_token=${SYSTEM_USER_TOKEN}" \
  -d "fields=access_token"
```

**Úsalo para:**
- `GET /{page_id}/instagram_accounts` (legacy IG actor IDs)
- `GET /{page_id}/page_backed_instagram_accounts` (PBIA IDs)

**NO es reemplazo del system user token** para crear creatives — algunos
endpoints de creative prefieren el system user token.

---

## 2. Los 3 IDs de Instagram que existen {#ig-ids}

En Meta coexisten 3 IDs distintos para la misma cuenta de IG:

| Tipo de ID | Ejemplo GR | De dónde viene | Cuándo usarlo |
|---|---|---|---|
| **Instagram Business Account ID** | `17841474779124860` | `GET /{page_id}?fields=instagram_business_account` | En `instagram_user_id` dentro de `object_story_spec`. **Este es el que usamos.** |
| **Page Backed Instagram Account (PBIA)** | `17841469776411776` | `GET /{page_id}/page_backed_instagram_accounts` (page token required) | Para pages que no tienen IG real conectado. **No aplica si hay IG real.** |
| **Raw IG user numeric ID** | `74758884637` | `GET /{page_id}?fields=instagram_business_account{ig_id}` | Uso interno de Meta — no útil en nuestro caso. |

**Regla simple:** siempre usar el "Instagram Business Account ID"
(el que empieza con `17841...`). Guardarlo en `.env` como
`META_IG_ACCOUNT_ID`.

---

## 3. Estructura de creative por tipo de ad {#creative-structure}

### Rule #1: `instagram_user_id` va DENTRO de `object_story_spec`

**Esto es lo más importante de este documento.** Si pones `instagram_user_id`
top-level en el creative params (como parámetro hermano de
`object_story_spec`), el API lo acepta pero el UI de Ads Manager NO lo lee.
Resultado: el dropdown de "Cuenta de Instagram" del ad sale vacío.

**MAL:**
```python
api_post(f"{ad_account}/adcreatives", token, {
    "name": "...",
    "object_story_spec": {...},   # sin instagram_user_id adentro
    "instagram_user_id": "17841...",   # ← top-level, UI lo ignora
})
```

**BIEN:**
```python
api_post(f"{ad_account}/adcreatives", token, {
    "name": "...",
    "object_story_spec": {
        "page_id": "...",
        "instagram_user_id": "17841...",   # ← DENTRO de OSS
        "link_data": {...},
    },
})
```

### Static single image

```python
object_story_spec = {
    "page_id": PAGE_ID,
    "instagram_user_id": IG_USER_ID,   # critical
    "link_data": {
        "link": "https://cliente.com/producto",
        "message": "Copy principal...",
        "name": "Headline",
        "description": "Sub-description",
        "image_hash": "abc123...",
        "call_to_action": {
            "type": "SHOP_NOW",
            "value": {"link": "https://cliente.com/producto"},
        },
    },
    "instagram_story_attachment": {   # opcional — 9:16 para Stories/Reels
        "link_data": {
            "link": "https://cliente.com/producto",
            "image_hash": "def456...",   # 1080×1920
            "call_to_action": {"type": "SHOP_NOW"},
        }
    },
}
```

### Carousel

```python
object_story_spec = {
    "page_id": PAGE_ID,
    "instagram_user_id": IG_USER_ID,
    "link_data": {
        "link": "...",
        "message": "...",
        "child_attachments": [
            {"link": "...", "image_hash": "H1", "name": "...", "description": "..."},
            {"link": "...", "image_hash": "H2", "name": "...", "description": "..."},
            {"link": "...", "image_hash": "H3", "name": "...", "description": "..."},
            {"link": "...", "image_hash": "H4", "name": "...", "description": "..."},
        ],
        "multi_share_end_card": True,
        "multi_share_optimized": True,
    },
}
```

### Dynamic Creative (asset_feed_spec)

Ver sección [Dynamic Creative](#dynamic-creative).

---

## 4. Targeting y Advantage+ Audience {#targeting}

### Advantage+ Audience (recomendado para prospección)

Meta "expande" la audiencia automáticamente. Casi siempre superior a
intereses manuales en 2026.

```python
targeting = {
    "geo_locations": {"countries": ["MX"]},
    "age_min": 18,     # MUST be <= 25 when advantage_audience enabled
    "age_max": 65,
    "genders": [1, 2],  # 1=male, 2=female
    "targeting_automation": {
        "advantage_audience": 1   # REQUIRED
    },
}
```

**Errores comunes:**
- `advantage_audience flag required` → faltó `targeting_automation`
- `age_min can't be higher than 25 with Advantage+` → baja a 18 o 25

### Intereses tradicionales (si lo necesitas)

```python
targeting = {
    "geo_locations": {"countries": ["MX"]},
    "age_min": 25,
    "age_max": 55,
    "flexible_spec": [{
        "interests": [
            {"id": "6003107902433", "name": "Salud y bienestar"},
        ]
    }],
}
```

Sin `targeting_automation` aquí.

---

## 5. Attribution windows por objetivo {#attribution}

Los attribution windows que acepta cada objetivo son distintos:

| Objetivo | attribution_spec válido |
|---|---|
| **OUTCOME_SALES (Conversion)** | `[{"event_type": "CLICK_THROUGH", "window_days": 7}, {"event_type": "VIEW_THROUGH", "window_days": 1}]` |
| **OUTCOME_TRAFFIC** | Solo `[{"event_type": "CLICK_THROUGH", "window_days": 1}]` |
| **OUTCOME_AWARENESS** | No attribution (omit) |

Ejemplo:
```python
adset_params["attribution_spec"] = [
    {"event_type": "CLICK_THROUGH", "window_days": 7},
    {"event_type": "VIEW_THROUGH", "window_days": 1},
]
```

Si usas el window incorrecto, el API devuelve:
`attribution_spec param is not compatible with this optimization_goal`.

---

## 6. Dynamic Creative — reglas especiales {#dynamic-creative}

Dynamic Creative permite dar a Meta múltiples imágenes, copies, y headlines;
Meta combina automáticamente y muestra la mejor combinación por usuario.

### Constraints únicos

1. **1 ad por ad set.** Si tratas de poner 2 ads en un DC ad set:
   `Cannot have more than one ad in given Dynamic Creative Ad Set`
   → Solución: crear ad set nuevo para cada DC ad.

2. **asset_feed_spec DEBE tener `ad_formats`.**
   Sin esto: `Invalid parameter`.
   ```python
   asset_feed_spec = {
       "ad_formats": ["SINGLE_IMAGE"],   # REQUIRED
       ...
   }
   ```

3. **is_dynamic_creative se marca en el ad set**, no en el creative:
   ```python
   adset_params["is_dynamic_creative"] = True
   ```

### Estructura completa DC

```python
object_story_spec = {
    "page_id": PAGE_ID,
    "instagram_user_id": IG_USER_ID,   # still required
    # No link_data — todo vive en asset_feed_spec
}

asset_feed_spec = {
    "ad_formats": ["SINGLE_IMAGE"],
    "images": [
        {"hash": "H1"}, {"hash": "H2"}, {"hash": "H3"}, {"hash": "H4"},
    ],
    "bodies": [
        {"text": "Copy variación 1 - beneficio principal"},
        {"text": "Copy variación 2 - social proof"},
        {"text": "Copy variación 3 - urgencia"},
    ],
    "titles": [
        {"text": "Headline A"}, {"text": "Headline B"},
    ],
    "descriptions": [
        {"text": "Sub 1"}, {"text": "Sub 2"},
    ],
    "link_urls": [
        {"website_url": "https://cliente.com/producto"},
    ],
    "call_to_action_types": ["SHOP_NOW"],
}
```

### Verificación post-creación

Los DC creatives NO tienen `effective_instagram_media_id` hasta que
empiezan a servir. Es normal que esté vacío al principio. Si después
de 24h sigue vacío, algo anda mal.

---

## 7. UTM tracking con url_tags {#utms}

### Campo correcto

`url_tags` es propiedad del **adcreative**, no del ad. No tiene `?` inicial.

```python
create_creative(..., url_tags=(
    "utm_source=meta"
    "&utm_medium=paid_social"
    "&utm_campaign={{campaign.name}}"
    "&utm_content={{ad.name}}"
    "&utm_term={{adset.name}}"
))
```

### Macros soportadas por Meta

| Macro | Valor en runtime |
|---|---|
| `{{campaign.name}}` | Nombre de la campaña |
| `{{campaign.id}}` | ID de la campaña |
| `{{adset.name}}` | Nombre del ad set |
| `{{adset.id}}` | ID del ad set |
| `{{ad.name}}` | Nombre del ad |
| `{{ad.id}}` | ID del ad |
| `{{placement}}` | Placement (feed, stories, reels, etc.) |
| `{{site_source_name}}` | fb / ig / msg / an |

### url_tags es inmutable

Una vez creado el creative, `url_tags` NO se puede editar vía POST al
creative ID. Solo name/status/adlabels son editables. Si necesitas
cambiar los UTMs, tienes que crear un creative nuevo y apuntar el ad
a él (ver `fix-creative` command).

### UI caveat

El UI de Ads Manager puede tardar en reflejar `url_tags` con macros.
Hard refresh (Cmd+Shift+R) suele resolverlo. El valor real aplica al
publicar aunque el campo se vea vacío en el UI.

---

## 8. Flujo completo: campaign → adset → ad {#full-flow}

### Orden obligatorio

1. **Create campaign** → devuelve `campaign_id`
2. **Create ad set(s)** con `campaign_id` → devuelve `adset_id`
3. **Upload images** → devuelve `image_hash`s
4. **Create creative** con `image_hash`s → devuelve `creative_id`
5. **Create ad** con `adset_id` + `creative_id` → devuelve `ad_id`

### Ejemplo end-to-end (curl)

```bash
# 1. Campaign
CAMPAIGN=$(curl -s -X POST "https://graph.facebook.com/v21.0/${AD_ACCOUNT}/campaigns" \
  -d "access_token=${TOKEN}" \
  -d "name=GR_CONV_ABR26" \
  -d "objective=OUTCOME_SALES" \
  -d "status=PAUSED" \
  -d "daily_budget=18000" \
  -d 'special_ad_categories=[]' | jq -r .id)

# 2. Ad set (conversion)
ADSET=$(curl -s -X POST "https://graph.facebook.com/v21.0/${AD_ACCOUNT}/adsets" \
  -d "access_token=${TOKEN}" \
  -d "name=CONV_AUDIENCIA" \
  -d "campaign_id=${CAMPAIGN}" \
  -d "optimization_goal=OFFSITE_CONVERSIONS" \
  -d "billing_event=IMPRESSIONS" \
  -d "status=PAUSED" \
  -d 'targeting={"geo_locations":{"countries":["MX"]},"age_min":18,"age_max":65,"targeting_automation":{"advantage_audience":1}}' \
  -d 'promoted_object={"pixel_id":"'${PIXEL}'","custom_event_type":"PURCHASE"}' \
  -d 'attribution_spec=[{"event_type":"CLICK_THROUGH","window_days":7}]' | jq -r .id)

# 3. Upload image (get hash)
HASH=$(curl -s -X POST "https://graph.facebook.com/v21.0/${AD_ACCOUNT}/adimages" \
  -F "access_token=${TOKEN}" \
  -F "filename=@./image.jpg" | jq -r '.images | to_entries[0].value.hash')

# 4. Creative (IG INSIDE OSS)
CREATIVE=$(curl -s -X POST "https://graph.facebook.com/v21.0/${AD_ACCOUNT}/adcreatives" \
  -d "access_token=${TOKEN}" \
  -d "name=GR-AD-001_creative" \
  -d 'object_story_spec={"page_id":"'${PAGE}'","instagram_user_id":"'${IG}'","link_data":{"link":"https://greenray.mx/p/protocolo","message":"Copy...","image_hash":"'${HASH}'","call_to_action":{"type":"SHOP_NOW","value":{"link":"https://greenray.mx/p/protocolo"}}}}' \
  -d "url_tags=utm_source=meta&utm_medium=paid_social&utm_campaign={{campaign.name}}" | jq -r .id)

# 5. Ad
AD=$(curl -s -X POST "https://graph.facebook.com/v21.0/${AD_ACCOUNT}/ads" \
  -d "access_token=${TOKEN}" \
  -d "name=GR-AD-001_PROTOCOLO" \
  -d "adset_id=${ADSET}" \
  -d 'creative={"creative_id":"'${CREATIVE}'"}' \
  -d "status=PAUSED" | jq -r .id)

echo "Created ad ${AD} in adset ${ADSET} with creative ${CREATIVE}"
```

---

## 9. Debugging: IG dropdown vacío {#ig-debugging}

Síntoma: Abres el ad en Ads Manager, sección "Identidad", el dropdown
"Cuenta de Instagram" muestra el dropdown vacío aunque ya asignaste
la IG en el ad account setup.

### Diagnóstico paso 1: verificar estructura del creative

```bash
curl -s -G "https://graph.facebook.com/v21.0/${CREATIVE_ID}" \
  -d "access_token=${TOKEN}" \
  -d "fields=object_story_spec{instagram_user_id,page_id},instagram_user_id,effective_instagram_media_id" | \
  python3 -m json.tool
```

Si ves:
```json
{
  "object_story_spec": {
    "page_id": "...",
    "link_data": {...}
    /* NO hay instagram_user_id aquí */
  },
  "instagram_user_id": "17841..."   /* ← top-level */
}
```
→ **ESTE ES EL BUG.** El UI lee desde `object_story_spec.instagram_user_id`
y lo está buscando donde no está.

### Fix

Creatives son inmutables — no puedes agregar `instagram_user_id` a un
OSS existente. Tienes que crear un creative nuevo y re-apuntar el ad:

```bash
# Ver scripts/meta_upload.py → fix-creative command
python3 meta_upload.py fix-creative \
  --env "/path/to/.env" \
  --ad-id "{AD_ID}" \
  --url-tags "utm_source=meta&utm_medium=paid_social&..."
```

O manualmente:

```bash
# 1. Fetch current OSS
curl -s -G "https://graph.facebook.com/v21.0/{CREATIVE_ID}" \
  -d "access_token=${TOKEN}" \
  -d "fields=name,object_story_spec" > /tmp/old.json

# 2. Python: insert IG inside OSS and POST new creative
python3 <<'EOF'
import json, urllib.parse, urllib.request
old = json.load(open('/tmp/old.json'))
oss = old['object_story_spec']
oss['instagram_user_id'] = '17841474779124860'  # your IG ID
# strip readonly fields
for k in ('id','effective_instagram_media_id','effective_instagram_story_id','effective_object_story_id'):
    oss.pop(k, None)
params = {
    'name': old['name'] + '_fixed',
    'object_story_spec': json.dumps(oss),
    'url_tags': 'utm_source=meta&utm_medium=paid_social&utm_campaign={{campaign.name}}',
    'access_token': 'YOUR_TOKEN',
}
req = urllib.request.Request(
    'https://graph.facebook.com/v21.0/act_XXX/adcreatives',
    data=urllib.parse.urlencode(params).encode(),
    method='POST',
)
print(json.load(urllib.request.urlopen(req)))
EOF

# 3. Point the ad to the new creative
curl -s -X POST "https://graph.facebook.com/v21.0/{AD_ID}" \
  -d "access_token=${TOKEN}" \
  -d 'creative={"creative_id":"NEW_CREATIVE_ID"}'
```

### Por qué pasa

Histórico: Meta tenía `instagram_actor_id` top-level como el campo
oficial. Lo deprecó silenciosamente en favor de `instagram_user_id`
dentro de `object_story_spec`. La migración del UI a leer desde la
nueva ubicación NO fue retroactiva — creatives viejos con IG top-level
siguen funcionando en delivery pero el dropdown del UI no los refleja.

En ads que creas vía UI, Meta automáticamente pone la IG dentro de
OSS. En ads que creas vía API, el default es dejarla top-level si no
lo especificas explícitamente. Por eso la skill usa SIEMPRE la
estructura correcta.
