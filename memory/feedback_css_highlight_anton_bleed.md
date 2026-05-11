---
name: CSS highlight bleed con Anton font
description: Para highlights inline en headings Anton (display font), usar inline-block + line-height tight + br antes/después. Evita bleeding multi-línea
type: feedback
originSessionId: 820fab0c-ced6-42cb-8ee5-adb66539345e
---
Cuando hagas highlights tipo "marker" (background amarillo/negro detrás de una palabra clave) en headings con fonts display de gran x-height (Anton, Bebas Neue, Impact), **NO uses estos patrones:**

❌ `display:inline + box-decoration-break:clone + padding 0 .12em` — el background visual se extiende verticalmente respetando line-height del header, causando bleeding sobre líneas adyacentes
❌ `display:inline-block + line-height:.82` (más chico que el line-height del header) — crea baseline jump, el span empuja líneas vecinas hacia arriba/abajo
❌ Span en medio de una línea con texto adyacente cuando el texto wrappea — el highlight bleeds a la línea anterior/siguiente al hacer wrap

✅ **Patrón validado:**
```css
.hl-y, .hl-k {
  display: inline-block;
  padding: .02em .14em .06em;
  line-height: 1;
  margin: .04em 0;
  vertical-align: baseline;
}
```
Y SIEMPRE envolver el span en su propia línea forzada con `<br>` antes y después:
```html
<h2>Una<br/><span class="hl-y">ferretería</span><br/>que no espera<br/>al lunes.</h2>
```

**Why:** Anton tiene x-height enorme y line-height típico 1.02-1.06. Un span con background dentro del flujo inline ocupa toda la altura de la caja de línea (line-height + padding), y eso visualmente se traslapa con líneas vecinas si están a menos de ~1.1× line-height de distancia. Inline-block con line-height:1 propio + margin propio + estar en su propia línea (vía br forzado) lo aísla completamente.

**How to apply:**
- Cualquier brochure / poster / cover con headers display que use highlights tipo "marker"
- Cross-client: este patrón vale para cualquier cliente SPEKGEN. Documentado en `F24- FERRE24/F24 - 01. BRAND MEDIA/BROCHURE_2026-05-08_MULTIPAGE/brochure.html` como referencia. Costó 3 pasadas debug en sesión 2026-05-08 — no repetir.
- Si necesitas el highlight en medio de una línea (mismo line con otro texto), reduce font-size del header hasta que entre + acepta el riesgo de bleeding mínimo, o usa `box-shadow: inset 0 -.6em 0 var(--yellow)` que pinta solo una "barra" detrás sin tomar altura completa
