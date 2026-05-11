---
name: Gemini API vs Web UI — HC carrusel quality
description: Gemini API pierde fidelidad composicional en carruseles HC complejos. Web UI preferida para producción final.
type: feedback
originSessionId: 0cf793cf-c149-49e5-9c02-41903f9902a3
---
Para HC carruseles de múltiples slides con instrucciones composicionales específicas (posición de logo, tamaño de numeral, layout texto/foto), el modelo `gemini-3.1-flash-image-preview` vía API genera imágenes pero pierde detalles críticos: logo en posición incorrecta, numeral drop-cap sin el tamaño correcto, layout zona texto/foto no respetado.

**Why:** El usuario evaluó HC-033 (serie "5 SEÑALES", 7 slides × 2 variantes) generado vía API y lo rechazó: "NO ME ENCANTARON. SE PERDIERON VARIAS COSAS." El Gemini Web UI produce resultados significativamente más fieles a los prompts.

**How to apply:** Para producción final de carruseles HC orgánicos con composición compleja, usar **Gemini Web UI** (workflow manual Gibran ejecuta prompts, QA, deposita finals). La API con `generate_images.py` es válida para drafts rápidos / referencia / iteración de concepto, pero no para el entregable final que va al Content Hub. Cuando se proponga generación de imágenes HC, indicar explícitamente qué método se usará y por qué.
