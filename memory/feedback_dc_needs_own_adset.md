---
name: Dynamic Creative necesita adset dedicado DC-enabled
description: Upload DC a adset standard falla con error 1885553. Split en N static ads o crear adset nuevo con dynamic_creative=true
type: feedback
originSessionId: b0c7bd4c-7ebf-4e46-a093-9ae722137d73
---
Si subes un creative con `asset_feed_spec` a un adset que NO fue creado con
`dynamic_creative: true`, Meta rechaza con:

> error_subcode 1885553 — "Cannot have more than one ad in given Dynamic
> Creative Ad Set. Dynamic Creative Ad Set allows at most one active ad"

(mensaje es engañoso — en realidad es "este adset no soporta DC").

**Why:** Los adsets standard no aceptan asset_feed_spec, y los DC-enabled
solo aceptan 1 ad total. Son dos sabores mutuamente excluyentes.

**How to apply:** Cuando user pide "mismo adset que batch anterior" y el
batch anterior fue static, tienes 2 opciones para ads con múltiples imágenes:

1. **Split en N static ads** (1 por imagen variante) — `HC-AD-022-a`, `-b`, etc.
   Meta optimiza delivery entre ellos igual que DC a escala. Pierdes el
   "rotado algorítmico dentro de 1 slot" pero ganas 1 slot por variante.
   Fue el fix que hicimos para BATCH_HC_2026-04-23-v1 (022/023/024).

2. **Crear adset nuevo dedicado** con `dynamic_creative=true` — 1 ad DC por
   adset. Más overhead pero preserva el comportamiento original.

Para batches futuros: preguntar al user si quiere DC real (→ adsets nuevos)
o split-static (→ reusar adset). Default recomendado: split-static (simple,
funciona, sin overhead de targeting duplicado).

**Creative huérfanos:** los DC creatives que se crearon antes del reject
quedan sin ad bound (no cobran). Documentar en el upload log si son muchos.
