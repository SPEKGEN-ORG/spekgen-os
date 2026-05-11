---
name: Prospect Templates Catalog
description: Catálogo de templates reutilizables de mockup para outreach. Cada template es base estable ex-prospecto real. Template 01 = Premium Travel (Mr. Bu Yachts).
type: project
originSessionId: 5b9a6102-c150-41eb-8458-ac2958ee3556
---
En `PROSPECTOS/mockup_factory/templates/` se mantiene un catálogo de templates numerados `0N_nombre/` con `template.html` + `README.md`.

**Regla:** al llegar prospecto nuevo, primero revisar `PROSPECTOS/README.md` → tabla "Catálogo de Templates" y elegir el que aplique. NO construir desde cero si hay uno adecuado.

**Template 01 — Premium Travel (estable v1.0, 2026-04-23):**
- Ex: Mr. Bu Yachts & Travel → spekgen.com/mrbuyachtstravemockup
- Ideal: yates, hoteles boutique, tours privados, glamping, charters con rating ≥4.5 y ≥6 fotos buenas
- Secciones: hero video+fallback, rating badge, manifiesto, experiencias, flota/catálogo, why-us, testimonials Google (4 cards), galería, stats, booking CTA, FAB social cluster (WA main + Maps/IG/FB)
- FAB técnico: CSS unscoped con !important + z-index 2147483000, position absolute para children con bottom animado (NO flex-direction column-reverse — causó bug en Shopify)

**Template 02 — Ecommerce Retail (estable v1.0, 2026-04-24):**
- Ex: Tridente Fishing Tackle → spekgen.com/tridentefishingmockup
- Ideal: retail físico con comunidad digital fuerte (≥10K FB/IG) sin ecommerce. Pitch: "ya tienes la comunidad, te falta la tienda online". Ticket bajo-medio, 20+ SKUs.
- Diferencia vs T01: vende productos (precios, add-to-cart, promos, envíos), no experiencia.
- Secciones: SPEKGEN ribbon + announcement bar + nav con mini-cart + hero editorial + marquee beneficios + 8 categorías + 4 productos destacados + promos (screenshots FB) + how-it-works + community stat + galería 12 + contact + Maps embed + final CTA + accordion FAB 6 canales + watermark.
- **Estandarizaciones aplicables a TODOS los mockups futuros** (no solo T02):
  1. **Accordion FAB 6 canales** bottom-right con class `.spk-fab-root` + JS que reubica a `document.body` on load + `setTimeout` re-assert 500ms/1500ms para escapar `transform` ancestor de Horizon.
  2. **Anti-reuse triple-layer SPEKGEN:** top ribbon (`MOCKUP CONCEPTUAL · Propuesta por SPEKGEN`) + badge persistente bottom-left (`DISEÑADO POR SPEKGEN`) + diagonal watermark `body::before` con `repeating-linear-gradient(-45deg)` 3.5% gold + `mix-blend-mode: overlay`.
  3. Ambos widgets fixed necesitan `position: fixed !important` Y relocate a `document.body` via JS — solo CSS !important NO basta en Horizon (confirmado con 2 iteraciones fallidas en Tridente v3→v5).

**Referencias de estilo (`_REFERENCES/` por template):**
Cada template puede acumular referencias externas en `0N_nombre/_REFERENCES/{slug}.md` con paleta, bloques, microinteracciones y notas de qué replicar. Al armar mockup nuevo, leer las refs del template aplicable primero.
- T01 Premium Travel: `yatezzitos.md` (yates MX, navy+turquesa+dorado, booking-widget-overlay-hero, process flow 3 pasos, FAB social, CTAs WhatsApp+SMS verify) — guardado 2026-04-30

**Cuando estabilizar un template nuevo:**
1. Copiar `generated/{slug}/index.html` → `templates/0N_nombre/template.html`
2. Escribir README con: cuándo usarlo, tabla de placeholders a swappear, changelog versionado
3. Actualizar tabla de catálogo en `PROSPECTOS/README.md`

**Proximos planeados:**
- 03 real_estate_luxury (brokers de La Paz)
- 04 restaurant_chef_table
- 05 wellness_retreat
- 06 service_professional (abogados/contadores sin catálogo)

Beneficio vs construir desde cero: en vez de ~2-3 hrs de iteración, reusar template reduce a ~30min (solo swap de copy + fotos).
