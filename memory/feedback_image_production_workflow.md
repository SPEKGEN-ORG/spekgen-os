---
name: Image Production Workflow
description: Social media slides are HTML/CSS rendered with Playwright to PNG. NEVER use Canva for slide production.
type: feedback
---

Las imagenes de carruseles e IG posts se producen con HTML/CSS + Playwright render. NUNCA usar Canva para producir slides.

**Why:** Gibran tiene un sistema establecido de visual templates (ej. "Contrast Morado" en `SPK - SPEKGEN AGENCY/SPK - 03. VISUAL TEMPLATES/`). Cada slide es un archivo HTML individual a 1080x1350px, renderizado a PNG con Playwright. Canva no es parte del workflow.

**How to apply:**
- Leer el template de `03. VISUAL TEMPLATES/` antes de producir
- Crear archivos HTML individuales por slide en `GA-XXX/html/`
- Renderizar con Playwright a `GA-XXX/renders/`
- Copiar a `GA-XXX/00. WINNERS/` como 1.png, 2.png, etc.
- Gemini se usa solo para generar imagenes sueltas (fotos, backgrounds), no para slides completas
- Canva NUNCA se usa para produccion de slides
