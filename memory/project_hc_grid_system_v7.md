---
name: HC Grid System v7 (vigente)
description: Sistema visual del feed IG de Healthy Chuchos aprobado 2026-04-26. Naranja + teal coexisten en cada post, 12 layouts catalogados.
type: project
originSessionId: be1e8cc7-81f5-4115-9c11-52f93c5d4ac9
---
**Fuente de verdad:** `HC - HEALTHY CHUCHOS/HC - 00. BRAND/00. VISUAL IDENTITY/HC_GRID_SYSTEM_v7.md` + `HC_GRID_MOCKUP_v7.html/.png/.pdf`.

**Why:** Gibran rechazó propuestas mono-color (v3 naranja/v4 navy/v5 teal) y la funcional v6 (color por categoría). Compartió referencia de "Furry Care" donde ambos colores marca conviven en cada post. Aprobado v7 el 2026-04-26.

**How to apply:**
- Cualquier post `HC-XXX` (Tier A organic) o `HC-H-XXX` (hero dual) que vaya al feed IG debe seguir v7. No inventar layouts fuera de los 12 IDs (L1-L12).
- 6 reglas duras: ambos colores presentes / logo HC chip cream TL / slot # JetBrains Mono TR / foto cutout circular o blob / headline Nunito 900 con underline accent del color contrario / shapes solo del catálogo permitido (paw, dots, squiggle, bubble, mega numeral, donut, block).
- Override vigente: el override `feedback_hc_text_inside_gemini.md` (texto dentro de Gemini) sigue para slides internos de carrusel pilar 1; **para tiles de feed v7 el texto va en HTML/CSS** (Playwright compositing).
- Layouts top usados: L1 cream-quote-blob-bn (slot E editorial domingo), L2 teal-blob-photo (ciencia con foto blob), L3/L11 mega-numeral (razones/listicle), L5 orange-speech-bubble (humor), L6 teal-donut-stat (dato %), L9 orange-mega-percent (dato −X%), L10 cream-block-top (ciencia centrada).
- Distribución recomendada por ventana de 12 posts: 4-5 base teal / 4-5 base naranja / 2-3 base cream. L1 editorial limitado a ~17%.
- Skill `/hc-organic-post` ya hookeado: A2 lee `HC_GRID_SYSTEM_v7.md`, brief A4 incluye campos `Grid Layout v7` (L#) + `Color base` + `Color acento`.
- HC_VISUAL_RULES.md y HC_SOCIAL_MEDIA_BRAND_GUIDE.md actualizados con preámbulo apuntando al v7. Versiones bumped a v1.2 / v1.1 respectivamente.
- Iteraciones previas (v1-v6 + comparativos) archivadas en `_DEPRECATED/` con `_README.md` explicando el por qué cronológico.
