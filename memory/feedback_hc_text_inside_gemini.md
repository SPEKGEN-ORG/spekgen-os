---
name: HC — Todo texto va DENTRO de Gemini (no HTML/CSS overlays)
description: Para HC, todas las imágenes (ads y orgánicos) deben generarse con texto integrado por Gemini usando ABSOLUTE TEXT RULE. NUNCA overlays HTML/CSS/Pillow/Playwright.
type: feedback
---

Para Healthy Chuchos, todas las imágenes — ads Y carruseles orgánicos — deben generarse con el texto YA integrado por Gemini usando bloques ABSOLUTE TEXT RULE con strings exactos. Nunca generar imágenes "text-free" asumiendo que el texto se compone después con HTML/CSS + Playwright.

**Why:** Gibran rechazó tajantemente la V3 de HC-009B que usaba Playwright/base64 overlays. Regla explícita en `HC - HEALTHY CHUCHOS/_KNOWLEDGE_BASE.md`: *"NUNCA HTML/CSS/Pillow overlays: Todo texto va por Gemini. La V3 de HC-009B con Playwright/base64 fue rechazada tajantemente"*. Y también: *"Ads siempre AD-READY con texto integrado — no generar imágenes text-free"*.

La memoria global `feedback_image_production_workflow.md` dice lo contrario para SPEKGEN general (slides = HTML/CSS + Playwright), pero **HC tiene override explícito**. HC = texto adentro de Gemini, siempre.

**How to apply:**
- Cada prompt de imagen para HC (ads, orgánico, carruseles, single) debe incluir bloque ABSOLUTE TEXT RULE con:
  - Strings EXACTOS de cada línea de texto, entre comillas
  - Tipografía, peso, color, posición específicos
  - Line breaks explícitos
  - Negative: "no misspellings", "no extra text"
  - Verificación de ortografía española correcta (ñ, tildes) con palabras críticas listadas
- Composición visual debe reservar negative space explícito para el texto (ej: "upper 60% reserved for headline")
- Si Gemini devuelve typos en español (anos, dano, como, tambien, asi) → rechazar y re-generar
- Si el cliente dice "dame prompts para Gemini", entregar prompts con texto integrado por default — no preguntar
- Esta regla aplica aunque el deliverable final se llame "carrusel" o "post orgánico" o "ad"

**Excepción conocida única:** Videos/Reels donde el texto va por CapCut/edición post. Para imagen estática: siempre Gemini.
