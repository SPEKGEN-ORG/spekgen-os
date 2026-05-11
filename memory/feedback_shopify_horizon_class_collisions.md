# feedback: Shopify Horizon theme class collisions

**Contexto:** Construyendo landings custom dentro de spekgen.com (Shopify, theme Horizon) via `_publish_pages.py` o `_publish_prospect.py`, hay un patrón recurrente de clases que colisionan con el theme y rompen estilos.

## Síntomas

- Mensajes/elementos invisibles o con texto oculto pese a tener `opacity:1` y `color` correctos en mi CSS
- Elementos `position:fixed` que se estiran a `width:100%` cubriendo toda la pantalla con backdrop-filter (caso `nav.cb-dots` cubriendo el hero entero como blur gigante)
- Animaciones que no disparan
- Bubbles, dots, guides, sticky bars que renderean en posición/tamaño incorrecto

## Causas

1. **Theme define clases genéricas con `display:none`/`visibility:hidden`/`opacity:0`** para entry animations de modales, popups, sliders. Las más comunes: `.in`, `.out`, `.media`, `.bubble`, `.guide`, `.dots`, `.dot`, `.progress`, `.reveal`, `.typing`, `.sticky-bar`.

2. **Chrome hider en `_publish_prospect.py`** (líneas ~190-200) tiene reglas con specificity de ID que fuerzan `width:100%!important` y `align-self:stretch!important` sobre todos los `> nav, > div, > section:not(.page), > footer` directos del wrapper `#spekgen-prospect-wrap`. Specificity 1,0,1 — beats class-only `!important`.

## Reglas obligatorias para nuevas landings

1. **Prefijar todas las clases custom con prefix corto** (`cb-`, `pg-`, `sk-`, etc.). NO usar nombres genéricos: `bubble`, `guide`, `dots`, `dot`, `progress`, `progress-bar`, `sticky-bar`, `reveal`, `reveal-stagger`, `typing`, `media`. Ni siquiera modifiers: `in`, `out`, `active`, `show`. Renombrarlos a `cb-in`, `cb-out`, etc.

2. **Para elementos fixed-position** (progress bar, side dots, floating guides, sticky bars), usar **selectores con ID-bumped specificity** para sobreescribir el chrome hider:
   ```css
   nav#dots.cb-dots,
   body nav#dots.cb-dots {
     position:fixed!important;
     width:max-content!important;
     left:auto!important;
     align-self:auto!important;
     /* ... */
   }
   ```
   El `body` prefix bumpea a specificity 1,1,2 vs chrome hider 1,0,1 → gana.

3. **Probar en local NO basta** — hay que publicar a Shopify y verificar live, porque el chrome hider solo se inyecta al publicar (no al renderear local).

4. **Script de rename automático:** ver `/tmp/spk_rename_cb.py` (sesión 2026-05-06) que hace renames batch con regex sobre CSS selectors + class attributes + JS selectors. Reusar/adaptar para landings nuevas.

## Diagnóstico

Cuando algo rompe en live (pero funciona local):
1. Inspeccionar elemento en DevTools, ver `getComputedStyle()` y comparar con CSS source
2. Si propiedades faltan (e.g. `position`, `width`) → es chrome hider ID rule overriding mi class rule
3. Buscar el rule más específico que está ganando (`Computed → Show all` muestra cascada)
4. Si todo el contenido es invisible/colapsado → probable colisión de class genérica con theme

## Cuándo aplica

- TODA landing nueva en `WEBSITE/pages/*.html`
- Mockups de prospectos en `PROSPECTOS/_prospectos/*/mockup_website/`
- Reportes mensuales en `publish-monthly-report` skill

Ya quemamos ~30 min depurando esto en el chatbots landing 2026-05-06. Memorizado para no repetir.
