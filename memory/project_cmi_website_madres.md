---
name: CMI Website (Centro de Medicina Integrativa)
description: Website wellness clinic LIVE en spekgen.com/cmi para clínica de la mamá de Gibran (Dra. María García Estrada en Tinguindín). Personal/no facturable
type: project
originSessionId: 9fb71508-89d4-4ac1-a272-944629246be1
---
# CMI · Centro de Medicina Integrativa

**Cliente personal:** la mamá de Gibran, **Dra. María García Estrada** (Tinguindín, Michoacán). Clínica de medicina integrativa + farmacia curada. NO entra al Delivery Hub (no facturable).

**Regalo Día de las Madres 2026-05-10.**

## URLs LIVE

- **https://spekgen.com/cmi** (canonical) → /pages/cmi-inicio-v48927e
- /pages/cmi-servicios · /pages/cmi-farmacia · /pages/cmi-sobre-mary · /pages/cmi-contacto

## Carpeta

`01. CLIENTS OFFICIAL/CMI - CENTRO DE MEDICINA INTEGRATIVA/`
- `_CLIENT_CONTEXT.md` — source of truth + última sesión
- `04. WEBSITE/` — código fuente local (5 HTML + styles.css + script.js + assets)
- `05. SHOPIFY/_publish_cmi.py` — publisher reutilizable para futuros republish
- `02. PRODUCTOS/` — fotos clasificadas por marca

## Stack final

- HTML/CSS/JS estático multi-page (5 páginas)
- **Tipografía:** Inter (body) + Lora (headings serif suave) — no editorial
- **Paleta:** verde wellness (`--green-deep #1F4E33`, `--green #2E7D4F`) + cream (`--cream #FBF8F1`) + acento terra (`--terra #C46B4F`)
- **Direction:** "Wellness Clinic Modern" (Parsley Health / One Medical / Hims aesthetic). NO editorial pretencioso, NO video full-bleed hero, NO SVG dibujados
- **Servicio destacado:** Terapia Scenar como #1 con badge "★ Único en la región"

## Cómo republicar

```bash
cd "01. CLIENTS OFFICIAL/CMI - CENTRO DE MEDICINA INTEGRATIVA/05. SHOPIFY"
/usr/bin/python3 _publish_cmi.py
```

Auto: sube assets cambiados al CDN, regenera handles versionados, actualiza redirects (incluyendo `/cmi` → nuevo hash), borra versiones viejas.

## How to apply (futuras sesiones)

- CMI NO va al Delivery Hub (personal, no facturable)
- Para cambios de diseño: tocar `04. WEBSITE/` local, preview con `preview_start cmi-static` (port 8791), republicar con `_publish_cmi.py`
- Mary aún debe pasar: cédula profesional real, testimonios reales, fotos profesionales adicionales (opcional)
- Próxima sesión opcional: Tier S polish (timeline "Tu primera visita", Quiz "qué servicio te toca", number counters, FAQ acordeón) — Gibran dijo "así está bien por ahora"

## WhatsApp / Social link preview (LIVE)

`og:image` LIVE en las 5 pages CMI — composición 1200×630 con foto Mary + logo + texto serif sobre overlay verde. Generada por `_make_og_image.py` (PIL), subida + asignada por `_set_og_images.py` via Shopify metafields:
- `seo.image_url` → theme Horizon renderea og:image
- `global.description_tag` → theme renderea meta description + og:description (sino auto-saca feo del body)

Cuando WhatsApp cachea preview viejo: forzar refresh en https://developers.facebook.com/tools/debug/?q=https://spekgen.com/cmi → "Scrape Again". O agregar `?v=N` al URL para bypass cache local.

## Lecciones técnicas (importantes para próximos publishes a Shopify)

1. **Shopify strippea `<link>` del body de Pages** por seguridad → siempre embed CSS INLINE como `<style>` block. Bug en `_publish_cmi.py` resuelto con `inline_local_css()`.
2. **Shopify no permite redirect→redirect** (cadena) → redirects "atajo" (ej. `/cmi`) deben apuntar DIRECTO al handle versionado, no al canonical. El publisher auto-actualiza este cada republish.
3. **`extract_body_with_head` de SPEKGEN no matchea `<link>` HTML5 sin closing tag** — bug latent en `_publish_prospect.py` que NO afectó porque siempre embebimos inline el CSS.
4. **Sub-agents Haiku fallan "Prompt is too long"** en sesiones con SPEKGEN system prompt grande — fallback a análisis directo en bursts de 5-8 imágenes con tool Read.
5. **Foto hero perfecta** = foto real auténtica del lugar, NO stock de doctora genérica. La de Mary en su consultorio (`assets/services/dra_mary_hero.jpg`) ganó por mucho.
