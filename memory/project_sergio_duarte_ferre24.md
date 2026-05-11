---
name: Sergio Duarte — histórico deal pre-merge (Duarte + Ferre24 forks). MERGEADO 2026-05-07 a Ferre24 opción C
description: HISTÓRICO. P-9001 cerrado 2026-05-06 como Duarte fork 1. 2026-05-07 mutado a Ferre24 opción C ($32K + $10.5K/mes). P-9002 Ferre24 ya no existe como propuesta abierta — mergeado al P-9001. Ver project_ferre24_active.md para estado vigente.
type: project
originSessionId: 462abfd9-5a40-4f90-8c0a-7f2d0cbb7470
---
# Sergio Duarte — Histórico pre-merge (NO usar para estado actual)

> **2026-05-07: MERGE FORK 1 → FORK 2 OPCIÓN C.** Sergio decidió cambiar de Duarte ($17K/$7.5K) a Ferre24 opción C ($32K/$10.5K) el día siguiente del cierre. P-9002 ya NO existe como propuesta abierta — mergeado al P-9001. Estado vigente: `project_ferre24_active.md`. Razón del merge documentada en `project_first_win_duarte.md`. Lecciones replicables en `F24- FERRE24/_KNOWLEDGE_BASE.md`.

## Estado al 2026-05-06 (pre-merge — solo histórico)

> **2026-05-06: P-9001 Ferreterías Duarte → WIN** registrado en pipeline. Setup $17K + retainer $7.5K/mes + 100 SKUs/mes incluidos. Anticipo $8,500 depositado 5-may. Ver `project_first_win_duarte.md`. P-9002 Ferre24 sigue en evaluación.

# Sergio Duarte — Estado al 2026-05-04

## Contexto del prospect
- Sergio Duarte vive en Tangancícuaro, Michoacán. Dueño de **Ferreterías Duarte** (sitio actual `ferreteriasduarte.com`, Tinguindín)
- Tiene acceso privilegiado a 3 proveedores grandes en Guadalajara: **MC Ferretero, Truper, VDE** (potencial 4to: Marvelsa)
- Tel: `332 550 0287` · WhatsApp habilitado
- Es **referido directo de Gibran** (no de scraping Maps), por eso no tiene Place ID
- Sergio pidió en transcript de la llamada: bot multimodal WhatsApp (texto + audio + imagen) 70/30 con auto-pause, atención automatizada porque "es desgastante el contacto uno por uno"
- Distribución mensajes WhatsApp Sergio: ~30% texto / 30% audio / 30% imagen

## Dos proyectos paralelos
- **Fork 1 — Ferreterías Duarte:** rediseño del sitio actual + plataforma BIG ECOMMERCE 500-1000 SKUs
- **Fork 2 — Ferre24:** marca NUEVA express GDL aprovechando los 3 proveedores GDL

## Pricing final lockeado (REV.A · 2026-05-04)

### Ferreterías Duarte (fork 1)
- **Setup: $17,000 MXN** (50/50 firma + entrega)
- Incluye: Shopify completo + bot multimodal + carrito abandonado + ticket system + guías Skydropx + GA4/Pixel/CAPI + **100 SKUs cargados llave en mano** (research + ficha + 3 imágenes + upload con metafields) + catálogo PDF auto-generado + redirects 301
- **Retainer: $7,500 MXN/mes** desde mes 2 — bot 24/7 + alta hasta 30 SKUs nuevos/mes + hasta 4 rotaciones imagen/año + 8h cambios/mes + reporte mensual + soporte
- **Bloques adicionales:** $1,000 MXN / 50 SKUs · **Excedente alta:** $40 MXN/SKU sobre los 30 incluidos
- **Cláusula soft:** retainer mínimo 6 meses, después cancelable con 30 días aviso. Cambios masivos +100 SKUs cotizan aparte
- **Año 1 piso:** $17K + 11 × $7.5K = **$99,500 MXN**
- **Hosting Shopify:** Sergio paga directo a Shopify (~$580 MXN/mes Basic)
- **Implementación:** 3-5 semanas desde 1er pago

### Ferre24 (fork 2 — 3 opciones)
- **A — Catálogos PDF embebidos:** $17,000 MXN setup
- **B — E-commerce comprable (recomendado):** $22,000 MXN setup
- **C — B + biblioteca editorial propia:** $32,000 MXN setup
- Retainer $7,500/mes (igual que Duarte)
- Curaduría catálogo proveedor: cotización aparte · bloques 50 SKUs a $1,500 MXN (más caro que Duarte porque incluye scraping de PDFs proveedor + decisión cross-proveedor)
- Año 1 piso opción B: **$104,500 MXN**

### Add-on opcional ambos: Marketing $22K/mes (mes 2-3+)
30 ads pagados + 30 orgánicos + agente IA en comentarios/DMs. Mencionado en roadmap sin destacar.

## Vigencia
- Firma antes del **19 mayo 2026** (15 días desde 04 mayo)

## Estado entregables al 2026-05-04

### LIVE en spekgen.com (Shopify)
- Home Duarte: https://spekgen.com/duartemockup
- PDP Sierra Circular Makita 5007MG: https://spekgen.com/duartepdpmockup
- PDP Llave Impacto Makita TW008G XGT 40V: https://spekgen.com/duartetw008gmockup
- Mockup Ferre24 con 3 opciones A/B/C demostradas: https://spekgen.com/ferre24mockup
- **PENDIENTE despublicar:** `/duartev2mockup`, `/duartev3mockup`, `/duartev4mockup` (V2/V3/V4 descartados por Sergio)

### Locales
- `propuesta_duarte/PROPUESTA_FERRETERIAS_DUARTE.pdf` (665 KB, 6 págs)
- `propuesta_ferre24/PROPUESTA_FERRE24.pdf` (562 KB, 5 págs)
- `_DUARTE_HUB.html` y `_FERRE24_HUB.html` (single-file dashboards con iframe previews + PDF embed + research links)
- Script Playwright reusable: `_prospectos/_build_propuestas_pdf.py`

### Pipeline (Operations Hub)
- **P-9001** Ferreterías Duarte · status "Mockup Listo" · tier A · priceOffered 17000
- **P-9002** Ferre24 · status "Mockup Listo" · tier A · priceOffered 22000
- Ambos con `hubUrl` apuntando a los HTML locales (servidos vía nueva ruta `/prospects/<path>` del Operations Hub server)

## Decisiones de pricing notables

- **Ajuste de scope, no del retainer:** cuando Gibran sintió $20-22K setup alto, bajamos a $17K reduciendo SKUs incluidos (200 → 100) en lugar de tocar el retainer. Patrón potencial replicable para futuros prospects donde el setup pegue en techo psicológico
- **Ferre24 NO se ajustó:** las 3 opciones ya tienen piso bajo en A ($17K) y escalan por scope técnico real, no por número de SKUs
- **Catálogo PDF descargable incluido en setup gratis** como sweetener — es script auto-generado de Shopify, costo marginal cero
- **Skill `/duarte-product-pipeline` (research + 3 imágenes por SKU vía Gemini) NO está construida.** Se construirá si Sergio firma. Costo Gemini estimado: ~$30-50 USD para batch completo 1000 SKUs

## Próximos pasos

- [ ] Mandar PDFs a Sergio (Duarte primero, Ferre24 mid-week para no saturar)
- [ ] Confirmar con Gibran despublicación de URLs V2/V3/V4 en spekgen.com (acción destructiva en infra compartida)
- [ ] Decidir si meter fila manual a `SPEKGEN_PROSPECTOS.xlsx` para los 2 leads referidos (sin Place ID el sync xlsx falla silenciosamente cuando se mueve de stage)
- [ ] Si Sergio firma Duarte: construir skill `/duarte-product-pipeline`
- [ ] Si Sergio firma Ferre24: validar acceso a catálogos PDF MC/Truper/VDE

## Tech stack del mockup Ferre24 (referencia)
- Single HTML standalone, ~3,800 líneas
- TailwindCSS + Google Fonts via CDN (Anton + Inter + JetBrains Mono)
- Paleta orange #FF5C00 + yellow #FFD500 + black + cream
- 3 opciones A/B/C demostradas en vivo con option chips arriba de cada sección
- Cart state en `localStorage['ferre24_cart_v1']`, namespace global `Ferre24`

## Research compartido cross-fork
- `SERGIO DUARTE - FERRETERIA DUARTE/research/visual_references_analysis.md` (508 líneas, paletas Ferrepat/Herramienta Eléctrica/Wurth)
- `SERGIO DUARTE - FERRETERIA DUARTE/research/proveedores_gdl_analysis.md` (matriz cross-categoría MC/Truper/VDE/Marvelsa)
- Aplican a ambos forks; el Hub de Ferre24 los linkea con paths relativos cross-folder
