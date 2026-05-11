---
name: meta-publish
description: Publica posts en Instagram y Facebook via Meta API para CUALQUIER cliente de SPEKGEN. Usa esta skill cuando se diga "publica MG-XXX", "sube HC-XXX a IG", "publica GR-XXX", "publica LF-XXX", "publica GA-XXX", o cualquier variacion de publicar contenido de cualquier cliente o marca personal. Soporta carruseles y estaticos. Publica en IG + FB simultaneamente.
---

# /meta-publish — Publicacion Universal IG+FB para todos los clientes SPEKGEN

Publica contenido de cualquier cliente SPEKGEN directamente a Instagram y Facebook via Meta API.

## Cuando usar esta skill

- Alguien dice "publica XXX-NNN" donde XXX es el prefijo de cualquier cliente
- Cualquier variacion: "sube a IG", "publica en redes", "programa para el viernes"
- Funciona para: MG, HC, GR, LF, GA (marca personal Gibran)

## Mapa de Clientes

| Prefijo | Cliente | Page ID | IG Business ID | Token Source | Imagen Folder |
|---------|---------|---------|----------------|-------------|---------------|
| `MG-` | METAGREEN | `132180209979937` | `17841462109913746` | `SPK - SPEKGEN AGENCY/.env` → `META_TOKEN` | `MG - METAGREEN/MG - 06. SOCIAL MEDIA/ABRIL MAYO/SEMANA X/MG-XXX/00. IMAGENES FINALES/` |
| `HC-` | HEALTHY CHUCHOS | `102627388012544` | `17841430824981516` | `SPK - SPEKGEN AGENCY/.env` → `META_TOKEN` | `HC - HEALTHY CHUCHOS/HC - 06. SOCIAL MEDIA/.../HC-XXX/00. IMAGENES FINALES/` |
| `GR-` | GREENRAY | `472031575985263` | `17841474779124860` | `SPK - SPEKGEN AGENCY/.env` → `META_TOKEN` | `GR - GREENRAY/GR - 06. SOCIAL MEDIA/.../GR-XXX/00. IMAGENES FINALES/` |
| `LF-` | LO FITNESS | `439469342587050` | — | `LF - LO FITNESS/.env` → `META_TOKEN` | `LF - LO FITNESS/LF - 06. SOCIAL MEDIA/.../LF-XXX/00. IMAGENES FINALES/` |
| `GA-` | GIBRAN ECOM | `1024749174062450` | `17841443011465783` | `SPK - SPEKGEN AGENCY/.env` → `META_TOKEN` | `SPK - SPEKGEN AGENCY/SPK - 12. SOCIAL MEDIA/GIBRAN IG POSTS/GA-XXX/00. WINNERS/` |

> **LO FITNESS** usa BM y token separado. Los demas comparten el token unificado SPEKGENAUTOADS.
> **LO FITNESS** no tiene IG Business conectado al token unificado — solo publicar en FB, o verificar si tiene IG conectado en su propio token.

## Base Path

```
CLIENTS_ROOT="/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL"
```

## Flujo de Publicacion

### Paso 0: Detectar cliente y configuracion

A partir del ID del post (ej: `MG-004`), extraer:
1. **Prefijo** → cliente
2. **Page ID, IG ID** → del mapa de arriba
3. **Token** → leer del .env correspondiente
4. **Imagen folder** → buscar con `find` en la carpeta del cliente

```bash
# Detectar prefijo
POST_ID="MG-004"
PREFIX=$(echo "$POST_ID" | grep -oE '^[A-Z]+-')

# Cargar token
case "$PREFIX" in
  MG-|HC-|GR-|GA-)
    META_TOKEN=$(grep '^META_TOKEN=' "$CLIENTS_ROOT/SPK - SPEKGEN AGENCY/.env" | cut -d= -f2-)
    ;;
  LF-)
    META_TOKEN=$(grep '^META_TOKEN=' "$CLIENTS_ROOT/LF - LO FITNESS/.env" | cut -d= -f2-)
    ;;
esac
```

### Paso 1: Encontrar imagenes

Buscar imagenes PNG en la carpeta del post. Orden: nombre alfabetico (los slides se nombran S1, S2... o 1.png, 2.png...).

```bash
# Buscar folder de imagenes
IMG_DIR=$(find "$CLIENT_FOLDER" -path "*/$POST_ID/00. IMAGENES FINALES" -o -path "*/$POST_ID/00. WINNERS" 2>/dev/null | head -1)

# Si no existe, buscar renders/ como fallback
if [ -z "$IMG_DIR" ]; then
  IMG_DIR=$(find "$CLIENT_FOLDER" -path "*/$POST_ID/renders" 2>/dev/null | head -1)
fi

# Listar PNGs ordenados
IMAGES=$(ls "$IMG_DIR"/*.png 2>/dev/null | sort)
NUM_IMAGES=$(echo "$IMAGES" | wc -l | tr -d ' ')
```

### Paso 2: Obtener caption

Buscar caption en este orden:
1. `{POST_FOLDER}/01. BRIEF/{POST_ID}_CAPTION.md` → extraer texto despues del separador `---`
2. Calendario xlsx del cliente → columna Caption/Copy

```bash
CAPTION_FILE=$(find "$CLIENT_FOLDER" -path "*/$POST_ID*CAPTION.md" 2>/dev/null | head -1)
```

Al leer el caption.md, tomar todo el texto DESPUES del primer `---` (ignorar el header YAML-like).

### Paso 3: Subir imagenes a hosting temporal

Meta API necesita URLs publicas. Usar `tmpfiles.org` como intermediario:

```bash
UPLOAD_URLS=()
for img in $IMAGES; do
  URL=$(curl -s -F "file=@$img" https://tmpfiles.org/api/v1/upload | \
    python3 -c "import sys,json; d=json.load(sys.stdin); url=d.get('data',{}).get('url',''); print(url.replace('tmpfiles.org/','tmpfiles.org/dl/') if url else 'FAILED')")
  UPLOAD_URLS+=("$URL")
done
```

> **Fallback:** Si tmpfiles.org falla, usar Supabase Storage si hay SUPABASE_SERVICE_ROLE_KEY disponible.

### Paso 4: Publicar en Instagram

**Si IG_ID existe para el cliente:**

**Single image (1 PNG):**
```bash
CONTAINER=$(curl -s -X POST "https://graph.facebook.com/v21.0/$IG_ID/media" \
  --data-urlencode "image_url=${UPLOAD_URLS[0]}" \
  --data-urlencode "caption=$CAPTION" \
  -d "access_token=$META_TOKEN")
CONTAINER_ID=$(echo "$CONTAINER" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

sleep 10

PUBLISH=$(curl -s -X POST "https://graph.facebook.com/v21.0/$IG_ID/media_publish" \
  -d "creation_id=$CONTAINER_ID" \
  -d "access_token=$META_TOKEN")
IG_MEDIA_ID=$(echo "$PUBLISH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
```

**Carousel (2+ PNGs):**
```bash
# 1. Crear children
CHILD_IDS=""
for url in "${UPLOAD_URLS[@]}"; do
  CHILD=$(curl -s -X POST "https://graph.facebook.com/v21.0/$IG_ID/media" \
    -d "image_url=$url" \
    -d "is_carousel_item=true" \
    -d "access_token=$META_TOKEN")
  CID=$(echo "$CHILD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
  CHILD_IDS="${CHILD_IDS:+$CHILD_IDS,}$CID"
done

# 2. Crear carousel container
CONTAINER=$(curl -s -X POST "https://graph.facebook.com/v21.0/$IG_ID/media" \
  -d "media_type=CAROUSEL" \
  -d "children=$CHILD_IDS" \
  --data-urlencode "caption=$CAPTION" \
  -d "access_token=$META_TOKEN")
CONTAINER_ID=$(echo "$CONTAINER" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

# 3. Esperar procesamiento
sleep 10

# 4. Publicar
PUBLISH=$(curl -s -X POST "https://graph.facebook.com/v21.0/$IG_ID/media_publish" \
  -d "creation_id=$CONTAINER_ID" \
  -d "access_token=$META_TOKEN")
IG_MEDIA_ID=$(echo "$PUBLISH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
```

### Paso 5: Publicar en Facebook

```bash
# Obtener Page Access Token
PAGE_TOKEN=$(curl -s "https://graph.facebook.com/v21.0/$PAGE_ID?fields=access_token&access_token=$META_TOKEN" | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# Si no hay page token, usar el token directo
if [ -z "$PAGE_TOKEN" ]; then
  PAGE_TOKEN="$META_TOKEN"
fi

# Subir fotos como unpublished
FB_PHOTO_IDS=()
for url in "${UPLOAD_URLS[@]}"; do
  PID=$(curl -s -X POST "https://graph.facebook.com/v21.0/$PAGE_ID/photos" \
    -d "url=$url" \
    -d "published=false" \
    -d "access_token=$PAGE_TOKEN" | \
    python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
  FB_PHOTO_IDS+=("$PID")
done

# Crear multi-photo post
ATTACHED=""
for i in "${!FB_PHOTO_IDS[@]}"; do
  ATTACHED="$ATTACHED -d attached_media[$i]={\"media_fbid\":\"${FB_PHOTO_IDS[$i]}\"}"
done

FB_POST_ID=$(eval curl -s -X POST "\"https://graph.facebook.com/v21.0/$PAGE_ID/feed\"" \
  --data-urlencode "\"message=$CAPTION\"" \
  $ATTACHED \
  -d "\"access_token=$PAGE_TOKEN\"" | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
```

> **Nota:** Si el `eval` con attached_media falla por shell escaping, usar Python para construir la request.

### Paso 5b: Facebook via Python (fallback mas robusto)

```python
import urllib.request, urllib.parse, json

data = {"message": CAPTION, "access_token": PAGE_TOKEN}
for i, pid in enumerate(FB_PHOTO_IDS):
    data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})

encoded = urllib.parse.urlencode(data).encode()
req = urllib.request.Request(
    f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed",
    data=encoded, method="POST"
)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
FB_POST_ID = result.get("id", "")
```

### Paso 6: Actualizar calendario xlsx

Buscar el calendario del cliente y actualizar status a "Publicado":

```python
import openpyxl

# Buscar calendario xlsx
# MG: ABRIL MAYO/MG_SOCIAL_MEDIA_CALENDAR.xlsx
# HC: ABRIL MAYO/HC_SOCIAL_MEDIA_CALENDAR.xlsx
# etc.

wb = openpyxl.load_workbook(calendar_path)
ws = wb['CALENDARIO']  # o la primera hoja

for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    if str(row[0].value) == POST_ID:
        # Status column (usually L = index 11)
        row[11].value = 'Publicado'
        break

wb.save(calendar_path)
```

### Paso 7: Reporte al usuario

Mostrar tabla al finalizar:

```
| Post | Instagram | Facebook | Status |
|------|-----------|----------|--------|
| MG-004 | 17882742000508864 | 132180209979937_122213... | PUBLICADO |
```

## Publicacion Programada

Si dicen "programa MG-005 para manana a las 10am":

1. Convertir fecha/hora a Unix timestamp (timezone: America/Mexico_City)
2. Agregar al container de IG: `-d "published=false" -d "scheduled_publish_time=$UNIX_TS"`
3. NO llamar `media_publish` — se publica solo
4. FB: usar `-d "scheduled_publish_time=$UNIX_TS" -d "published=false"` en el post

## Publicacion Multiple

Si dicen "publica MG-005, MG-006, MG-007":
1. Iterar sobre cada post
2. Publicar en secuencia (NO en paralelo — rate limits de Meta)
3. Sleep 5s entre posts
4. Reportar resultado de cada uno en tabla

## Errores comunes

| Error | Causa | Solucion |
|-------|-------|----------|
| `(#200) Unpublished posts must be posted to a page as the page itself` | Usando system user token para FB en vez de page token | Obtener page token con `?fields=access_token` primero |
| `(#100) param children must be a comma-separated list` | IDs de children mal formateados | Verificar que no hay espacios |
| `IMAGE_DOWNLOAD_TIMEOUT` | tmpfiles.org lento o URL incorrecta | Verificar URL tiene `/dl/` en la ruta. Reintentar upload |
| `(#9004) There was a timeout` | Meta tardando en procesar imagen | Aumentar sleep a 15-20s antes de publish |
| Token expirado | System user token revocado | Regenerar en Meta Business Suite > Business Settings > System Users > SPEKGENAUTOADS > Generate New Token |

## Notas importantes

1. **tmpfiles.org links expiran en ~60 min.** Suficiente para que Meta los descargue.
2. **Rate limits:** Max ~25 API calls por hora por token. Un carousel de 5 slides usa ~8 calls (5 children + 1 container + 1 publish + 1 FB).
3. **No publicar mas de 25 posts por dia por cuenta IG** (limite de Meta).
4. **Videos:** Esta skill solo soporta imagenes. Para Reels, usar la API de Reels (endpoint diferente).
5. **Nunca mostrar tokens en output** al usuario.
