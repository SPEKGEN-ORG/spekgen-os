# Feedback — Validar CPA por producto SIEMPRE antes de pausar

## Regla

Antes de pausar cualquier ad de Meta, calcular el CPA real por producto:

```
CPA_max = precio_unitario_producto - $150 (costo absorbido SPEKGEN)
Si spend / purchases > CPA_max  →  pausar
Si purchases == 0 y spend > CPA_max × 2  →  pausar
```

No confiar en ROAS de cuenta ni en "me parece que ya lleva mucho". Calcular numero.

## Origen del aprendizaje

Ejercicio cross-client 2026-04-17. El ad `LF-049_METAFIT_PROBLEM_SOLUTION` (ad_id `120243603540450731`) habia gastado $2,138 con 2 compras. ROAS aparente "ok" a nivel cuenta. **Yo propuse no pausarlo** con data superficial.

Gibran exigio validar CPA por producto:
- METAFIT precio ~$498, costo absorbido $150 → CPA_max $348
- Spend $2,138 / 2 compras = CPA real **$1,069** → 3x el maximo permitido
- Pausa obligatoria. Ahorro inmediato.

Sin la exigencia de Gibran, habriamos seguido quemando ~$300/dia en un ad con unit economics imposibles.

## Que hacer distinto

1. **Primera accion en cualquier analisis de ads**: abrir catalogo del cliente y anotar CPA_max por producto que se esta publicitando.
2. **Nunca decir "ROAS 0.xx" sin contextualizar contra CPA_max.** ROAS 1.0 con producto de $2,000 es winner; con producto de $300 es loser.
3. **Auto-pausa en monitores cloud**: las reglas deben incluir `CPA_real > CPA_max` no solo `ROAS < 1`. Revisar `hc-meta-monitor.yml` y `gr-meta-monitor.yml` en `g-bran/Spekgen-ops` y agregar esta regla.
4. **CPA_max por cliente** vive en: LF catalogo en `02. PRODUCTOS/`, HC en `HC_PRODUCTS_LOG_GLOBAL_v2.xlsx`, GR en `02. PRODUCTOS/PRODUCT_CATALOG.md`.

## Aplica a

- Todos los monitores automaticos (GH Actions de HC, GR, futuro LF)
- Todas las decisiones de pausa/escala manual
- El skill (pendiente) `/cross-client-intel` — debe imprimir CPA_real vs CPA_max en cada loser
