---
name: No volver al Pixel como hipótesis #1 cuando atribución gap es <10%
description: Cuando un cliente no ve compras y CALIBRATION muestra gap Meta vs Shopify <10%, no diagnosticar Pixel; ir a audiencia, oferta y landing
type: feedback
originSessionId: 70f8da16-d755-454b-8781-dbe7ebba1f45
---
Gibran me corrigió 2026-05-11 durante audit de LF: "Mira, el pixel no es el tema... siempre quieres hacer mil revisiones al pixel, pero nunca es el tema". Recibido.

**Regla:** antes de proponer "verificar/reconstruir Pixel" como hipótesis principal en un audit:

1. Buscar **atribución gap medido** en `SPK - MEDIA BUYING OPS/LOGS/{CLIENTE}/CALIBRATION.md` (sección "Atribución gap Meta vs Shopify"). Si el gap 30d es <10%, el tracking funciona — el problema está en otro lado.
2. Cruzar con **Shopify abandoned_checkouts** y **orders.json**. Si no hay abandoned checkouts post-relaunch, no hay intent — no es atribución, es que la gente no agrega al carrito.
3. Sólo proponer reconstrucción de Pixel si:
   - Hay gap >20% Meta↔Shopify, O
   - El Pixel stats en Meta API muestra eventos faltantes Y Shopify orders confirman compras que no llegan al Pixel.

**Why:** En agencias donde el theme y el Pixel ya fueron debuggeados (LF tuvo fix de GA4 vía Custom Pixel 14-abr, HC tiene atribución gap structural documentado), volver al Pixel como hipótesis #1 desperdicia tiempo y desvía del verdadero problema.

**How to apply:** En auditorías de "0 compras / mucho spend", ir directo a:
- (1) audience structure: ¿hay LAL, retargeting, exclusiones?
- (2) ad-landing match: ¿lo que promete el ad existe en la PDP?
- (3) audiencia broad sin filtros = quema de presupuesto sin learning
- (4) curva de delivery del ad (CTR/CPC mejorando = clicks OK; problema abajo)

Pixel se valida con un pull rápido de events del último día, NO se reconstruye salvo evidencia dura.
