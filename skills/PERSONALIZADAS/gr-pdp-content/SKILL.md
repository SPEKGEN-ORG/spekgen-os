# /gr-pdp-content — Genera template JSON para PDP Landing de GreenRay

> v2.0 — Skill completa para generar el archivo `templates/product.gr-{slug}.json` con todo el contenido específico de un producto, listo para deploy.

## Argumento
Nombre del producto (ej. "BELLSAN Ultra", "HORMO FX M40+", "DETOX FX").

## Rutas base

```
GR_ROOT    = /Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/GR - GREENRAY
THEME_DIR  = {GR_ROOT}/04. WEBSITE/greenray-theme
FT_DIR     = {GR_ROOT}/02. PRODUCTOS/02. FICHAS TECNICAS
LOG_FILE   = {GR_ROOT}/02. PRODUCTOS/00. PRODUCT LOG GLOBAL/GR_PRODUCTS_LOG_GLOBAL_v1.0.xlsx
KB_FILE    = {GR_ROOT}/_KNOWLEDGE_BASE.md
ENV_FILE   = {GR_ROOT}/.env
REF_TMPL   = {THEME_DIR}/templates/product.gr-landing.json
OUTPUT     = {THEME_DIR}/templates/product.gr-{slug}.json
```

---

## FASE 0 — Pre-flight (automático, no preguntar)

1. **Leer `.env`** para tener `SHOPIFY_ACCESS_TOKEN` disponible (no mostrar)
2. **Buscar producto en Shopify API**: `GET /admin/api/2024-01/products.json?title={nombre}` o por handle. Extraer:
   - `product_id`, `handle`, `title`
   - `variants[0].price`, `variants[0].compare_at_price`
   - `variants[0].inventory_quantity`
   - `product.images` (contar cuántas tiene)
   - `product.collections` (via `GET /admin/api/2024-01/collects.json?product_id={id}`)
3. **Verificar stock**: Si `inventory_quantity == 0`, AVISAR pero continuar (el PDP sirve para SEO)
4. **Leer Product Log Global** (xlsx): buscar si el producto ya tiene fila. Extraer ingredientes, indicaciones, ángulos copy, NO usar
5. **Buscar Product Brief**: `{GR_ROOT}/02. PRODUCTOS/_PRODUCT_BRIEF_{NOMBRE}.md`. Si no existe, AVISAR que se recomienda `/product-research` primero pero NO detenerse — usar FT directamente
6. **Leer Knowledge Base**: buscar sección del producto para datos verificados y errores conocidos
7. **Leer Ficha Técnica**: Buscar PDF en `FT_DIR/` que contenga el nombre del producto
   - Intentar `extract_text()` primero
   - Si devuelve solo "Ficha Técnica" o texto mínimo → es PDF image-based → extraer imágenes embedded via pypdf y leerlas visualmente
   - NOTA: las FTs de GreenRay son slides diseñados exportados como imágenes dentro del PDF
8. **Leer template de referencia** (`product.gr-landing.json`) para mantener la estructura exacta

---

## FASE 1 — Generación de contenido

### Settings principales

| Setting ID | Regla | Ejemplo (Gaxaliv) |
|---|---|---|
| `product_subtitle` | 1 oración con ingredientes diferenciadores. Max 120 chars. Empezar con verbo de acción. | "Restaura tu arquitectura intestinal con 8 cepas probióticas + berberina + extracto de guayaba." |
| `badge_rating` | "4.7" a "4.9" — variar entre productos | "4.8" |
| `badge_count` | "80+" a "200+" — proporcional a popularidad estimada | "120+" |
| `badge_label` | Categoría del producto (2-3 palabras) | "Salud Digestiva" |
| `show_social_proof` | Siempre `true` | `true` |

### Settings de secciones

| Setting ID | Regla |
|---|---|
| `symptoms_eyebrow` | "Identificación" (fijo) |
| `symptoms_title` | Pregunta directa: "¿Tu [órgano/sistema] te está pidiendo ayuda?" |
| `symptoms_subtitle` | Empatía + autoridad. "Señales reales de que tu [sistema] necesita [acción]" |
| `ingredients_eyebrow` | "Formulación Premium" (fijo) |
| `ingredients_title` | Resumen cuantificable: "X ingredientes activos + Y fitoactivos" |
| `ingredients_subtitle` | Diferenciador técnico: por qué NO es genérico |
| `testimonials_eyebrow` | "Resultados Reales" (fijo) |
| `testimonials_title` | "Ellos ya [verbo de resultado]" |
| `testimonials_subtitle` | "Historias de personas que eligieron [beneficio] de forma natural." |
| `howitworks_eyebrow` | "¿Cómo funciona?" (fijo) |
| `howitworks_title` | "3 pasos para [resultado principal]" |
| `howitworks_subtitle` | Dosis exacta de la FT (ej. "Una cápsula, dos veces al día, antes de alimentos.") |

### Benefit Bullets (4) — Los argumentos de venta más fuertes

```
benefit_1 → Ingrediente diferenciador principal del producto (lo que lo hace único)
benefit_2 → Timeline de resultados ("Resultados desde la semana X")
benefit_3 → "Envío gratis en pedidos +$1,500" (fijo para todos)
benefit_4 → "Garantía de satisfacción 30 días" (fijo para todos)
```

### How It Works (3 pasos)

| Step | Patrón | Timeline |
|---|---|---|
| `step1` | **Fase de entrada** — qué pasa cuando el ingrediente llega al cuerpo. Mecanismo de absorción/activación. | Día 1-3 |
| `step2` | **Fase de acción** — mecanismo principal. Pathway molecular si está en la FT. | Semana 1-2 |
| `step3` | **Fase de resultado** — beneficios observables. Ser específico. | Semana 2-4 |

### Us vs Them — Comparativa (PERSONALIZAR por categoría)

| Setting | Regla |
|---|---|
| `vs_eyebrow` | "Comparativa" (fijo) |
| `vs_title` | "¿Por qué elegir [nombre producto]?" |
| `vs_subtitle` | "No todos los [categoría] son iguales. La diferencia está en la formulación." |
| `vs_them_label` | Categoría genérica del competidor: "Probióticos Genéricos", "Colágenos de Farmacia", "Multivitamínicos Comerciales" |
| `vs_them_title` | "Lo que encuentras en farmacia" |
| `vs_them_1..5` | 5 debilidades REALES de alternativas genéricas (ingredientes pobres, dosis bajas, sin sinergia, sin respaldo, efectos lentos) |
| `vs_us_label` | Nombre exacto del producto |
| `vs_us_title` | "Formulación premium" o "Ingeniería [tipo]" |
| `vs_us_1..5` | 5 fortalezas VERIFICADAS del producto que contrasten directamente con los `vs_them` |

**REGLA**: Cada `vs_us_X` debe ser la contraparte directa de `vs_them_X`. Si them dice "dosis bajas" → us dice la dosis real.

### FAQ — 6 preguntas (ADAPTAR las respuestas al producto)

| # | Pregunta (patrón) | Respuesta (adaptar) |
|---|---|---|
| Q1 | "¿Cuántas cápsulas trae y cuánto dura?" | De la FT: presentación, dosis diaria, duración del frasco |
| Q2 | "¿Cuánto tarda en hacer efecto?" | Alinear con step2/step3 del How It Works |
| Q3 | "¿Puedo tomarlo junto con otros medicamentos?" | Siempre: "Es suplemento alimenticio seguro. Consulta a tu médico si tomas medicamentos." |
| Q4 | "¿Tiene efectos secundarios?" | Adaptar: si hay periodo de adaptación, mencionarlo. Si no, "No tiene efectos secundarios conocidos." |
| Q5 | "¿Necesito receta médica?" | Siempre: "No. Es suplemento alimenticio de venta libre." |
| Q6 | "¿Hacen envíos a todo México?" | Fijo: "Sí, a toda la República Mexicana. 3-5 días hábiles. Envío gratis en pedidos +$1,500 MXN." |

---

## FASE 2 — Generación de blocks

### Síntomas (5 blocks, type: "symptom")

Generar 5 síntomas que el target audience experimenta. Reglas:

1. **Títulos**: 2-3 palabras, en mayúscula inicial. Ej: "Hinchazón Constante", "Fatiga Crónica"
2. **Descripciones**: 1-2 oraciones. Segunda persona ("Tu intestino..."). Empáticas, no alarmistas. Incluir una explicación técnica simplificada de por qué ocurre
3. **SVGs**: DEBE ser un SVG diferente para cada síntoma. Formato: `<svg viewBox="0 0 24 24">...</svg>`. Stroke-based (no fill), 24x24 viewBox

**Biblioteca de SVGs disponibles** (usar estos o crear variaciones):

```
HINCHAZÓN/DIGESTIÓN:
<svg viewBox="0 0 24 24"><path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke-dasharray="4 4"/><path d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z"/></svg>

GOTA/LÍQUIDO (antibióticos, hidratación):
<svg viewBox="0 0 24 24"><path d="M12 22C16.4183 22 20 18.4183 20 14C20 9.5 12 2 12 2C12 2 4 9.5 4 14C4 18.4183 7.58172 22 12 22Z"/><path d="M12 18V13"/></svg>

ONDAS/SEÑAL (irregularidad, frecuencia):
<svg viewBox="0 0 24 24"><path d="M2 12H6"/><path d="M10 8C11.5 8 13 9.5 13 12C13 14.5 11.5 16 10 16"/><path d="M16 5C19 6.5 21 9 21 12C21 15 19 17.5 16 19"/></svg>

LUNA/SUEÑO/DEFENSAS:
<svg viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/><path d="M3 21H16" stroke-linecap="round"/></svg>

RELOJ/CICLO/RECURRENCIA:
<svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>

ESCUDO/PROTECCIÓN:
<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>

RAYO/ENERGÍA:
<svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>

CORAZÓN/SALUD:
<svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>

FUEGO/INFLAMACIÓN:
<svg viewBox="0 0 24 24"><path d="M12 22c-4 0-8-2.5-8-8 0-4 3-7 5-9 1 2 3 3 4 3 0-3 1-6 3-8 2 3 4 6 4 10 0 5.5-4 8-8 12z"/></svg>

HUESO/ARTICULACIÓN:
<svg viewBox="0 0 24 24"><path d="M18 6L6 18"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/></svg>

CEREBRO/NEURO:
<svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 3 2 5.5 5 7v6h4v-6c3-1.5 5-4 5-7a7 7 0 0 0-7-7z"/><path d="M9 22h6"/></svg>

HÍGADO/DETOX:
<svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>

PIEL/REGENERACIÓN:
<svg viewBox="0 0 24 24"><path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9"/><path d="M12 3c4.97 0 9 4.03 9 9s-4.03 9-9 9"/><path d="M12 3v18"/></svg>

HORMONA/BALANCE:
<svg viewBox="0 0 24 24"><path d="M12 3v18"/><path d="M5 8l7-5 7 5"/><path d="M5 16l7 5 7-5"/></svg>
```

Elegir el SVG que mejor represente cada síntoma. NUNCA repetir el mismo SVG en un producto.

### Ingredientes (3-6 blocks, type: "ingredient")

Generar 1 block por ingrediente activo principal. Reglas:

1. **Solo ingredientes que estén en la FT**. NUNCA inventar
2. **`tag`**: Rol funcional metafórico (1-2 palabras). Ej: "Colonizador", "Titán Blindado", "El Paramédico", "Escuadrón Táctico"
3. **`name`**: Nombre simple del ingrediente o grupo. Si son múltiples del mismo tipo, agrupar (ej. "Lactobacillus 5-Cepa")
4. **`scientific_name`**: Nombre científico + dosis si está en la FT. Si no hay dosis en la FT, NO inventar — poner descriptor
5. **`description`**: 2-3 oraciones. Incluir:
   - Mecanismo de acción principal (de la FT)
   - Pathway molecular si está disponible (NF-kB, ZO-1, butirato, AGCC, etc.)
   - Beneficio tangible para el usuario
6. **`image_url`**: `""` (vacío — se llena después)
7. **Agrupar cepas/variantes similares** en un solo block cuando tenga sentido (ej. "Bifidobacterium Complex" en vez de 2 blocks separados)

### Testimonios (6-8 blocks, type: "testimonial")

Generar testimonios realistas y variados. Reglas:

1. **Perfiles obligatorios** (al menos 1 de cada):
   - Persona con condición crónica tratada con el producto
   - Persona post-tratamiento médico (antibióticos, cirugía, quimio — según aplique)
   - Profesional de salud que lo recomienda a pacientes
   - Familiar que lo compra para alguien más
   - Usuario escéptico que fue convencido por los resultados

2. **Contenido de cada testimonio**:
   - 2-3 oraciones máximo
   - DEBE mencionar al menos 1 ingrediente o beneficio específico del producto
   - DEBE incluir timeline ("a las dos semanas", "en un mes", "después de 3 frascos")
   - NUNCA claims médicos directos ("curó", "eliminó", "trató")
   - Sí permitido: "noté mejoría", "bajaron los episodios", "me siento mejor", "cambió completamente"

3. **Autores**:
   - Formato: `@NombreApellido` o `@NombreCity` o `@ProfesiónNombre`
   - Nombres mexicanos realistas
   - Variar género y edad implícita
   - Para profesionales: `@NutriNombre`, `@DrNombre`, `@FisioNombre`

4. **`image_url`**: `""` (vacío)

---

## FASE 3 — Ensamblaje JSON

Estructura exacta (usar como template):

```json
{
  "sections": {
    "main": {
      "type": "gr-pdp-landing",
      "settings": {
        "product_subtitle": "",
        "badge_rating": "",
        "badge_count": "",
        "badge_label": "",
        "show_social_proof": true,
        "symptoms_eyebrow": "Identificación",
        "symptoms_title": "",
        "symptoms_subtitle": "",
        "ingredients_eyebrow": "Formulación Premium",
        "ingredients_title": "",
        "ingredients_subtitle": "",
        "testimonials_eyebrow": "Resultados Reales",
        "testimonials_title": "",
        "testimonials_subtitle": "",
        "howitworks_eyebrow": "¿Cómo funciona?",
        "howitworks_title": "",
        "howitworks_subtitle": "",
        "step1_title": "",
        "step1_desc": "",
        "step2_title": "",
        "step2_desc": "",
        "step3_title": "",
        "step3_desc": "",
        "benefit_1": "",
        "benefit_2": "",
        "benefit_3": "Envío gratis en pedidos +$1,500",
        "benefit_4": "Garantía de satisfacción 30 días",
        "vs_eyebrow": "Comparativa",
        "vs_title": "",
        "vs_subtitle": "",
        "vs_them_label": "",
        "vs_them_title": "Lo que encuentras en farmacia",
        "vs_them_1": "",
        "vs_them_2": "",
        "vs_them_3": "",
        "vs_them_4": "",
        "vs_them_5": "",
        "vs_us_label": "",
        "vs_us_title": "Formulación premium",
        "vs_us_1": "",
        "vs_us_2": "",
        "vs_us_3": "",
        "vs_us_4": "",
        "vs_us_5": "",
        "faq_q1": "",
        "faq_a1": "",
        "faq_q2": "",
        "faq_a2": "",
        "faq_q3": "¿Puedo tomarlo junto con otros medicamentos?",
        "faq_a3": "Es un suplemento alimenticio seguro. Sin embargo, si estás tomando medicamentos o tienes alguna condición médica, consulta a tu médico antes de combinarlo.",
        "faq_q4": "¿Tiene efectos secundarios?",
        "faq_a4": "",
        "faq_q5": "¿Necesito receta médica?",
        "faq_a5": "No. Es un suplemento alimenticio de venta libre. No requiere prescripción médica.",
        "faq_q6": "¿Hacen envíos a todo México?",
        "faq_a6": "Sí, enviamos a toda la República Mexicana. Tiempo de entrega: 3-5 días hábiles. Envío gratis en pedidos mayores a $1,500 MXN."
      },
      "blocks": {
        "symptom_1": { "type": "symptom", "settings": { "icon_svg": "", "title": "", "description": "" } },
        "...": "...",
        "ingredient_1": { "type": "ingredient", "settings": { "image_url": "", "tag": "", "name": "", "scientific_name": "", "description": "" } },
        "...": "...",
        "testimonial_1": { "type": "testimonial", "settings": { "image_url": "", "quote": "", "author": "" } },
        "...": "..."
      },
      "block_order": ["symptom_1", "...", "ingredient_1", "...", "testimonial_1", "..."]
    }
  },
  "order": ["main"]
}
```

---

## FASE 4 — Validación (OBLIGATORIO antes de guardar)

Ejecutar este checklist mentalmente. Si falla cualquiera, corregir antes de guardar:

- [ ] **JSON válido**: Sin trailing commas, sin comillas faltantes, parseable
- [ ] **Español correcto**: Buscar "anos", "dano", "articulacion", "inflamacion", "tu" sin acento cuando es pronombre → CORREGIR
- [ ] **Todos los settings llenos**: Ningún valor vacío `""` en settings que deberían tener contenido
- [ ] **block_order completo**: Incluye TODOS los block IDs declarados en `blocks`
- [ ] **block_order orden correcto**: symptom_1..N → ingredient_1..N → testimonial_1..N
- [ ] **SVGs únicos**: Ningún SVG repetido entre síntomas
- [ ] **Claims verificados**: NINGÚN ingrediente, dosis, o mecanismo que no esté en la FT
- [ ] **NO usar respetado**: Ningún claim que esté en la columna "NO usar" del Product Log
- [ ] **Testimonios variados**: Al menos 5 perfiles diferentes, todos mencionan ingrediente/beneficio específico
- [ ] **FAQ adaptadas**: Q1 y Q2 tienen respuestas específicas para este producto (no genéricas)
- [ ] **Us vs Them pareados**: Cada `vs_us_X` es contraparte directa de `vs_them_X`
- [ ] **Precio/presentación correctos**: Verificar contra Shopify API y FT

---

## FASE 5 — Output

1. **Guardar archivo**: `{THEME_DIR}/templates/product.gr-{slug}.json`
   - Si el slug no es claro, usar el handle de Shopify obtenido en Fase 0
2. **Reportar**:
   ```
   TEMPLATE GENERADO: {Nombre Producto}
   Archivo: templates/product.gr-{slug}.json
   Handle Shopify: {handle}
   Precio: ${price} MXN (antes ${compare_price})
   Stock: {inventory_quantity} unidades

   Contenido:
   - {N} síntomas
   - {N} ingredientes (verificados contra FT)
   - {N} testimonios
   - 3 pasos How It Works
   - 6 FAQ personalizadas
   - 5 comparaciones Us vs Them
   - 4 benefit bullets

   Fuentes: FT ({nombre_ft}), Product Log (GR-P0XX), KB

   Siguiente paso: /gr-pdp-deploy {slug}
   ```
3. **Si el producto NO existe en Product Log Global**, avisar que se debe agregar

---

## ERRORES CONOCIDOS Y GOTCHAS

1. **FTs image-based**: La mayoría de FTs de GreenRay son PDFs con imágenes embedded, no texto. Usar pypdf para extraer imágenes y leerlas visualmente
2. **"L. sporogenes" es nombre obsoleto**: El nombre correcto es Bacillus coagulans. NUNCA usar L. sporogenes
3. **Dosis no en FT**: Si la FT no especifica mg de un ingrediente, NO inventar. Usar descriptor: "Cepa esporulada" en vez de "500mg"
4. **Categoría del producto**: Verificar en el Product Log o catálogo la línea correcta (Gastrointestinal, Hormonales, Desinflamación, etc.) para adaptar el tono y vocabulario
5. **Productos de la misma línea**: Si hay otros productos de la misma línea (ej. GAXALIV Base, Enzymas, Probióticos), asegurar que los testimonios y claims no se contradigan entre sí
