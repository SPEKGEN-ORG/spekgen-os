---
name: Horizon theme .grid class collides with Tailwind .grid
description: Cuando se embebe HTML con Tailwind en una page de Shopify con tema Horizon, la clase .grid colisiona y rompe todos los grids
type: feedback
originSessionId: 4223a5d4-0334-4c10-9b95-244e4feb260f
---
**Symptom:** Cualquier `<div class="grid grid-cols-3">` embebido en una Shopify page con tema Horizon renderiza con 14 columnas (148px 148px 148px 0px 0px 0px...) en lugar de 3 iguales. Cards colapsan en columnas angostas.

**Root cause:** Horizon tiene esta regla global:
```css
@media (min-width: 750px) {
  .grid {
    display: grid;
    grid-template-columns: var(--margin-4xl) repeat(var(--centered-column-number), minmax(0,1fr)) var(--margin-4xl);
  }
}
```
= 14 columnas (2 márgenes + 12 contenido). Choca con Tailwind's `.grid { display: grid }`.

Especificidad idéntica (0,1,0) → la regla que carga al último gana → Horizon carga después → Horizon gana. `!important` en mi regla `#spekgen-prospect-wrap .grid-cols-3 { grid-template-columns: ... !important }` NO era suficiente porque `.grid` establecía `grid-template-columns` antes y ganaba al final del cascade (ambos tienen `!important` implícito o la cadena de cascada no resolvía limpio).

**Fix que funciona (bulletproof):** renombrar el token bare `grid` → `spk-grid` en el HTML antes de publicar. Las utility classes `grid-cols-N`, `md:grid-cols-N`, `lg:grid-cols-N` se quedan porque no colisionan.

```python
def rename_colliding_classes(html: str) -> str:
    def rewrite_class(m):
        quote, classes = m.group(1), m.group(2)
        tokens = [("spk-grid" if t == "grid" else t) for t in classes.split()]
        return f'class={quote}{" ".join(tokens)}{quote}'
    return re.sub(r'class=(["\'])([^"\']*)\1', rewrite_class, html)
```

Más CSS: `#spekgen-prospect-wrap .spk-grid { display: grid; }` (reemplaza `.grid`).

**Dónde está aplicado:** `SPK - SPEKGEN AGENCY/PROSPECTOS/_publish_prospect.py` función `rename_colliding_classes()`.

**Regla general:** al embeber HTML externo con Tailwind en cualquier tema de Shopify, asumir que CUALQUIER utility class de 1 palabra (`grid`, `container`, `section`, `flex`, `hidden`) puede colisionar con el tema. `grid` fue el único confirmado para Horizon. Si aparece otro bug de layout, checar `document.styleSheets` vivo y buscar selectores `.{token}` en el tema.

**Also applies to:** cualquier futuro deploy de prospect a spekgen.com, cualquier embedding en HC Content Hub (Horizon también), cualquier SPA embed en Shopify Horizon.
