---
name: Prospect Yerena (vet) — published to spekgen.com/yerenamockup
description: Veterinaria Farmacia Yerena (LP-149, La Paz BCS) live 2026-04-29. First Bond Vet pattern application. Meeting with owner Roberto Romero 1 PM same day.
type: project
originSessionId: 57841043-f116-44ae-a90e-75d6ba3b1741
---
**Lead**: LP-149 · **Owner**: Roberto Romero Yerena · **Meeting**: 1 PM 2026-04-29
**Phone**: +52 612 139 5539 · **Address**: Av. Reforma 3120, La Paz BCS

## Live URLs

```
https://spekgen.com/yerenamockup
https://spekgen.com/yerenapropuesta
```

Logo og:image confirmado para preview en redes/WhatsApp.

## Business

Triple línea: (a) farmacia veterinaria, (b) consultas y servicios clínicos, (c) tienda accesorios y alimento. **3 MVZ con cédula** (Roberto, Mayra, Alondra). Visitas a domicilio. Abren 7 días incl. festivos. 4.7★ Google con 40 reseñas.

Brand vibe (per BRIEF): "vet de cabecera de barrio paceño" — NO premium spa frío. Royal blue `#1A4FBF` + cream + coral CTA. Display: Fraunces. Body: Inter.

## Patterns aplicados (primer Bond Vet implementation)

3 capas Bond Vet sobre el refactor previo (sin tocar el resto):

1. **Concern-led routing** — "¿Qué necesita tu mascota hoy?" con 4 cards-CTA → WhatsApp pre-rellenado (Una revisión / Vacunas / Está enferma o lastimada [variant urgent coral] / Solo medicamento o alimento)
2. **Sticky mobile dual-intent CTA bar** — fixed bottom mobile, slide-up cuando scroll past hero, WA verde + Llamar dark blue, respeta safe-area-inset-bottom
3. **"Abierto ahora" live status** — píldora verde con pulse en nav, JS computa horario L-V 8AM-9PM / S-D 8AM-8PM, cierra con "cierra X PM" o "abre 8 AM" en rojo si cerrado

## Stack técnico

- HTML + Tailwind CDN + custom CSS scoped a `#spekgen-prospect-wrap`
- Motion stack: Lenis + GSAP + ScrollTrigger + SplitText + Phosphor Icons (vía Apéndice B)
- Hero usa `data-split` para reveal de "Tu vet de cabecera. Abierto domingos."
- USP strip + marquee + TikTok videos section + servicios + tienda + equipo + galería + reseñas + visítanos + footer + FAB

## Bugs cazados durante este publish

1. **Horizon CSS Grid constraint**: page-width-narrow no usa max-width sino grid-template-columns con CSS vars. Override en chrome_hider del `_publish_prospect.py`. Documentado en `feedback_horizon_css_grid_width_bug.md`
2. **Auto page-title bar**: Shopify renderea page.title como h1 en text-block — había un bar negro feo arriba. Hide via `.text-block[class*="__heading"]` + nuke section-background residue
3. **Logo no se subía como og:image**: script buscaba literal `logo.*` pero file era `yerena-logo.jpg`. Patcheado a regex `*logo*`

Los 3 fixes están permanentes en el script — beneficio para todos los próximos prospectos.

## Files

- Index live: `mockup_factory/generated/yerena/index.html`
- BRIEF: `mockup_factory/generated/yerena/BRIEF.md`
- Assets: `mockup_factory/generated/yerena/assets/` (fachada, logo, productos, equipo, etc.)
- Videos: `mockup_factory/generated/yerena/VIDEOS/` (TikTok intros)
- Propuesta: `mockup_factory/generated/yerena/propuesta/PROPUESTA_YERENA.html`

## Pendientes

- [ ] Meeting 1 PM con owner — ya tiene los links live para mostrar
- [ ] Si owner confirma → mover a propuesta + cerrar deal
- [ ] v2 alternativa pendiente: PROMPTS_yerena_v2.md ready para correr en próxima sesión usando frontend-design skill + shadcn MCP. Construye `index_v2.html` sin tocar el live para evaluación benchmark
- [ ] Si v2 supera al actual → reemplazar y republish con `cp index_v2.html index.html` + delete locked_handles + re-run publish-prospect

## Notes para futuros vet/dental/medspa

Bond Vet patterns que funcionan (validados en yerena):
- Warm conversational copy ("Tu vet de cabecera. Abierto domingos." > "El veterinario de la familia paceña.")
- Concern-led routing (4 cards entry funnel)
- Sticky CTA mobile (en LATAM mobile traffic = 70%+, este es crítico)
- Live status indicator
- WhatsApp como CTA principal con mensajes pre-rellenados específicos por concern

Replicable a los 390 leads (estética 201 + dental 189) en la base de prospectos.
