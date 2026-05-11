---
name: Gibran Ecom slides expect photo backgrounds by default
description: For @gibran.alonzo.ecom carousel posts, covers (and often other slides) should combine personal/work photos as background layers with text overlays — not pure CSS cards.
type: feedback
---

Los slides de @gibran.alonzo.ecom deben combinar fotos reales (personales, escritorio, trabajo, laptop, etc.) como background layer con los textos encima. No son cards CSS puros.

**Why:** El estilo que funciona en este perfil es "builder cinematic" — mostrar el trabajo real, el escritorio, los monitores, la vida detrás. Las cards CSS sin fotos se sienten esteriles y genericas. En GA-036 Gibran eligio como winner una cover con foto (alt_g notebook flatlay). El patron establecido es: usar fotos de su banco personal (GA-036/photos/ tiene: personal_paisaje, personal_selfie, personal_sunset, personal_ny, work_img_2025 multi-monitor, work_img_2040 notebook flatlay, work_img_2915 coding night, cta_desk_day, cta_desk_topdown, cover_working).

**How to apply:** Al producir carruseles para GA-*** (Gibran Ecom), siempre incluir photo backgrounds en al menos el cover (slide 1) y opcionalmente el CTA (slide final). El sistema en `_shared/render_slide.py` soporta block `photo` con: src, position, opacity, zoom, overlay (auto/vignette/purple/light/soft/custom), layout (full/top/bottom/right/left). Preguntar a Gibran si no hay fotos disponibles claras para el tema del post — no asumir.
