# HC PDP V2 ArtriDog — Sprint + A/B Test

**Sprint cerrado:** 2026-04-30 (16+ horas). A/B test LIVE desde ~5pm Mazatlán.

## Estado actual

- **V1 ArtriDog:** `https://healthychuchos.com/products/artridog` — limpia, restaurada, `template_suffix: artridog`
- **V2 ArtriDog:** `https://healthychuchos.com/products/artridog-v2-r2` — 18 sections custom `hc-pdp-*`, `template_suffix: artridog-v2`, tag `pdp-test-v2`
- **A/B test:** Shogun Split URL 50/50, primary goal Purchase, duración 14-30d o hasta significancia
- **Tráfico:** $350 MXN/día Meta Ads (HC-VENTAS-MES1) + organic
- **Subscribe & Save:** plan 15% off cada 30d aplicado a V1+V2, wire-up en 3 forms (hero/sticky/cta-final) con sync JS
- **Lighthouse mobile:** 44 → 75 (+31 pts)
- **Pixel firing:** confirmado en V1 y V2

## IDs clave

| Campo | Valor |
|---|---|
| Theme Horizon HC | `152638718204` |
| Producto V1 | `9262298431740` (handle `artridog`) |
| Producto V2 | `9323553554684` (handle `artridog-v2-r2`) |
| Selling Plan Group | `gid://shopify/SellingPlanGroup/3711893756` |
| Selling Plan | `gid://shopify/SellingPlan/5637046524` (15%/30d) |
| Meta Ad Account | `act_1626923298353925` |
| Meta Pixel | `1813096612719811` |
| Campaign | `6899758932234` (HC-VENTAS-MES1) |

## V2 sections shippeadas (18)

hero carousel 4 slides + sticky ATC, problema, reframe (split editorial img-LEFT copy-RIGHT), efficacy timeline, ingredientes (9 accordions), how-it-works, scientific backing, vs them, before/after slider drag, UGC testimonial (split editorial copy-LEFT photo-RIGHT), perfiles banner, picky-eater guarantee, FAQ, CTA final, footer custom, related products slider.

## Meta Ads — winners conocidos

- **PS-S-V1** ROAS 7.54
- **OFERTA-V2** ROAS 3.99 lifetime, **cayendo a 2.06 last 14d** (vigilar — refresh creative si <1.5)
- 11 ads activos en HC-VENTAS-MES1 a $350/día

## Decisiones tomadas

- Subscribe & Save quedó vía API directo (no aparece en Shopify Subscriptions app oficial — filtra por `app_id`). Funcional en checkout, no administrable UI.
- A/B Split URL handles distintos > metafields. Sin Plus, es la forma más simple.
- V1 con title cambiado en V2 → invisible al cliente en cart (mismo producto a su ojo).
- Lighthouse 75 = good enough para shippear; el cuello LCP queda como deuda técnica.

## Deuda técnica / backlog

1. **Hero LCP rearchitect**: server-render slide 1 como `<img>` directo, lazy-init carousel post-LCP. Embla scroll-snap actual añade 3.1s Load Delay.
2. **Validar Subscribe & Save renew** end-to-end (primer ciclo de cobro 30d después).
3. **Tracking Shogun audit** a 7 días para validar conversion attribution.

## Próximos pasos

- [ ] **2026-05-02 (sábado):** audit Meta Ads + check primeros datos A/B
- [ ] **2026-05-07 (7d):** validar tracking conversion en Shogun
- [ ] Refresh OFERTA-V2 si ROAS 14d sigue <1.5
- [ ] Decidir winner V1 vs V2 cuando haya significancia statistical (>=14d, >=200 conv)

## Archivos / paths clave

- Batch Gemini: `SPK - 15. FACTORY/pdps/BATCH_HC_ARTRIDOG_PDP_V2_2026-04-29/`
- Playbook prompting: `SPK - 05. DEEP RESEARCH/AI IMAGE PROMPTING/_PLAYBOOK_GEMINI_2026-04-29.md`
- Sections theme: archivos `hc-pdp-*` en theme `152638718204`
- KB cliente: `HC - HEALTHY CHUCHOS/_KNOWLEDGE_BASE.md` sesión 48
