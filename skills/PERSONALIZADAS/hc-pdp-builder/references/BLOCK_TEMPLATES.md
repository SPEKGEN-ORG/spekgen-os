# HC PDP Block Templates — 14 bloques parametrizados

Variables globales a sustituir en TODOS los bloques:
- `{PREFIX}` → prefijo CSS (ej: `gd-`)
- `{PREFIX_UPPER}` → prefijo para IDs/comentarios (ej: `GD`)
- `{PRIMARY}` → color hex principal (ej: `#8B0400`)
- `{MID}` → color hex intermedio (ej: `#B5382E`)
- `{LIGHT}` → color hex claro (ej: `#E8A090`)
- `{RGBA_BASE}` → valores RGB (ej: `139,4,0`)
- `{PRODUCT_NAME}` → nombre del producto (ej: `GastroDog`)
- `{PRODUCT_FULL}` → nombre completo (ej: `GastroDog — Regeneración Intestinal`)
- `{BRAND}` → `Healthy Chuchos`
- `{PRICE}` → precio (ej: `$549`)
- `{WEIGHT}` → peso neto (ej: `225g`)
- `{SERVINGS}` → porciones (ej: `45`)

---

## 01-BUYBOX.html — Hero BuyBox

**Comment**: `<!-- HC-{PREFIX_UPPER}-BUYBOX-001 | Hero BuyBox {PRODUCT_NAME} | Pegar en bloque Custom HTML de EComposer -->`
**Max-width**: 580px
**Purpose**: Complete hero buybox with pricing, features, dose tip, and Shopify native widget styling

**CSS Architecture**:
- `:root` block with CSS custom properties:
  - `--{PREFIX}grad-primary`: gradient 135deg with MID→LIGHT→PRIMARY (for checkmarks, pills)
  - `--{PREFIX}grad-accent`: gradient 135deg with PRIMARY→MID→LIGHT (for text gradients)
  - `--{PREFIX}ink`: #121216
  - `--{PREFIX}muted`: rgba(29,29,31,.58)
  - `--{PREFIX}brand`: {MID}
  - `--{PREFIX}brand-dark`: {PRIMARY}
  - `--{PREFIX}brand-light`: {LIGHT}

**Structure** (in order):
1. **Header row** (flex, gap 10px):
   - Pill NEW/Formulación Premium (gradient bg, white text, uppercase)
   - Pill "FORMULA VETERINARIA" (white bg, gradient text via background-clip)
2. **H1 product title** (2.6rem, weight 780, gradient text via background-clip)
3. **Subtitle** (1rem, muted color, max-width 480px): Product description with key ingredients + weight/porciones
4. **Price block**:
   - Price row: main price (2.3rem bold) + currency "MXN" + compare price (line-through) + discount badge (red gradient)
   - Price meta: checkmark SVG + "Envio gratis +$599 | MSI disponibles"
5. **Feature pills** (flex-wrap row, gap 8px):
   - 5 pills with checkmark SVG + ingredient/benefit text
   - Glassmorphism bg, backdrop-filter blur(8px), hover lift effect
   - SVG strokes use `url(#{PREFIX}GradIcon)` gradient
6. **Dose tip card** (flex row, gap 12px):
   - Icon box (38px, rounded 10px) with clock SVG
   - Text: "**1 cucharada (5g)** sobre su alimento | Efecto desde **[tiempo]**"
   - Glassmorphism with gradient border ::after

**SECOND `<style>` block — Shopify Native Widget CSS** (CRITICAL):
- Quantity selector: `.product-form__quantity`, `.quantity-selector`, `quantity-input` → pill shape (border-radius 999px), white bg, shadow
- ATC button: `.product-form__submit`, `button[name="add"]` → 56px height, pill shape, gradient bg with product colors, heavy shadow, hover lift
- Layout: `.product-form__buttons` → flex row with gap 14px
- All rules use `!important` to override Shopify theme
- Mobile @media(max-width:500px) → column layout

**Content to customize**: Pills text, subtitle, price, compare price, feature pills (ingredient-specific), dose timing

---

## 02-TRUST.html — Trust Badges + Métodos de Pago

**Comment**: `<!-- HC-{PREFIX_UPPER}-TRUST-003 | Trust Badges + Metodos de Pago | PDP A - Con logos reales -->`
**Max-width**: 680px
**Purpose**: Payment logos + shipping/trust cards below buybox

**CSS Architecture**:
- `:root` with `--{PREFIX}grad-primary`, `--{PREFIX}text-dark`, `--{PREFIX}text-gray`

**Structure** (TWO sections):

**Section 1 — Payment Logos Grid** (`.{PREFIX}pay-grid`):
- Label: "Pagos Seguros" (centered, uppercase, gray)
- Flex row of 5 logo tiles (70x45px each, glassmorphism):
  - Visa: `https://cdn.shopify.com/s/files/1/0768/1382/8348/files/VISA.png?v=1773343571`
  - American Express: `https://cdn.shopify.com/s/files/1/0768/1382/8348/files/AMERCIAN_EXPRESS.png?v=1773343571`
  - Mercado Pago: `https://cdn.shopify.com/s/files/1/0768/1382/8348/files/MERCADO_PAGO.png?v=1773343571`
  - PayPal: `https://cdn.shopify.com/s/files/1/0768/1382/8348/files/PAYPAL.png?v=1773343571`
  - OXXO: `https://cdn.shopify.com/s/files/1/0768/1382/8348/files/OXXO.png?v=1773343571`
- Hover: lift + scale img 1.1x + accent border-color

**Section 2 — Shipping/Trust Cards** (`.{PREFIX}ship-grid`, 3-col grid):
- 3 cards (glassmorphism, rounded 16px):
  1. Shield icon → "Pagos Rápidos y Seguros" / "Transacción **protegida**"
  2. Truck icon → "Envío Gratis" / "En compras +**$599**"
  3. Return icon → "Devolución 30 Días" / "**100%** garantizado"
- Each card: icon box (38px, gradient border ::after) + text block (h4 + p)
- SVG strokes use `url(#{PREFIX}GradTrust)` gradient

**Mobile** @media(max-width:600px): ship-grid → 1 col, pay tiles → 33% flex

**Content**: Payment logos are SHARED across all HC products (same URLs). Ship cards text is standard.

---

## 03-PROBLEMA.html — Estadísticas del Problema

**Comment**: `<!-- HC-{PREFIX_UPPER}-PROBLEMA | [Descripción del problema] | PDP A - Solo Iconos -->`
**Max-width**: 900px
**Purpose**: Creates urgency — the problem the product solves

**Structure**:
- Tag pill: "El Problema"
- H2 title with gradient highlight: Hook statement about the real problem
- Subtitle: 1-2 sentences expanding
- 3-column stat grid:
  - Each stat: icon box + big gradient number + description text
- Body note: Paragraph explaining why conventional solutions fail

**Content to customize per product**:
- 3 statistics relevant to the product's problem domain
- The hook H2 (should be provocative, challenging assumptions)
- The body note (why current approaches don't work)

**Example numbers**: "70%", "3x", "85%", "$2,500", "1 de 3"

---

## 04-MECANISMO.html — Mecanismo de Acción

**Comment**: `<!-- HC-{PREFIX_UPPER}-MECANISMO | [Fases/Mecanismo] | PDP A - Solo Iconos -->`
**Max-width**: 900px
**Purpose**: Explains how the product works (phases/steps)

**Structure**:
- Tag pill: "Cómo Funciona"
- H2 title: "[Mecanismo] en [N] fases"
- Subtitle: 1 sentence
- 3-column grid (one per phase):
  - Icon box
  - Phase number (big gradient)
  - Phase name (bold)
  - Timeframe label (uppercase micro: "Efecto: Horas/Días/Semanas")
  - Description (1-2 sentences)
- Synergy note: How phases work together

**Content to customize**: Phase names, timeframes, descriptions, mechanism summary

---

## 05-FORMULA.html — Ingredientes

**Comment**: `<!-- HC-{PREFIX_UPPER}-FORMULA | Fórmula [N] Activos | PDP A - Solo Iconos -->`
**Max-width**: 900px
**Purpose**: Ingredient cards with percentages and mechanisms

**Structure**:
- Tag pill: "La Fórmula"
- H2 title: "[N] activos, 0 rellenos"
- Subtitle: Brief formula philosophy
- Grid of ingredient cards (2 columns for ≤4 ingredients, adapt for 5+):
  - Each card: circular icon (72px) + ingredient name + percentage tag + mechanism description
- Note: "100% transparencia — cada ingrediente tiene su función"

**Content to customize**: Each ingredient name, percentage, icon, mechanism description

---

## 06-PERFILES.html — Perfiles de Paciente / Etapas de Vida

**Comment**: `<!-- HC-{PREFIX_UPPER}-PERFILES | [Título] | PDP A - Solo Iconos -->`
**Max-width**: 900px
**Purpose**: Shows who the product is for

**Structure**:
- Tag pill: "Para Todas las Etapas" o "Para Quién Es"
- H2 title with highlight
- Subtitle
- 3-5 profile cards (3-col grid, mobile 1-col):
  - Large circular icon (72px)
  - Profile name (bold)
  - Age/weight range (micro text, accent color, uppercase)
  - Description (1-2 sentences)

**Content varies by product**:
- DogRelax: Cachorros / Adultos / Seniors
- GastroDog: Diarrea crónica / Post-antibiótico / IBD / Sensible / Permeabilidad
- ArtriDog: Seniors / Deportistas / Razas grandes / Post-cirugía
- Adapt to product's ICP segments

---

## 07-VS.html — Tabla Comparativa

**Comment**: `<!-- HC-{PREFIX_UPPER}-VS | Comparativa vs Convencional | PDP A - Solo Iconos -->`
**Max-width**: 900px
**Purpose**: Differentiates product from conventional alternatives

**Structure**:
- Tag pill: "Comparativa"
- H2 title: "[Producto] vs Lo convencional"
- Table with 3 columns: Criterio / Convencional / {PRODUCT_NAME}
- 5-7 comparison rows
- Product column highlighted with accent color background
- Check marks (✓) for product advantages, X marks (✗) for conventional drawbacks

**Standard comparison criteria (adapt per product)**:
- Enfoque (sintomático vs causa raíz)
- Ingredientes (rellenos vs activos puros)
- Evidencia clínica
- Efectos secundarios
- Tiempo de resultados
- Palatabilidad
- Garantía

---

## 08-HOWTO.html — Guía de Uso

**Comment**: `<!-- HC-{PREFIX_UPPER}-HOWTO | Cómo Usarlo | PDP A - Solo Iconos -->`
**Max-width**: 900px
**Purpose**: Simple usage instructions + dosing chart

**Structure**:
- Tag pill: "Guía de Uso"
- H2 title: "Así de fácil"
- 3-step grid:
  1. Mide [cantidad] — icon: measuring cube
  2. Mezcla con su alimento — icon: cup/bowl
  3. [Resultado] en [tiempo] — icon: checkmark
- Dosing bar (flex row, mobile column):
  - 3-4 tiers by weight range: dose label + weight range

**Content to customize**: Step descriptions, number of dosing tiers, specific doses per weight, time to results

---

## 09-AUTORIDAD.html — Respaldo Científico

**Comment**: `<!-- HC-{PREFIX_UPPER}-AUTORIDAD | Respaldo Científico | PDP A - Solo Iconos -->`
**Max-width**: 900px
**Purpose**: Trust/authority signals

**Structure**:
- Tag pill: "Respaldo"
- H2 title: "Ciencia que respalda"
- Subtitle: Formulation/manufacturing claim
- 2x2 badge grid:
  - Each badge: icon box (48px, rounded 14px) + two-line text (strong title + span subtitle)
- Footer note: Manufacturing attribution

**Standard badges (same for all products)**:
1. COFEPRIS Registrado — Cumple normativa mexicana vigente
2. Greenmark Lab S.A. de C.V. — Laboratorio certificado en [ubicación]
3. [N]+ Estudios Clínicos — Evidencia en [contexto]
4. Lote Rastreable — Cada bote tiene número de lote y caducidad

**Content to customize**: Number of studies, specific evidence claims, lab location

---

## 10-GARANTIA.html — Garantía de Satisfacción

**Comment**: `<!-- HC-{PREFIX_UPPER}-GARANTIA | Garantía de Satisfacción | PDP A - Solo Iconos -->`
**Max-width**: 700px
**Purpose**: Risk reversal — money-back guarantee

**Structure**:
- Single hero card (horizontal layout, mobile vertical):
  - Large shield icon (96px circular)
  - Content area:
    - Tag pill: "Sin Riesgo"
    - Title: "Garantía de Satisfacción 30 Días" (with gradient highlight)
    - Description: Money-back promise
    - 3 numbered steps in flex row: Contáctanos → Envía el bote → Reembolso total

**Content mostly standard**: Only customize the description copy to reference the product's specific promise.

---

## 11-FAQ.html — Preguntas Frecuentes

**Comment**: `<!-- HC-{PREFIX_UPPER}-FAQ-00[N] | Preguntas Frecuentes Accordion | PDP A -->`
**Max-width**: 700px
**Purpose**: Address objections, improve SEO

**Structure**:
- Tag pill: "FAQ"
- H2 title: "Preguntas frecuentes" (with gradient highlight)
- Accordion list (6 items):
  - Each item: `div.{PREFIX}faq-item` container
  - Question: `div[role="button" tabindex="0" onclick="this.parentElement.classList.toggle('open')"]`
  - Answer: max-height transition from 0 to 300px on `.open` class
  - Chevron SVG rotates 180deg on open

**CRITICAL**: Use `<div>` NOT `<button>` for the question trigger. Shopify wraps custom HTML in a form, and `<button>` triggers form submit (add to cart).

**Standard FAQ topics (adapt answers per product)**:
1. ¿En cuánto tiempo veo resultados?
2. ¿Tiene efectos secundarios / lo seda?
3. ¿Qué talla/peso de perro puede tomarlo?
4. ¿Puedo darlo junto con su medicamento?
5. ¿A qué sabe? ¿Y si no le gusta?
6. ¿Cuánto dura un bote?

---

## 12-SCHEMA.html — JSON-LD Structured Data

**Comment**: `<!-- HC-{PREFIX_UPPER}-SCHEMA | JSON-LD Structured Data | PDP A -->`
**Purpose**: SEO structured data for Google rich results

**Structure**: Two `<script type="application/ld+json">` blocks:

**Block 1 — Product**:
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{PRODUCT_FULL}",
  "brand": {"@type": "Brand", "name": "{BRAND}"},
  "description": "[SEO description ~150 chars]",
  "category": "Suplementos para Mascotas > Perros > [Categoría]",
  "weight": {"@type": "QuantitativeValue", "value": "[grams]", "unitCode": "GRM"},
  "countryOfOrigin": {"@type": "Country", "name": "México"},
  "manufacturer": {"@type": "Organization", "name": "Greenmark Lab S.A. de C.V."},
  "additionalProperty": [
    {"@type": "PropertyValue", "name": "Formato", "value": "Polvo"},
    {"@type": "PropertyValue", "name": "Porciones", "value": "{SERVINGS}"},
    {"@type": "PropertyValue", "name": "Porción", "value": "5 g"}
  ]
}
```

**Block 2 — FAQPage**: Mirror the 6 FAQ items from 11-FAQ.html with proper `Question`/`Answer` schema entities.

---

## 13-STICKYATC.html — Sticky Add to Cart

**Comment**: `<!-- HC-{PREFIX_UPPER}-STICKYATC-002 | Sticky Add-to-Cart Bar {PRODUCT_NAME} | PDP A -->`
**Purpose**: Persistent purchase CTA on scroll

**Structure**:
- Fixed bar at bottom (z-index: 9999)
- Hidden by default, visible cuando `window.scrollY > 600` (scroll listener con rAF)
- Content: product thumbnail + name + price + qty selector + gradient CTA button

**JS Architecture** (CRÍTICO — NO modificar este patrón):

```
variantId detection (multi-estrategia):
  1. window.ShopifyAnalytics.meta.product
  2. select/input[name="id"] en el DOM
  3. ?variant= en la URL
  4. fetch('/products/[handle].js') → async

Cart add (AJAX — NUNCA usar submitBtn.click() ni form.submit()):
  fetch('/cart/add.js', { method:'POST', body: JSON.stringify({items:[{id,quantity}]}) })
  → then: refreshAndOpenDrawer()

refreshAndOpenDrawer():
  fetch('/?sections=' + HEADER_SECTION_ID)
  → reemplaza cart-drawer-component innerHTML con HTML actualizado
  → llama openDrawer()
  catch → openDrawer() directo

openDrawer() (4 estrategias en cascada):
  1. cart-drawer-component.open()
  2. dialog.showModal()
  3. dialog.setAttribute('open','')
  4. click en botón del header

HEADER_SECTION_ID:
  Hardcoded fallback: 'sections--19904143065340__header_section'
  detectHeaderSection() lo sobrescribe dinámicamente al init
```

**⚠️ NUNCA HACER ESTO — causa redirección a /cart page:**
```javascript
// ❌ INCORRECTO
var submitBtn = document.querySelector('form[action*="/cart/add"] button[type="submit"]');
if(submitBtn){ submitBtn.click(); }
else { var form = document.querySelector('form[action*="/cart/add"]'); if(form) form.submit(); }
```

**Referencia de código completo**: Copiar arquitectura JS de cualquier archivo en producción y adaptar prefijo + colores:
- GastroDog (`gd-`): `02. PRODUCTOS/06. GASTRODOG/07. PDPs/PDP_A_ICONOS/13-STICKYATC.html`
- ArtriDog (`ad-`): `02. PRODUCTOS/07. ARTRIDOG/07. PDPs/PDP_A_ICONOS/13-STICKYATC.html`
- OmegaDog (`od-`): `02. PRODUCTOS/09. OMEGADOG/07. PDPs/PDP_A_ICONOS/13-STICKYATC.html`

**Content to customize al generar nuevo producto**: Prefijo CSS, colores del gradiente del botón, nombre/precio de fallback hardcoded

---

## SEO-BODY-HTML-{PRODUCT_UPPER}.html — SEO Body HTML

**Comment**: `<!-- HC-{PREFIX_UPPER}-SEO | SEO Body HTML for Product Metafield -->`
**Purpose**: Semantic HTML for Shopify product body / metafield

**Structure**:
- `<article>` wrapper
- `<h1>` with product full name
- 5 `<h2>` sections:
  1. Qué es {PRODUCT_NAME}
  2. Ingredientes Clave
  3. Cómo Funciona
  4. Para Quién Es
  5. Modo de Uso
- Short paragraphs, natural keyword density
- NO inline styles — pure semantic HTML
- Keywords naturales relevant to product category

**Content to customize**: All paragraphs tailored to product data
