# Patrón: Comparativa de identidades A/B (single-source + side-by-side merge)

**Caso piloto:** F24 / Ferre24 (2026-05-08 noche). Sergio pidió decidir entre 2 identidades visuales — necesitaba comparación limpia donde solo varíe la marca, no formato/contenido.

## Arquitectura

1. **Single-source via `build.py`** (Python templating):
   - Define `THEME_A` y `THEME_B` como dicts con tokens: `accent`, `accent_2`, `display_font`, `display_style` (italic vs normal), `sans_font`, `mono_font`, `logo_path`, `img_base`, etc.
   - `BODY` = HTML markup ÚNICO compartido entre ambas identidades.
   - `CSS_TEMPLATE` = CSS con `{tokens}` parametrizados.
   - Output: 2 HTMLs estructuralmente idénticos en subcarpetas distintas.
   - Cualquier edit a `BODY` se replica idéntico → garantiza paridad cross-identidad.

2. **`render_both.py`** (Playwright single browser, 2 PDFs).

3. **`merge_side_by_side.py`** con **PyMuPDF (`fitz`)** — preserva vectores 100%:
   - Página doble (ej. 34×11.5 in para 2 trifolds tabloide 17×11).
   - Header band 0.5 in con label coloreado por identidad (`#FFD500` A · `#C6FF00` B).
   - `page.show_pdf_page(rect, src, page_idx)` para embed vectorial.
   - Divider hairline entre paneles.

4. **Image slots con fallback graceful:**
   - CSS `background: linear-gradient(overlay), url("{img_base}IMG_X.png") center/cover, fallback`.
   - Si la PNG no existe, browser usa el fallback gradient. NO se rompe.
   - Permite producir el brochure type-driven primero y agregar imagery después sin tocar markup.

5. **Dashboard de prompts** (`prompts_dashboard.html`) con copy-button por slot, identidad-coded, filename targets exactos.

## Reutilización

Cualquier cliente que pida comparar 2+ identidades de marca (logo + paleta + tipo) reutilizando contenido idéntico:
- LF / GR / MG / HC durante rebrand
- Prospectos en mockup phase con 2-3 opciones visuales
- Pitch decks A/B

Carpeta canónica:
```
BROCHURE_COMPARATIVA_<DATE>/
├── build.py                    ← single source
├── render_both.py              ← Playwright N PDFs
├── merge_side_by_side.py       ← PyMuPDF merge
├── prompts_dashboard.html      ← (opcional) Gemini prompts
├── identidad_A_<color>/{brochure.html, assets/, *.pdf, preview-*.png}
├── identidad_B_<color>/{...}
├── IMAGENES/identidad_A_<color>/
├── IMAGENES/identidad_B_<color>/
└── <CLIENTE>_COMPARATIVA_AB.pdf  ← entregable final
```

## Lecciones técnicas

- **PyMuPDF `Rect.inflate()` NO existe** — usar `fitz.Rect(x0+pad, y0+pad, x1-pad, y1-pad)` manual.
- **`page.insert_textbox(rect, text, fontname="hebo", ...)`** — `hebo` = Helvetica-Bold built-in, `align=1` centrado.
- **`page.show_pdf_page(rect, src_doc, page_idx)`** preserva vectores. NO usar pixmap salvo que necesites raster.
- **Playwright single context, multiple goto** ahorra tiempo vs nuevo browser per render.
- **CSS `background: stack`** con multiple capas: orden = top→bottom. Overlay primero, photo segundo, fallback color al final.

## Anti-patrones

- ❌ Duplicar HTMLs A y B → drift inevitable cuando se edita uno.
- ❌ Usar Playwright para componer comparativa (raster, pierde calidad).
- ❌ Hardcodear paths a imágenes en BODY → no es theme-aware.
- ❌ No tener fallback graceful en image slots → brochure roto si no hay foto.
