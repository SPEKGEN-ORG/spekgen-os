---
name: Design Intel system + motion stack for prospect mockups
description: 6 design DNA reports + libraries doc + yacht reference + motion stack integration. Built 2026-04-29 to upgrade mockups from "GHL-tier" to "Awwwards-tier".
type: project
originSessionId: 57841043-f116-44ae-a90e-75d6ba3b1741
---
**Created 2026-04-29.** Lives in `SPK - SPEKGEN AGENCY/PROSPECTOS/_design_intel/`.

## Folder structure

```
_design_intel/
├── README.md                          ← workflow + prompt-to-report mapping
├── PROMPTS_yerena_v2.md               ← validation + build prompts for new stack
├── prompts/                           ← 10 deep research prompts (Gemini-ready)
├── reports/                           ← 6 unique reports saved (DNA per vertical)
├── screenshots/                       ← yacht reference index from 22 sites
└── libraries/                         ← MOTION_LIBRARIES_AND_RESOURCES.md (45KB)
```

## Reports saved (6)

| Slot | Vertical | File |
|---|---|---|
| 01 | Yacht charter | reports/01_yacht_charter_DNA.md |
| 03 | Fine dining / mariscos | reports/03_fine_dining_DNA.md |
| 05 | Premium fishing charters | reports/05_premium_fishing_charters_DNA.md |
| 06 | Architecture / builders | reports/06_architecture_builders_DNA.md |
| 07 | Modern medspa / aesthetic / dental (incluye Bond Vet) | reports/07_medspa_aesthetic_clinics_DNA.md |
| 10 | Smoke shops / cannabis lifestyle | reports/10_smoke_shops_cannabis_lifestyle_DNA.md |

**Gaps**: hotels (02), villas (04), music (08), glamping (09) — Gibran no los corrió o se perdieron por paste errors. Aceptable para arrancar.

## Prompts pristinos (10)

Cada prompt vive en `prompts/{N}_{vertical}.md`. Estructura:
- Role + mission específicos al vertical
- 15-20 URLs reales nombradas agrupadas por tier (global / mid / LATAM-MX / nicho)
- 10 secciones de deliverables (landscape map, per-site teardown, motion inventory, IA, **section 5 custom UX patterns por industria**, copy DNA, psych triggers, conversion mechanics, premium-vs-template tells, **section 10 actionable pattern library custom**)
- Output requirements: 8,000+ palabras, todo claim con URL, verbatim quotes, marca [SPECULATIVE]
- Anti-fluff clause: nada "best practices", sin closing summary

Re-runnable cuando se necesite refresh de un vertical.

**WARNING**: cuando Gibran corre y pega outputs, hay que pegar a `reports/` NO a `prompts/`. Varios reports se perdieron en este lanzamiento por paste errors al overwrite de los prompts.

## Motion stack (Apéndice B integrado)

CDN block + init script ahora viven en:
- `mockup_factory/templates/01_premium_travel/template.html`
- `mockup_factory/templates/02_ecommerce_retail/template.html`
- 16 mockups generados (patcheados via `_apply_motion_upgrade.py` idempotente)

Stack: Lenis + GSAP + ScrollTrigger + SplitText + Phosphor Icons. Patterns activables vía data attrs:
- `data-split` en headlines → SplitText reveal por chars
- `data-reveal` en sections → fade-up scroll-triggered
- `data-magnetic` en buttons → magnetic cursor effect

## Workflow

1. Cuando se necesite report nuevo: abrir `prompts/{N}_{vertical}.md` y pegar a Gemini Deep Research
2. Pegar output de Gemini a `reports/{N}_{vertical}_DNA.md` (NO en prompts)
3. Si se necesitan screenshots de URLs referenced: lanzar background agent que recorra y guarde `screenshots/{N}_{vertical}/REFERENCE_INDEX.md`
4. Cuando se construya un mockup de esa vertical, leer el report como source-of-truth + aplicar motion stack vía data attrs

## Patches al `_publish_prospect.py` (críticos)

1. **Logo wildcard detection**: detecta `*logo*` no solo `logo.*` (catches `yerena-logo.jpg`, `brand_logo.svg`, etc.)
2. **Horizon CSS Grid override**: anula `--narrow-page-width`, `--page-margin`, `--full-page-grid-central-column-width` + force `.section { display: block; grid-template-columns: 100%; }`
3. **Auto page-title kill**: hide `.text-block[class*="__heading"]` + nuke `.section-background` padding/min-height para eliminar bar negro arriba

Beneficio: TODOS los prospectos publicados de aquí en adelante reciben estos fixes automáticamente.

## How to apply

- Construir mockup de vertical X → leer `reports/{N}_{vertical}_DNA.md` primero
- Aplicar motion stack via data attrs (no genéricos `.animate-fade`)
- Si el prospecto es vet/dental/medspa → patron Bond Vet del report 07 es el case study explícito
- Para libraries (Aceternity, Magic UI, etc) → consultar `libraries/MOTION_LIBRARIES_AND_RESOURCES.md` Top-10 shortlist
- shadcn-ui-mcp-server YA INSTALADO → puedo jalar bloques shadcn on-demand al construir templates

## Related memory files

- `feedback_horizon_css_grid_width_bug.md` — fix técnico Horizon
- `feedback_claude_mcp_type_field_required.md` — gotcha install MCP
- `project_yerena_published.md` — primer caso aplicado
