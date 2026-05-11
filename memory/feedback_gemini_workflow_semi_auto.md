---
name: Gemini Workflow — Semi-Auto (Web UI)
description: Gibran usa gemini.google.com/app para generar imágenes, NO la API. Prompts deben ser 100% independientes. Entregable es HTML con copy buttons, no .md.
type: feedback
originSessionId: 8f23ff9f-5350-45bb-aa25-d23d7d3006a6
---
Gibran genera imágenes de HC (y otros clientes) en gemini.google.com/app, NO con la API de Gemini. La API tuvo problemas y se descartó temporalmente.

**Why:** Problemas con la cuenta de API de Gemini. El workflow semi-automático (web UI) es más confiable en este momento.

**How to apply:**

1. **Modelo de entrega para prompts:** Crear archivo HTML local (en `02. PROMPTS/`) con:
   - Un card por slide
   - Sección de attachments clara (qué imágenes adjuntar con ese prompt)
   - El prompt completo en un área scrollable
   - Botón "Copiar prompt" (navigator.clipboard.writeText)
   - NUNCA entregar prompts como archivo .md

2. **Prompts 100% independientes:** Cada prompt se pega en un tab separado de Gemini. NUNCA referenciar otras imágenes, otros slides, "el mismo perro de la slide anterior". Cada prompt debe describir COMPLETAMENTE todos los personajes, fondos, composición, lighting, texto — como si fuera el único prompt que Gemini va a ver.

3. **Attachments por slide:** Cada card del HTML debe indicar exactamente qué imágenes adjuntar. El usuario las adjunta manualmente antes de pegar el prompt. Mínimo para slides con perros: referencia de inspiración. Para slides con producto: mockup del producto (OBLIGATORIO para que Gemini genere el packaging correcto).

4. **Variaciones:** Siempre 3 variaciones por prompt. El usuario elige la mejor y la guarda en `03. WF ITERACIONES/`. Winners en `00. IMAGENES FINALES/`.
