---
name: hc-pdp-builder
version: v002
description: "Genera los bloques HTML completos de una PDP (Product Detail Page) para cualquier producto de Healthy Chuchos en Shopify/EcomPoser. Crea 14 archivos HTML con design system glassmorphism, colores derivados de la etiqueta del producto, iconos SVG con gradientes, y contenido optimizado para conversión. ACTIVAR SIEMPRE cuando Gibran mencione: 'PDP de [producto]', 'bloques HTML de [producto]', 'página de producto de [producto]', 'genera la PDP', 'crea los bloques', 'siguiente PDP', 'PDP del OmegaDog', 'PDP del VistaChu', 'bloques para Shopify', 'HTML para EcomPoser', 'arma la página de producto', o cualquier solicitud de crear bloques HTML para una página de producto de Healthy Chuchos. También activar cuando se pida crear una PDP para cualquier producto HC (DogRelax, ArtriDog, GastroDog, OmegaDog, VistaChu)."
---

# HC PDP Builder — Generador de Product Detail Pages para Healthy Chuchos

## Qué hace este skill

Genera el set completo de 14 bloques HTML para una PDP en Shopify/EcomPoser. Cada bloque es un archivo HTML independiente que se pega en un bloque "Custom HTML" de EcomPoser. El design system es consistente entre productos pero cada uno tiene su paleta de colores derivada de su etiqueta.

## Workflow paso a paso

### PASO 0: Leer referencias del design system
Antes de generar CUALQUIER bloque, lee estos archivos de referencia:
- `references/DESIGN_SYSTEM.md` — Paleta de colores, CSS patterns, componentes, reglas responsive
- `references/BLOCK_TEMPLATES.md` — Los 14 bloques con estructura, contenido placeholder, y variaciones

### PASO 1: Identificar el producto y recopilar datos

1. **Identificar el producto**: Pregunta cuál producto si no está claro. Productos HC: DogRelax, ArtriDog, GastroDog, OmegaDog, VistaChu.

2. **Leer el contexto del producto**:
   - `HC - HEALTHY CHUCHOS/_CLIENT_CONTEXT.md` — Contexto general del cliente
   - `HC - HEALTHY CHUCHOS/HC - 02. PRODUCTOS/[NUM]. [PRODUCTO]/` — Carpeta del producto

3. **Extraer datos del Products Log Global**:
   Ubicación: `HC - HEALTHY CHUCHOS/HC - 02. PRODUCTOS/02. PRODUCT LOG GLOBAL/HC_PRODUCTS_LOG_GLOBAL_v2.xlsx`

   Datos necesarios del Excel:
   - Nombre completo del producto
   - Subtítulo / claim principal
   - Ingredientes con porcentajes
   - Mecanismo de acción (fases)
   - Dosificación por peso
   - Perfiles de paciente / ICP
   - Precio
   - Peso neto y porciones
   - Claims aprobados
   - Evidencia científica / estudios

4. **Leer el Image Brief** si existe:
   `[PRODUCTO]/07. PDPs/` o archivos subidos por Gibran con el brief de imágenes PDP.

### PASO 2: Determinar la paleta de colores

Cada producto tiene UN color accent derivado de su etiqueta. Este color genera una paleta de 3 stops para gradientes:

| Producto | Color Etiqueta | Primary | Mid | Light | RGBA |
|----------|---------------|---------|-----|-------|------|
| DogRelax | Verde olivo | `#6B7A3A` | `#97A25A` | `#D4DE94` | `107,122,58` |
| ArtriDog | Azul teal | `#2D5B64` | `#42838F` | `#5A9DA8` | `66,131,143` |
| GastroDog | Rojo oscuro | `#8B0400` | `#B5382E` | `#E8A090` | `139,4,0` |
| OmegaDog | Morado | `#3D0F6B` | `#7B3FAE` | `#CAB2DF` | `61,15,107` |
| VistaChu | (preguntar) | — | — | — | — |

**Regla de derivación**: Si solo tienes el color primary (de la etiqueta), genera Mid y Light así:
- **Mid**: Mezcla del primary con ~40% blanco, reduciendo saturación ligeramente
- **Light**: Mezcla del primary con ~70% blanco, mucho más suave/pastel

Si el color no está en la tabla, SIEMPRE pregunta a Gibran: "¿Cuál es el color accent de la etiqueta de [PRODUCTO]? (hex)"

### PASO 3: Definir el prefijo CSS

Cada producto tiene un prefijo de 2 letras para TODAS las clases CSS:

| Producto | Prefijo |
|----------|---------|
| DogRelax | `dr-` |
| ArtriDog | `ad-` |
| GastroDog | `gd-` |
| OmegaDog | `od-` |
| VistaChu | `vc-` |

### PASO 4: Generar los 14 bloques HTML

Lee `references/BLOCK_TEMPLATES.md` para la estructura exacta de cada bloque. Genera en este orden:

```
01-BUYBOX.html       → Buybox suplementario (badges + trust pills)
02-TRUST.html        → Barra de confianza horizontal
03-PROBLEMA.html     → Stats del problema (3 columnas)
04-MECANISMO.html    → Mecanismo de acción (fases)
05-FORMULA.html      → Cards de ingredientes
06-PERFILES.html     → Perfiles de paciente / etapas de vida
07-VS.html           → Tabla comparativa vs convencional
08-HOWTO.html        → Guía de uso (3 pasos + dosificación)
09-AUTORIDAD.html    → Badges de autoridad (COFEPRIS, lab, estudios)
10-GARANTIA.html     → Garantía de satisfacción 30 días
11-FAQ.html          → Accordion de 6 preguntas frecuentes
12-SCHEMA.html       → JSON-LD (Product + FAQPage)
13-STICKYATC.html    → Sticky Add to Cart bar
SEO-BODY-HTML-[PRODUCTO].html → HTML semántico para SEO
```

### PASO 5: Guardar archivos

Ubicación de destino:
```
HC - HEALTHY CHUCHOS/HC - 02. PRODUCTOS/[NUM]. [PRODUCTO]/07. PDPs/PDP_A_ICONOS/
```

Antes de guardar, hacer `ls` del directorio destino para verificar si ya existen archivos.

### PASO 6: Verificación QA

Después de generar todos los bloques:
1. Verificar que TODOS los archivos usan el prefijo CSS correcto
2. Verificar que NINGÚN archivo tiene colores de otro producto
3. Verificar que no hay palabras prohibidas de compliance ("cura", "antibiótico", "medicamento", "trata", "elimina")
4. Verificar que cada SVG tiene su `<defs><linearGradient>` definido
5. Verificar que los `@media(max-width:680px)` están presentes en cada archivo
6. Contar archivos: deben ser exactamente 14
7. **Verificar que el 13-STICKYATC usa AJAX Cart API** — ver sección "Reglas del Sticky ATC" abajo

## Reglas de compliance (CRÍTICO)

Lenguaje PERMITIDO: "apoya", "contribuye", "ayuda a mantener", "promueve", "favorece"
Lenguaje PROHIBIDO: "cura", "trata", "elimina", "antibiótico", "medicamento", "droga", "fármaco"

Estos son suplementos nutricionales, NO medicamentos. Nunca hacer claims médicos directos.

## Reglas de código HTML

1. **NO usar `<button>`** para interacciones — usar `<div role="button" tabindex="0">` con onclick. Razón: en Shopify, `<button>` dentro de un form dispara submit (agregar al carrito).
2. **CSS inline en `<style>`** al inicio de cada archivo — no archivos CSS externos.
3. **SVG inline** con gradientes definidos en `<defs>` — no imágenes externas.
4. **Font stack**: `'Inter',system-ui,-apple-system,sans-serif`
5. **Sin dependencias externas**: ni JS libraries, ni CSS frameworks, ni CDN links.
6. **Cada bloque es 100% independiente**: puede pegarse en cualquier orden en EcomPoser.

## Convención de comentarios HTML

Cada archivo inicia con un comentario identificador:
```html
<!-- HC-[PREFIX]-[BLOCK] | [Descripción] | PDP A - Solo Iconos -->
```
Ejemplo: `<!-- HC-GD-PROBLEMA | Síntomas Digestivos | PDP A - Solo Iconos -->`

---

## ⚠️ Reglas del Sticky ATC (13-STICKYATC.html) — CRÍTICO

### El problema que NO debes reproducir

El método INCORRECTO hace `submitBtn.click()` o `form.submit()`. Esto causa que en algunos temas de Shopify el usuario sea **redirigido a la página /cart** en lugar de abrir el cart drawer lateral.

```javascript
// ❌ INCORRECTO — NUNCA USAR ESTO
var submitBtn = document.querySelector('form[action*="/cart/add"] button[type="submit"]');
if(submitBtn){ submitBtn.click(); }  // puede redirigir a /cart
else { var form = document.querySelector('form[action*="/cart/add"]'); if(form) form.submit(); } // siempre redirige
```

### El método CORRECTO: AJAX Cart API + cart drawer

El Sticky ATC SIEMPRE debe:
1. Agregar al carrito vía **`fetch('/cart/add.js')`** (AJAX — sin navegación)
2. Refrescar el drawer via **Section Rendering** (`fetch('/?sections=' + HEADER_SECTION_ID)`)
3. Abrir el drawer con **`openDrawer()`** (multi-estrategia)

### Estructura JS obligatoria para 13-STICKYATC.html

```javascript
(function(){
  'use strict';

  var SCROLL_THRESHOLD = 600;
  var FEEDBACK_MS      = 2200;

  // HARDCODED fallback — confirmado funcional en healthychuchos.com
  // detectHeaderSection() lo sobrescribe dinámicamente si lo encuentra
  var HEADER_SECTION_ID = 'sections--19904143065340__header_section';

  var variantId = null;
  var qty = 1;

  /* --- Detección de variant (multi-estrategia) --- */
  function tryShopifyAnalytics(){ /* window.ShopifyAnalytics.meta.product */ }
  function tryFormInput(){ /* select[name="id"], input[name="id"], etc */ }
  function tryURLParam(){ /* ?variant=XXXXXXX en la URL */ }
  function tryProductJSON(){ /* fetch('/products/[handle].js') */ }
  function detectProduct(){ /* prueba en orden, async fallback */ }

  /* --- Detección dinámica del section ID del header --- */
  function detectHeaderSection(){
    // 1. cart-items-component[data-section-id]
    // 2. .shopify-section-group-header-group
    // 3. [id^="shopify-section-"] que contenga cart-drawer-component
    // fallback: HEADER_SECTION_ID hardcoded
  }

  /* --- AJAX add to cart --- */
  function doAdd(){
    fetch('/cart/add.js', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ items: [{ id: parseInt(variantId), quantity: qty }] })
    })
    .then(function(res){ return res.ok ? res.json() : res.json().then(function(e){ throw e; }); })
    .then(function(){ refreshAndOpenDrawer(); })  // ← abre el drawer, NO redirige
    .catch(function(){ /* mostrar error en el btn */ });
  }

  /* --- Section Rendering + open drawer --- */
  function refreshAndOpenDrawer(){
    fetch('/?sections=' + HEADER_SECTION_ID)
      .then(function(res){ return res.json(); })
      .then(function(sections){
        // Reemplazar el HTML del cart-drawer-component con la versión actualizada
        // luego llamar openDrawer()
      })
      .catch(function(){ openDrawer(); }); // fallback: abrir sin refresh
  }

  function openDrawer(){
    var drawer = document.querySelector('cart-drawer-component');
    // Estrategia 1: drawer.open() (método nativo del custom element)
    // Estrategia 2: dialog.showModal()
    // Estrategia 3: dialog.setAttribute('open','')
    // Estrategia 4: click en el botón del header
  }

})();
```

### Referencia de implementación completa

Ver archivos funcionales en producción:
- `HC - HEALTHY CHUCHOS/HC - 02. PRODUCTOS/06. GASTRODOG/07. PDPs/PDP_A_ICONOS/13-STICKYATC.html` (GastroDog — prefijo `gd-`)
- `HC - HEALTHY CHUCHOS/HC - 02. PRODUCTOS/07. ARTRIDOG/07. PDPs/PDP_A_ICONOS/13-STICKYATC.html` (ArtriDog — prefijo `ad-`)
- `HC - HEALTHY CHUCHOS/HC - 02. PRODUCTOS/09. OMEGADOG/07. PDPs/PDP_A_ICONOS/13-STICKYATC.html` (OmegaDog — prefijo `od-`, corregido v002)

Al generar un nuevo Sticky ATC, **copiar la arquitectura JS de cualquiera de estos archivos** y solo cambiar:
- El prefijo CSS (`gd-` → `od-` → `ad-` etc.)
- Los colores del gradiente del botón
- El nombre/precio hardcoded de fallback
- Los `known handles` si usas la estrategia de fallback por handle

### Checklist QA para el Sticky ATC

- [ ] El botón CTA usa `fetch('/cart/add.js')` — NO `.click()` ni `form.submit()`
- [ ] `refreshAndOpenDrawer()` se llama después de un add exitoso
- [ ] `HEADER_SECTION_ID` tiene el valor hardcoded `sections--19904143065340__header_section`
- [ ] `detectHeaderSection()` está implementada para sobrescribir dinámicamente
- [ ] `openDrawer()` tiene las 4 estrategias en cascada
- [ ] El selector de cantidad es un `<div>` con `textContent`, NO un `<input type="number">`
- [ ] El botón CTA es `<div role="button" tabindex="0" onclick="...">` — NO `<button>`
