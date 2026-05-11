# project: GR HORMO FX Pack 40+ bundle (creado 2026-04-21)

Product bundle y landing page creados via Shopify Admin API para soportar Ad 2 del batch v4.1.

## Product

- **Title:** HORMO FX Pack 40+ · Hombre + Mujer
- **Handle:** `hormo-fx-pack-40-hombre-mujer`
- **Product ID:** 8199258144857
- **Variant ID:** 43244361875545
- **SKU:** GR-PACK-HORMO40
- **Price:** $799 MXN
- **Compare_at_price:** $875 MXN (= suma individual real: HORMO FX M40+ $410 + HORMO FX MEN 40+ $465)
- **Ahorro vs individual:** $76 (9%)
- **Inventory:** sin tracking (vende infinito) — decisión pendiente
- **Status:** active
- **URL:** https://greenray.com.mx/products/hormo-fx-pack-40-hombre-mujer

Contenido del bundle: HORMO FX M40+ (30 cap, mujer) + HORMO FX MEN 40+ (30 cap, hombre).

## Landing page

- **Title:** Pack 40+ · Balance Hormonal en Pareja
- **Handle:** `pack-40-hormonal`
- **Page ID:** 132747133017
- **Template suffix:** `pack-40` (custom creado para bypassear bug del default)
- **URL:** https://greenray.com.mx/pages/pack-40-hormonal
- **Published:** true

body_html custom incluye:
- Hero con título + subtítulo
- Precio tachado + precio actual + badge AHORRAS $76
- `<form action="/cart/add">` con variant_id hardcoded 43244361875545
- 2 cards de productos incluidos
- Disclaimer médico

**Falta:** imagen hero del bundle (actualmente sin visual grande del pack).

## Template custom creado

`templates/page.pack-40.liquid` en theme Sense (ID 131785490521):
```liquid
<div class="page-width" style="padding: 24px 0;">
  {{ page.content }}
</div>
```

Razón: default `templates/page.json` tiene `main-page` disabled → ninguna page default renderiza body_html. Ver `feedback_shopify_sense_page_default_bug.md`.

## Uso en ads

- Ad 2 del batch v4.1 CROSS 2026-04-21 apunta a esta landing page
- CTA Meta: https://greenray.com.mx/pages/pack-40-hormonal
- Copy en Canva: `$799 / $875 · AHORRAS $76` (Gibran edita canvas, no regenera)

## Pendientes

- [ ] Subir imagen hero al body_html de la page (crop del ad o generar nuevo con Gemini)
- [ ] Decidir si activar inventory tracking + stock inicial
- [ ] Considerar meter el bundle también dentro de `/pages/salud-hormonal` EcomPoser section (requiere UI manual de EcomPoser app)
- [ ] Monitorear performance: si Pack 40+ vende decente, replicar mecánica con otros pares (ej. Pack Belleza 40+ = Colágeno Beauty + HormoFX Mujer)
