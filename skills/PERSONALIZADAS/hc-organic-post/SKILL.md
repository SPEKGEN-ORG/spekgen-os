---
name: hc-organic-post
description: >
  Workflow completo de producción de posts orgánicos para Healthy Chuchos.
  Fase A (CONCEPTO → BRIEF + PROMPTS HTML para Gemini web UI) y
  Fase B (IMÁGENES → CALENDARIO + CAPTION + CONTENT HUB).
  Activar cuando Gibran diga: "vamos con HC-XXX", "nuevo post orgánico HC",
  "adapta esta inspiración para HC", "tengo esta referencia para HC",
  "ya están las imágenes en 00. imagenes finales", "imágenes listas HC-XXX",
  "ya puse las imágenes", "súbelas al hub".
---

# /hc-organic-post — Producción Orgánica HC

Workflow semi-automático de dos fases para posts orgánicos de Healthy Chuchos.
Gibran genera las imágenes en gemini.google.com/app — Claude maneja todo lo demás.

---

## Detección de Fase

**Fase A** → Gibran inicia un post nuevo o pasa inspiración.
Triggers: "vamos con HC-XXX", "nuevo post", "tengo esta inspiración", "adapta esta referencia", imágenes de inspiración adjuntas sin contexto previo de Fase B.

**Fase B** → Gibran dice que las imágenes ya están listas.
Triggers: "ya están las imágenes", "ya puse las imágenes", "imágenes listas", "súbelas al hub", "ya tengo los winners".

Si hay ambigüedad, preguntar en cuál fase está. Máximo 1 pregunta.

---

## FASE A — CONCEPTO → BRIEF + PROMPTS HTML

### A1. Recopilar inputs

Antes de hacer nada, confirmar:

1. **Post ID** — HC-XXX. Si no lo menciona, leer el calendario xlsx para encontrar el siguiente disponible:
   ```python
   CALENDAR = "HC - HEALTHY CHUCHOS/HC - 06. SOCIAL MEDIA/MARZO ABRIL/HC_SOCIAL_MEDIA_CALENDAR.xlsx"
   df = pd.read_excel(CALENDAR, sheet_name="CALENDARIO", header=2)
   # Encontrar el primer ID con STATUS vacío o "Pendiente" sin imágenes aún
   ```

2. **Inspiración** — Imágenes adjuntas por Gibran y/o descripción en texto. Analizar visualmente si hay imágenes.

3. **Concepto/ángulo** — Lo que Gibran quiere comunicar. Inferir del contexto si es claro.

4. **Producto** — ArtriDog / DogRelax / GastroDog / OmegaDog (o "ninguno" para Pilar 2 sin product reveal). Si hay producto, verificar si hay mockup disponible en `02. PRODUCTOS/03. MOCK UPS/`.

5. **Pilar** — Inferir del concepto:
   - Pilar 1 (CIENCIA LIGHT): educativo, ingredientes, ciencia, mecanismo de acción
   - Pilar 2 (RELATABLE/HUMOR): situaciones del dueño, memes, humor, storytelling
   - Pilar 3 (BRAND/AUTORIDAD): Monse, detrás de cámaras, transparencia de fórmula

6. **Número de slides** — Default: 5-6 para Pilar 2, 4-5 para Pilar 1, 3-4 para Pilar 3.

Si el concepto es claro desde el mensaje inicial, NO preguntar todo de nuevo — inferir y continuar.

### A2. Leer reglas de marca

Leer SIEMPRE antes de crear el brief:
```
BASE_SOCIAL = "HC - HEALTHY CHUCHOS/HC - 06. SOCIAL MEDIA/"
BASE_BRAND  = "HC - HEALTHY CHUCHOS/HC - 00. BRAND/00. VISUAL IDENTITY/"
- {BASE_BRAND}HC_GRID_SYSTEM_v7.md — Sistema visual del feed (paleta dual + 12 layouts) ← FUENTE DE VERDAD del feed
- {BASE_SOCIAL}HC_VISUAL_RULES.md — Reglas de producto, formato, errores comunes
- {BASE_SOCIAL}HC_SOCIAL_MEDIA_BRAND_GUIDE.md — Arquitectura 3-tier, pilares, voz
```

**OBLIGATORIO:** elegir uno de los 12 layouts del v7 (L1-L12) ANTES de escribir el brief. Si ningún layout calza, parar y preguntar a Gibran si abrimos un L13. NO inventar layouts fuera del catálogo.

Si hay producto, también leer:
```
- HC - HEALTHY CHUCHOS/HC - 02. PRODUCTOS/02. PRODUCT LOG GLOBAL/HC_PRODUCTS_LOG_GLOBAL_v2.xlsx
```
Para extraer claims verificados del producto (ingredientes, beneficios, compliance language).

### A3. Crear estructura de carpetas

Determinar la semana correcta según la fecha planificada en el calendario.

```bash
SEMANA_DIR = "HC - HEALTHY CHUCHOS/HC - 06. SOCIAL MEDIA/MARZO ABRIL/SEMANA X"
POST_DIR   = "{SEMANA_DIR}/HC-XXX"

mkdir -p "{POST_DIR}/01. BRIEF"
mkdir -p "{POST_DIR}/02. PROMPTS"
mkdir -p "{POST_DIR}/00. IMAGENES FINALES"
mkdir -p "{POST_DIR}/03. WF ITERACIONES"
mkdir -p "{POST_DIR}/INSPIRACION"
```

Si hay imágenes de inspiración adjuntas, copiarlas a `INSPIRACION/`.

### A4. Escribir el brief

Archivo: `{POST_DIR}/01. BRIEF/HC-XXX_BRIEF.md`

**Estructura obligatoria:**

```markdown
# HC-XXX | BRIEF — "{Título del concepto}"

## DATOS DEL POST

| Campo | Valor |
|---|---|
| **ID** | HC-XXX |
| **Producto** | {Producto o "Ninguno"} |
| **Pilar** | {1/2/3} — {NOMBRE PILAR} |
| **Funnel** | {TOFU/MOFU/BOFU} |
| **Formato** | Carrusel {N} slides |
| **Grid Layout v7** | {L1-L12} — {layout ID, ej. "L2 teal-blob-photo"} ← OBLIGATORIO |
| **Color base** | {teal / naranja / cream} ← debe coincidir con el layout |
| **Color acento** | {color contrario al base} |
| **Raza protagonista** | {Raza del perro elegida — debe ser reconocible} |
| **Ángulo** | {El ángulo creativo en una línea} |
| **Mood** | {Mood general del post} |
| **Semana** | {N} — {Mes} 2026 |

## CONCEPTO CREATIVO

{Premisa del post en 2-3 párrafos. Explica la narrativa, el personaje, el giro. Qué hace que esto sea relatable. Qué referencia visual se está adaptando.}

**Adaptación a sistema v7 (obligatorio):**
- Layout v7: {L1-L12 — descrito en HC_GRID_SYSTEM_v7.md}
- Color base del slot: {teal #1A9B8C / naranja #E8852E / cream #FFFCEF}
- Color acento (siempre el contrario del base): {teal o naranja}
- Logo HC chip cream TL + slot number TR: presentes (no negociar)
- Foto en cutout (circle / blob / blob B&N para L1)
- Headline Nunito 900 con underline accent del color contrario
- Brand shapes solo del catálogo permitido (paw, dots, squiggle, bubble, mega, donut, block)
- {Cualquier elemento de la inspiración que deba traducirse a paleta HC}

## NARRATIVA SLIDE A SLIDE

### SLIDE 1 — {NOMBRE SLIDE}

**Visual:** {Descripción detallada de lo que debe aparecer en la imagen}
**Texto en imagen:**
- {Línea 1}
- {Línea 2 si aplica}
**Mood:** {Mood específico de esta slide}

### SLIDE 2 — {NOMBRE SLIDE}
{... repetir para cada slide}

## CAPTION

{Caption completo listo para publicar. Ver reglas en sección CAPTION RULES más abajo.}

## NOTAS ESTRATÉGICAS

- **Pilar {N} compliance:** {Regla específica del pilar — ej. "Producto aparece SOLO en slides 5-6"}
- **Grid Identity v7:** Layout {L#} elegido. Naranja + teal coexisten. Logo TL + slot # TR. Foto cutout. Headline con underline accent.
- **Disfraz/elemento especial:** {Si hay elemento visual inusual, describir exactamente}
- **Consistencia del perro:** {Descripción canónica del perro protagonista para usar en TODOS los prompts}
- **Compliance:** {Notas de lenguaje correcto para claims del producto}

## ASSETS NECESARIOS

| Asset | Ruta | Estado |
|---|---|---|
| {Mockup producto} | {Ruta} | {Disponible / Buscar} |
| {Referencia inspiración} | {Ruta} | {Disponible} |
```

**CAPTION RULES (para escribir el caption del brief y del calendario):**
- Estructura: Hook impactante → Desarrollo relatable (2-3 párrafos) → Ciencia/producto (si aplica) → CTA → Disclaimer → Hashtags
- Longitud: mín 100 palabras, ideal 150-250
- Pilar 2: el producto entra TARDE en el caption, después de establecer el humor
- Compliance SIEMPRE: "apoya / contribuye a / ayuda a manejar / apoyo natural" — NUNCA "cura / trata / elimina / sustituye"
- MV (no MVZ): "Formulado por una Médica Veterinaria" / "Consulta a tu MV"
- Hashtags: 5-8 relevantes, mezcla producto + condición + marca
- Español correcto: revisar tildes, ñ, signos de apertura (¡ ¿) antes de entregar

### A5. Generar el HTML de prompts Gemini

Archivo: `{POST_DIR}/02. PROMPTS/HC-XXX_GEMINI_PROMPTS.html`

**Reglas absolutas de los prompts:**

1. **100% INDEPENDIENTES** — Cada prompt se pegará en un tab separado de gemini.google.com/app. NUNCA referenciar "la imagen anterior", "el mismo perro de arriba", "usa la misma composición". Cada prompt debe describir COMPLETAMENTE:
   - Todos los personajes (especie, raza, color de pelo, tamaño, expresión, pose)
   - Fondo completo (color, elementos, iluminación)
   - Composición (posición de cada elemento)
   - Texto que debe aparecer EN la imagen (fuente, posición, color)
   - Estilo fotográfico / de ilustración

2. **ABSOLUTE TEXT RULE** — TODO el texto que aparecerá en la imagen va DENTRO del prompt de Gemini. NUNCA se agrega texto con HTML/CSS post-generación. Si el texto es parte del diseño del slide, describirlo en el prompt.

3. **HYPERREALISM BLOCK** — Para cualquier perro en el prompt, incluir este bloque:
   ```
   Shot on Sony A7R IV with 85mm f/1.4 lens, professional studio lighting,
   hyperrealistic fur texture, photorealistic render, 8K resolution,
   award-winning pet photography style.
   ```

4. **PALETA HC** — Nunca indicar colores ajenos a la paleta. Siempre:
   - Navy: `deep navy blue #1A1464`
   - Orange: `warm orange #E8852E`
   - Cream: `warm cream #FFFCEF`
   - Teal: `teal #1A9B8C`
   - DogRelax Green: `sage green #97A25A`

5. **3 VARIACIONES** — Al final de cada prompt, indicar: `Generate 3 variations of this image.`

**Estructura del HTML:**

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>HC-XXX — Prompts Gemini</title>
  <style>
    /* Dark theme */
    body { background: #0d1117; color: #e6edf3; font-family: -apple-system, sans-serif; padding: 24px; }
    h1 { color: #58a6ff; }
    .slide-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; margin-bottom: 24px; }
    .slide-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #8b949e; margin-bottom: 8px; }
    .slide-title { font-size: 18px; font-weight: 700; margin-bottom: 16px; color: #f0f6fc; }
    .attachments { background: #1c2128; border-left: 3px solid #e8852e; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px; }
    .attachments strong { color: #e8852e; font-size: 12px; text-transform: uppercase; }
    .attachments ul { margin: 8px 0 0; padding-left: 20px; color: #c9d1d9; }
    .prompt-area { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 16px; font-family: monospace; font-size: 13px; line-height: 1.6; white-space: pre-wrap; max-height: 400px; overflow-y: auto; margin-bottom: 12px; color: #e6edf3; }
    .copy-btn { background: #238636; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; transition: all 0.2s; }
    .copy-btn:hover { background: #2ea043; }
    .copy-btn.copied { background: #388bfd; }
  </style>
</head>
<body>
  <h1>HC-XXX — Prompts Gemini</h1>
  <p style="color:#8b949e;">Pega cada prompt en un <strong>tab separado</strong> de gemini.google.com/app con los attachments indicados. Genera 3 variaciones por slide.</p>

  <!-- Un card por slide -->
  <div class="slide-card">
    <div class="slide-label">Slide 1</div>
    <div class="slide-title">HOOK — Título del slide</div>
    <div class="attachments">
      <strong>📎 Adjuntar con este prompt:</strong>
      <ul>
        <li>Referencia de inspiración: INSPIRACION/Screenshot_xxx.png</li>
        <li>Mockup producto (si aplica): 02. PRODUCTOS/03. MOCK UPS/DogRelax.jpeg</li>
      </ul>
    </div>
    <div class="prompt-area" id="prompt-s1">
{PROMPT COMPLETO AQUÍ}
    </div>
    <button class="copy-btn" onclick="copyPrompt('prompt-s1', this)">Copiar prompt</button>
  </div>

  <script>
    function copyPrompt(id, btn) {
      const text = document.getElementById(id).innerText;
      navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = '✓ Copiado';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = original;
          btn.classList.remove('copied');
        }, 2500);
      }).catch(() => {
        const area = document.getElementById(id);
        const range = document.createRange();
        range.selectNodeContents(area);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
        document.execCommand('copy');
        btn.textContent = '✓ Copiado (fallback)';
        setTimeout(() => { btn.textContent = 'Copiar prompt'; }, 2500);
      });
    }
  </script>
</body>
</html>
```

**Attachments por slide:**
- Slides con perro protagonista: imagen de inspiración de referencia (si existe)
- Slide con producto: mockup del producto (OBLIGATORIO para que Gemini reproduzca el packaging correcto)
- Slide sin perro ni producto: indicar "Sin adjuntos necesarios"

### A6. Entrega al usuario

```
Brief listo: [HC-XXX_BRIEF.md](ruta/al/brief)
open "ruta completa al brief"

Prompts HTML listo: [HC-XXX_GEMINI_PROMPTS.html](ruta/al/html)
open "ruta completa al html"

Siguiente paso:
1. Abre el HTML y copia cada prompt (botón azul)
2. En gemini.google.com/app, abre un tab por slide
3. Adjunta las imágenes indicadas en el card de cada prompt
4. Genera 3 variaciones por slide
5. Guarda las iteraciones en 03. WF ITERACIONES/
6. Pon los winners finales en 00. IMAGENES FINALES/
7. Cuando tengas todos los winners, dime "ya están las imágenes" y yo termino el post
```

---

## FASE B — IMÁGENES → FINALIZACIÓN

### B1. Listar imágenes disponibles

```python
import os
IMAGENES_DIR = "{POST_DIR}/00. IMAGENES FINALES"
imgs = sorted([f for f in os.listdir(IMAGENES_DIR) if f.endswith('.png') and not f.startswith('.')])
# Mostrar al usuario con índices
```

### B2. Confirmar orden del carrusel

Si las imágenes tienen nombres descriptivos (ej. `hook.png`, `reveal.png`) → inferir orden del brief.

Si tienen nombres genéricos (ej. `1.png`, `2.png`) → mostrar la lista y preguntar:
"¿Cuál es el orden correcto del carrusel? Ejemplo: 4→1→2→3→5"

Hacer MÁXIMO 1 pregunta. Si el orden se puede deducir del brief, hacerlo directamente.

### B3. Renombrar imágenes al orden correcto

Usar Python (`shutil.move()` — maneja Unicode en paths):

```python
import shutil, os
from pathlib import Path

orden = [...]  # Lista de archivos en orden correcto del carrusel
nombres_slide = ["hook", "slide2_nombre", "slide3_nombre", ...]  # Del brief

for i, (archivo, nombre) in enumerate(zip(orden, nombres_slide), 1):
    old = Path(IMAGENES_DIR) / archivo
    new = Path(IMAGENES_DIR) / f"{i:02d}_{nombre}.png"
    shutil.move(str(old), str(new))
    print(f"  {archivo} → {i:02d}_{nombre}.png")
```

### B4. Actualizar calendario xlsx

Leer la fila HC-XXX con openpyxl, actualizar:

```python
import openpyxl

path = "HC - HEALTHY CHUCHOS/HC - 06. SOCIAL MEDIA/MARZO ABRIL/HC_SOCIAL_MEDIA_CALENDAR.xlsx"
wb = openpyxl.load_workbook(path)
ws = wb['CALENDARIO']

# Encontrar header row (donde 'ID' columna es) y fila HC-XXX
# Columnas estándar: TIPO=6, PRODUCTO(S)=7, FORMATO=9, #SLIDES=10,
# ANGULO=11, HOOK=12, CAPTION=13, CTA TIPO=14, KEYWORD=15,
# DESTINO=16, STATUS=17, PROD STATUS=18, NOTAS=29

updates = {
    col_TIPO:       tipo_valor,            # "Relatable/Humor" / "Educativo" / etc.
    col_PRODUCTO:   producto_upper,        # "DOGRELAX" / "ARTRIDOG" / etc.
    col_FORMATO:    "Carrusel",
    col_SLIDES:     n_slides,
    col_ANGULO:     angulo_del_brief,
    col_HOOK:       hook_primera_linea,
    col_CAPTION:    caption_completo,
    col_CTA_TIPO:   "Comenta KEYWORD",
    col_KEYWORD:    keyword,               # Palabra clave para el KW comment flow
    col_DESTINO:    f"DM quiz → {producto}",
    col_STATUS:     "Pendiente",
    col_PROD_STATUS: "Imágenes listas",
    col_NOTAS:      notas_breves,
}

for col, val in updates.items():
    ws.cell(row=hc_row, column=col).value = val
wb.save(path)
```

**Caption para el calendario (escribir fresh, no copy-paste del brief):**
- Revisar el borrador del brief como base
- Aplicar todas las CAPTION RULES de la Fase A
- Verificar acentos, ñ, signos de apertura (¡ ¿) antes de guardar
- KEYWORD para CTA: elegir palabra relacionada al problema (ej. RELAX, CALMA, ARTRI, OMEGA)

### B5. Ejecutar upload al Content Hub

```bash
cd "/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY"
python3 upload_post_to_hub.py HC-XXX review
```

El script:
1. Lee el calendario (HOOK + CAPTION ya actualizados en B4)
2. Encuentra las imágenes renombradas en `00. IMAGENES FINALES/`
3. Las sube a Supabase bucket `post-media` (path: `hc/HC-XXX/`)
4. Upserta el metaobject `content_item` en Shopify staging con `status=review`
5. Envía email de notificación a equipo HC + Gibran

### B6. Reporte final

```
✓ HC-XXX listo para aprobación

Imágenes subidas: {N} slides (ordenadas {01_hook → 0N_xxx})
Calendario actualizado: {fecha planificada}, producto {PRODUCTO}
Caption: {primeras 80 chars del hook}...

Portal Content Hub: https://yca1z0-wf.myshopify.com/pages/hc-stage
Tab: Pendientes — esperando aprobación de Monse
```

---

## Reglas Globales HC (nunca negociar)

| Regla | Detalle |
|---|---|
| **Gemini = web UI** | gemini.google.com/app — NO API. Cada prompt en tab separado |
| **Prompts 100% independientes** | Cada prompt describe TODO: perros, fondo, texto, composición, lighting |
| **ABSOLUTE TEXT RULE** | Todo texto en imagen → dentro del prompt Gemini. NUNCA overlay HTML/CSS |
| **Hyperrealism block** | Obligatorio en todo prompt que incluya perros |
| **3 variaciones** | Siempre pedir 3 variaciones. Ganador en `00. IMAGENES FINALES/` |
| **Pilar 2: producto casi invisible** | Slides 1-(N-2) = humor puro. Producto entra en slides finales solamente |
| **Grid System v7** | Naranja + teal coexisten en CADA tile de feed. Layout = uno de los 12 IDs (L1-L12) del v7. Ver `HC - 00. BRAND/00. VISUAL IDENTITY/HC_GRID_SYSTEM_v7.md` |
| **Paleta HC es sagrada** | Naranja #E8852E + Teal #1A9B8C en cada post. Cream #FFFCEF respiración. Navy #1A1464 solo en Slot E (L1 editorial) |
| **Compliance** | "apoya/contribuye/promueve" — NUNCA "cura/trata/elimina/sustituye" |
| **MV no MVZ** | "Médica Veterinaria" / "tu MV" — nunca "MVZ" |
| **Español correcto** | Acentos, ñ, ¡ ¿ obligatorios en todo copy |
| **Productos HC = polvo** | ArtriDog/DogRelax/GastroDog = polvo. OmegaDog = cápsulas rojo rubí |

---

## Paths Clave

```
BASE_HC     = "HC - HEALTHY CHUCHOS/"
SOCIAL_DIR  = "{BASE_HC}06. SOCIAL MEDIA/MARZO ABRIL/"
CALENDAR    = "{SOCIAL_DIR}HC_SOCIAL_MEDIA_CALENDAR.xlsx"
GRID_SYSTEM  = "{BASE_HC}00. BRAND/00. VISUAL IDENTITY/HC_GRID_SYSTEM_v7.md"
GRID_MOCKUP  = "{BASE_HC}00. BRAND/00. VISUAL IDENTITY/HC_GRID_MOCKUP_v7.html"
VISUAL_RULES = "{BASE_HC}06. SOCIAL MEDIA/HC_VISUAL_RULES.md"
BRAND_GUIDE  = "{BASE_HC}06. SOCIAL MEDIA/HC_SOCIAL_MEDIA_BRAND_GUIDE.md"
PRODUCT_LOG  = "{BASE_HC}02. PRODUCTOS/02. PRODUCT LOG GLOBAL/HC_PRODUCTS_LOG_GLOBAL_v2.xlsx"
MOCKUPS_DIR  = "{BASE_HC}02. PRODUCTOS/03. MOCK UPS/"
UPLOAD_SCRIPT = "SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/upload_post_to_hub.py"
PORTAL_URL   = "https://yca1z0-wf.myshopify.com/pages/hc-stage"

# Post-específico (reemplazar HC-XXX y SEMANA X)
POST_DIR    = "{SOCIAL_DIR}SEMANA X/HC-XXX/"
BRIEF       = "{POST_DIR}01. BRIEF/HC-XXX_BRIEF.md"
PROMPTS_HTML = "{POST_DIR}02. PROMPTS/HC-XXX_GEMINI_PROMPTS.html"
FINALES     = "{POST_DIR}00. IMAGENES FINALES/"
ITERACIONES = "{POST_DIR}03. WF ITERACIONES/"
INSPIRACION = "{POST_DIR}INSPIRACION/"
```
