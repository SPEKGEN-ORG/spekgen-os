---
name: OmegaDog bottle and capsules — physical specs
description: OmegaDog real packaging is opaque white medium-tall bottle with mostly-white label (purple+orange wavy accents only), Australian Shepherd on label, opaque walls, dark ruby capsules ONLY visible if loose. Never invent generic vitamin bottle.
type: feedback
---

OmegaDog tiene 2 errores recurrentes que Gibran ha corregido. Los dos:

**1. Las cápsulas son ROJO RUBÍ OSCURO / BURGUNDY** — translúcidas con tono casi granate. NO son amber, doradas, ni amarillas.

**Why:** Las cápsulas de aceite de krill son naturalmente rojas oscuras por la astaxantina, a diferencia del aceite de pescado genérico que sí es amarillo/dorado.

**2. El BOTE es opaco y la etiqueta es mayormente BLANCA**, NO un bote de vitaminas estilizado con etiqueta toda morada.

**Why:** Gemini cuando lee "krill oil capsules" en un prompt tiende a generar un bote genérico de suplementos (alto, narrow, etiqueta colorida, cápsulas visibles a través del frasco). El producto REAL es completamente distinto: bote blanco OPACO de proporciones similares al GastroDog, etiqueta BLANCA con apenas ondas decorativas moradas (arriba) y naranjas (abajo), NO se ven cápsulas a través del plástico. Pasó en HC-011 S6 v3+v4 (2026-04-09) — descartadas.

**Specs reales del bote (replicar SIEMPRE — verificar contra `02. PRODUCTOS/03. MOCK UPS/Omega Dog.jpeg`):**
- Bote: medio-alto, blanco OPACO plástico, rounded shoulders, proporciones ~1.6:1 alto:ancho. NO tipo vitamina narrow.
- Tapa: blanca rosca, mismo diámetro que el cuello.
- Etiqueta: ~70% blanca con ondas moradas arriba + ondas naranjas abajo. NO label monocromática.
- Logo Healthy Chuchos arriba (perro/gato naranja+morado). "NUTRACÉUTICOS VETERINARIOS" pequeño.
- "OmegaDog" en texto OSCURO (brown/navy) con paw print entre Omega y Dog. NO en naranja, NO bright.
- "ACEITE DE KRILL" subtitle.
- **Pastor Australiano TRICOLOR** (negro+café/tan+blanco, fluffy, ears perked) en lado derecho del label. NO Belgian Malinois, NO Labrador.
- 2 iconos circulares (piel/pelaje + cardiovascular) en lado izquierdo.
- "suplemento nutricional" + "CONT. NETO 225 g" abajo.
- **OPACO**: las cápsulas NO se ven a través del frasco. NUNCA renderizar paredes translúcidas o sombras de cápsulas a través del label.

**How to apply:**
1. SIEMPRE adjuntar `02. PRODUCTOS/03. MOCK UPS/Omega Dog.jpeg` como referencia.
2. Usar lenguaje fuerte en prompt: "MATCH THE ATTACHED REFERENCE EXACTLY — opaque white plastic bottle with mostly-white label, NOT a tall vitamin bottle, NOT a fully purple label, NO visible capsules through walls".
3. Si quieres mostrar cápsulas, ponerlas LOOSE en la superficie al lado del bote — nunca dentro visibles.
4. Negativo explícito: "NO tall narrow vitamin bottle, NO fully purple label, NO translucent walls, NO 60 capsules text, NO Belgian Malinois (use Australian Shepherd tricolor)".
5. Cápsulas (cuando aparezcan): "dark ruby-red translucent softgel — deep burgundy/garnet, NEVER amber/golden/yellow".
6. PRODUCT_RULES en `HC-011/02. PROMPTS/generate_hc011_patitas.py` ya tiene la descripción correcta — copiar de ahí cuando arranques nuevos generadores HC.
7. `HC_VISUAL_RULES.md` (sección 1) tiene la spec actualizada — leerlo siempre antes de generar.
