# Feedback — FAB widget en mockups Shopify-published siempre re-parentear al body

**Fecha:** 2026-05-04
**Detectado en:** IES Travel mockup deploy v1/v2 (3 iteraciones para arreglarlo)

## Problema

FAB social cluster (botón flotante WhatsApp + cluster expandible) con `position: fixed; right: 24px; bottom: 24px` se renderiza **mal posicionado** cuando el mockup se despliega a `spekgen.com/{slug}mockup` por `_publish_prospect.py`:

- A veces aparece en lado izquierdo deformado
- A veces se estira a 100% del viewport
- Z-index alto (2147483000) no lo arregla
- `!important` en position/right/bottom tampoco lo arregla

## Causa raíz

El script `_publish_prospect.py` envuelve TODO el body en `<div id="spekgen-prospect-wrap">`. Ese wrapper tiene CSS:

```css
#spekgen-prospect-wrap {
  display: flex !important;
  flex-direction: column !important;
}
#spekgen-prospect-wrap > section, #spekgen-prospect-wrap > div:not(.page) {
  width: 100% !important;
  align-self: stretch !important;
}
```

Con esas reglas:
1. El FAB queda como `> div` y recibe `width: 100% !important` → se estira a todo el viewport
2. `position: fixed` busca el "containing block" más cercano con transform/filter/perspective. El wrap no tiene esos pero `flex-direction: column !important` puede crear contexto que afecta al fixed en algunos browsers

## Solución

**Re-parentear el FAB al `<body>` directamente vía JS al `DOMContentLoaded`:**

```js
const fabWrap = document.getElementById('fabWrap');
if (fabWrap && fabWrap.parentElement !== document.body) {
  document.body.appendChild(fabWrap);
}
```

Una vez fuera del wrap, `position: fixed` se ancla al viewport (porque el body es el initial containing block) y todo funciona normal.

## Aplicabilidad

**Cualquier elemento con `position: fixed` en mockups que se despliegan a Shopify via `_publish_prospect.py`** — FAB, cookie banners, tooltips, modals globales, scroll-progress bars, custom cursors. Todos requieren reparenteo al body.

## Patrón canónico para futuros mockups

```js
// In DOMContentLoaded, after other init:
['fabWrap', 'cookieBanner', 'globalModal'].forEach(id => {
  const el = document.getElementById(id);
  if (el && el.parentElement !== document.body) {
    document.body.appendChild(el);
  }
});
```

Considerar agregar al template T01 Premium Travel (`mockup_factory/templates/01_premium_travel/template.html`) como helper standard.

## Referencias

- Memoria relacionada: `feedback_horizon_grid_collision.md` (otra colisión Horizon vs Tailwind, ya resuelta con `.spk-grid` rename)
- Script wrap CSS: `mockup_factory/_publish_prospect.py` líneas 240+ (CHROME_HIDER_CSS)
- Sí aplica a Mr. Bu Yachts también (referenciado en `01_premium_travel/README.md` v1.0 changelog "FAB social cluster con main = WhatsApp verde, acordeón hacia arriba")
