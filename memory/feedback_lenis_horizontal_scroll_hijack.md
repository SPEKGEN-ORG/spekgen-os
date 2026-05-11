# Feedback: Lenis hijackea touch/wheel de containers horizontales internos

**Detectado:** 2026-05-08, mockup Green & Rosse en `spekgen.com/greenrossemockup`.

## Síntoma

Cliente reporta:
- Slider horizontal (carrusel reseñas, scroll-x con `overflow-x: auto`) NO permite arrastrar/swipear
- Botones dentro del slider con `target="_blank"` no responden al tap en mobile

## Causa raíz

[Lenis](https://lenis.studiofreight.com/) (smooth-scroll library, muy usada en sitios premium con GSAP) **secuestra los eventos wheel y touch del documento entero**. Cuando hay un container interno con `overflow-x:auto`, Lenis intercepta los eventos antes de que lleguen al container. El usuario "no puede slidear" y, peor, en mobile el `touchend` también puede comerse y bloquea clicks de elementos hijos.

## Fix canónico

```html
<div id="reviews-track"
     data-lenis-prevent
     data-lenis-prevent-wheel
     data-lenis-prevent-touch
     class="overflow-x-auto ...">
  ...
</div>
```

Los 3 atributos son la API oficial de Lenis para opt-out por elemento. Una vez puestos, Lenis ignora wheel y touch sobre ese subtree.

## Layer adicional: drag-to-scroll manual

Aunque Lenis ya no hijackea, en desktop el container scrollea solo con shift+wheel o trackpad horizontal — UX pobre. Agregar pointer events manuales:

```js
let isDown = false, startX = 0, startScroll = 0, moved = 0;
track.addEventListener('pointerdown', (e) => {
  if (e.target.closest('a,button')) return;
  isDown = true; moved = 0;
  startX = e.clientX;
  startScroll = track.scrollLeft;
  track.setPointerCapture(e.pointerId);
});
track.addEventListener('pointermove', (e) => {
  if (!isDown) return;
  const dx = e.clientX - startX;
  moved = Math.abs(dx);
  if (moved > 6) track.classList.add('is-dragging');
  track.scrollLeft = startScroll - dx;
});
track.addEventListener('pointerup', endDrag);
track.addEventListener('pointercancel', endDrag);

// CSS: cuando is-dragging, desactivar pointer-events de hijos para no abrir links al soltar
.track.is-dragging a, .track.is-dragging .card { pointer-events: none; }
```

Y wheel vertical → horizontal:

```js
track.addEventListener('wheel', (e) => {
  if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
    e.preventDefault();
    track.scrollLeft += e.deltaY;
  }
}, { passive: false });
```

## Por qué falla el botón VER en mobile

Los `<a class="link">` dentro del card eran perfectamente válidos, pero en mobile Lenis interpretaba el touch como gesture de scroll vertical y se comía el touchend. Reforzar con:

```css
.review-link {
  position: relative;
  z-index: 5;
  pointer-events: auto;
  cursor: pointer;
  -webkit-tap-highlight-color: rgba(167,94,80,0.15);
}
```

## Aplica a

- Cualquier prospect mockup que use Lenis + GSAP (la mayoría desde 2026-04)
- Sliders de reseñas, sliders before/after, carruseles de productos, galerías de fotos
- Tabs horizontales con scroll en mobile

## Lección de proceso

Cuando construya un nuevo mockup con Lenis y necesite un container con scroll interno (cualquier eje), agregar `data-lenis-prevent` desde el inicio. Es 30 segundos de prevención que evita 1 hora de debug post-launch + un mensaje "no funciona el slider" del cliente.
