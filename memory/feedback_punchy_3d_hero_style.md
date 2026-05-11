---
name: Punchy 3D Hero style validated
description: Tercer estilo aprobado para @gibran.alonzo.ecom — usar para hero storytelling / sistema-tech
type: feedback
originSessionId: e0d5711d-8388-4215-bbca-ef121ce9cc20
---
Estilo "Punchy 3D Hero" aprobado como tercer estilo del library de @gibran.alonzo.ecom, junto a "Contrast Morado" y "Light Tech". Primer uso: GA-042 (Mi mejor empleada nunca duerme) — 2026-04-14.

**Why:** Gibran explícitamente dijo "me gustó mucho el estilo" tras publicar GA-042. El estilo funcionó para un carrusel de 10 slides sobre el sistema de Meta Ads monitor.

**How to apply:**
- **Cuándo usar:** cuando el tema sea sistema / automatización / tech / build-in-public con hero-storytelling. Contrast Morado para vibes/personal; Light Tech para data-heavy tables/metrics; Punchy 3D Hero cuando hay un "objeto hero" que contar (iPhone, pipeline, sistema).
- **Especificaciones visuales:**
  - BG: `#FAFAF8` off-white con dot pattern sutil (radial gradients 40px/60px, opacidad 0.012-0.015)
  - Typography: Anton (condensed) en tamaños 180-200px para headlines, bicolor `#A8A8B0` gray + `#0A0A0F` black
  - Hero object: 3D con shadow stack (3 layers de shadow: crisp + mid + diffuse ambient)
  - Chrome consistente: handle `@gibran.alonzo.ecom` top-left (20px black circle + text), page# top-right gray, "Save for later" + caption italic bottom
  - Accent color: peach/orange `#FF9A5A → #FF5A1F` (CTA/hero), purple `#A78BFA` (dark variant BUILDER)
- **Producción híbrida:** Gemini para slides hero/concept (cover, before-state, dual-iPhone, CTA cards), HTML+Playwright para slides data-críticos (email real, rules table, pipeline).
- **Template HTML base:** reusar estructura de `GA-042/html/slide_03.html` o `slide_05.html` — ya tiene el chrome, headline, bg pattern estandarizados.
