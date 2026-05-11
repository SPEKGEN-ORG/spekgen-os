# /gr-pdp-deploy — Deploya PDP Landing de GreenRay a Shopify

> v2.0 — Deploy completo: upload template → asignar producto → colecciones → Product Log → git → verificación.

## Argumento
Handle/slug del producto (ej. "bellsan-ultra", "detox-fx") o nombre del producto.

## Rutas base

```
GR_ROOT    = /Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/GR - GREENRAY
THEME_DIR  = {GR_ROOT}/04. WEBSITE/greenray-theme
LOG_FILE   = {GR_ROOT}/02. PRODUCTOS/00. PRODUCT LOG GLOBAL/GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx
ENV_FILE   = {GR_ROOT}/.env
KB_FILE    = {GR_ROOT}/_KNOWLEDGE_BASE.md
CTX_FILE   = {GR_ROOT}/_CLIENT_CONTEXT.md
```

## Constantes Shopify

```
STORE       = greenraynutraceuticos.myshopify.com
THEME_ID    = 131785490521
API_VERSION = 2024-01
BASE_URL    = https://{STORE}/admin/api/{API_VERSION}
COLLECTION_ALL = 284481355865   # "TODOS LOS PRODUCTOS"
```

---

## FASE 0 — Pre-flight checks

1. **Leer `.env`** → extraer `SHOPIFY_ACCESS_TOKEN` (NUNCA mostrar)
2. **Resolver el slug**: Si el usuario dio un nombre, convertir a slug (lowercase, guiones). Si no es claro, buscar en Shopify API
3. **Verificar que el template JSON existe**: `{THEME_DIR}/templates/product.gr-{slug}.json`
   - Si NO existe → **PARAR**. Informar: "Template no encontrado. Ejecutar `/gr-pdp-content {producto}` primero."
4. **Validar JSON**: Parsear el archivo y verificar que es JSON válido con la estructura correcta (`sections.main.type === "gr-pdp-landing"`)
5. **Buscar producto en Shopify**: `GET {BASE_URL}/products.json?handle={handle}`
   - Si no se encuentra, intentar por título: `GET {BASE_URL}/products.json?title={título}`
   - Si aún no se encuentra → listar productos y preguntar al usuario
   - Guardar: `product_id`, `handle`, `title`, `template_suffix` actual
6. **Check de sobreescritura**: Si el producto YA tiene `template_suffix` que empiece con `gr-`:
   - Informar: "Este producto ya tiene template `{template_suffix}`. ¿Redeployar?"
   - En este contexto de skill, PROCEDER (es un redeploy, no un error)

---

## FASE 1 — Upload del template a Shopify

```python
import json, urllib.request, ssl, os

# Leer token
env_path = '{ENV_FILE}'
token = None
with open(env_path) as f:
    for line in f:
        if line.startswith('SHOPIFY_ACCESS_TOKEN='):
            token = line.strip().split('=', 1)[1].strip('"').strip("'")

# Leer template
template_path = '{THEME_DIR}/templates/product.gr-{slug}.json'
with open(template_path) as f:
    content = f.read()

# Validar JSON
json.loads(content)  # Si falla, parar

# PUT al theme
asset_key = f'templates/product.gr-{slug}.json'
payload = json.dumps({'asset': {'key': asset_key, 'value': content}}).encode()
req = urllib.request.Request(
    f'https://greenraynutraceuticos.myshopify.com/admin/api/2024-01/themes/131785490521/assets.json',
    data=payload, method='PUT'
)
req.add_header('X-Shopify-Access-Token', token)
req.add_header('Content-Type', 'application/json')

ctx = ssl.create_default_context()
resp = urllib.request.urlopen(req, context=ctx)
result = json.loads(resp.read())
print(f"Template uploaded: {result['asset']['key']}")
```

Verificar respuesta 200. Si 422 → mostrar error de Shopify, revisar JSON syntax.

---

## FASE 2 — Asignar template al producto

```python
# PUT /admin/api/2024-01/products/{product_id}.json
template_suffix = f'gr-{slug}'
payload = json.dumps({
    'product': {
        'id': product_id,
        'template_suffix': template_suffix
    }
}).encode()
req = urllib.request.Request(
    f'https://greenraynutraceuticos.myshopify.com/admin/api/2024-01/products/{product_id}.json',
    data=payload, method='PUT'
)
req.add_header('X-Shopify-Access-Token', token)
req.add_header('Content-Type', 'application/json')
resp = urllib.request.urlopen(req, context=ctx)
```

Verificar que `template_suffix` se guardó correctamente.

---

## FASE 3 — Verificar y asignar colecciones

1. **Obtener colecciones actuales del producto**:
   ```python
   # GET /admin/api/2024-01/collects.json?product_id={product_id}
   ```

2. **Verificar que esté en "TODOS LOS PRODUCTOS"** (ID: 284481355865):
   - Si NO está → crear collect:
   ```python
   # POST /admin/api/2024-01/collects.json
   payload = json.dumps({'collect': {'product_id': product_id, 'collection_id': 284481355865}}).encode()
   ```

3. **Buscar colección de categoría** que coincida con la línea del producto:
   ```python
   # GET /admin/api/2024-01/custom_collections.json
   # Buscar por título que matchee la categoría (Gastrointestinal, Inmunología, etc.)
   ```
   - Si se encuentra una colección que matchee y el producto no está → asignar
   - Si no se encuentra → informar (no es error, solo no hay colección de categoría)

4. **Listar colecciones finales** del producto para el reporte

---

## FASE 4 — Actualizar Product Log Global

```python
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
from datetime import date

wb = load_workbook('{LOG_FILE}')
ws = wb.active

# Buscar producto por nombre (columna B)
product_row = None
for row in range(2, ws.max_row + 1):
    cell_val = ws[f'B{row}'].value
    if cell_val and '{nombre}'.lower() in str(cell_val).lower():
        product_row = row
        break

if product_row:
    # Actualizar PDP Publicada (columna K) y Última Actualización (columna P)
    ws[f'K{product_row}'] = 'Sí (Native Liquid PDP)'
    ws[f'P{product_row}'] = str(date.today())
    ws[f'K{product_row}'].alignment = Alignment(wrap_text=True, vertical='top')
    ws[f'P{product_row}'].alignment = Alignment(wrap_text=True, vertical='top')
    wb.save('{LOG_FILE}')
    print(f"Product Log actualizado: fila {product_row}")
else:
    print("AVISO: Producto no encontrado en Product Log. Agregar manualmente o via /product-research.")
```

---

## FASE 5 — Git commit + push

```bash
cd "{THEME_DIR}"
git add "templates/product.gr-{slug}.json"
git commit -m "feat: add PDP landing for {Nombre Producto}

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git push origin main
```

Capturar el commit hash para el reporte.

---

## FASE 6 — Verificación post-deploy

1. **Construir URL**: `https://greenray.com.mx/products/{handle}`
2. **Verificar que la página responde**: Hacer un request HTTP a la URL
   ```python
   req = urllib.request.Request(f'https://greenray.com.mx/products/{handle}')
   resp = urllib.request.urlopen(req, context=ctx)
   status = resp.status
   html = resp.read().decode()
   has_section = 'gr-pdp' in html
   ```
3. **Verificar contenido**: Buscar `gr-pdp` en el HTML para confirmar que la sección se renderiza
4. Si falla → informar error específico

---

## FASE 7 — Reporte final

```
DEPLOY COMPLETADO: {Nombre Producto}

1. Template     : templates/product.gr-{slug}.json → Shopify ✅
2. Producto     : {handle} (ID: {product_id}) → template_suffix: gr-{slug} ✅
3. Colecciones  : {lista de colecciones con nombres} ✅
4. Product Log  : Fila {N} actualizada (PDP = Sí) ✅
5. Git          : {commit_hash} → pushed ✅
6. URL live     : https://greenray.com.mx/products/{handle}
7. Verificación : HTTP {status} / Sección gr-pdp: {sí/no}

Verificar visualmente en móvil y desktop.
```

Si algún paso falló, reportar con ❌ y el error específico.

---

## Manejo de errores

| Error | Causa | Solución |
|---|---|---|
| Template JSON no existe | No se ejecutó `/gr-pdp-content` | Informar → ejecutar primero |
| JSON inválido | Error de sintaxis | Mostrar línea del error, corregir |
| 401 Unauthorized | Token expirado o inválido | Re-leer `.env`, verificar token |
| 422 Unprocessable | Template tiene errores Liquid/JSON | Mostrar error de Shopify, corregir template |
| Producto no encontrado | Handle incorrecto o producto no publicado | Listar productos, pedir al usuario que confirme |
| Colección no encontrada | No existe colección de la categoría | Informar, no es bloqueante |
| Git push falla | Sin permisos o conflicto | `git pull --rebase` y reintentar |
| URL no responde | DNS, cache, o template roto | Esperar 30s y reintentar. Si persiste, verificar en Shopify Admin |
| HTML no contiene gr-pdp | Template asignado pero no renderiza | Verificar que `template_suffix` matchea el nombre del archivo sin "product." |

---

## Notas importantes

- **NUNCA** mostrar `SHOPIFY_ACCESS_TOKEN` en output
- El section Liquid (`gr-pdp-landing.liquid`) NO se modifica — solo se crean/actualizan template JSONs
- Si es un redeploy del mismo producto, sobreescribir sin preguntar
- Los defaults del Liquid cubren settings CRO genéricas — el JSON solo necesita sobreescribir lo que es específico del producto
- Después de deploy exitoso, el usuario DEBE verificar visualmente en móvil (el screenshot tool no captura scroll completo)
