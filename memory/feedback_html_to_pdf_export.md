---
name: HTML to PDF export — técnica correcta
description: Cómo exportar HTML largo (email/brochure) a PDF de una sola página continua, sin cortes, sin pixelado, con calidad retina.
type: feedback
---

## Problema

Playwright `page.pdf()` con `width` y `height` custom **NO genera una página continua**. Aunque el `height` sea el alto total del contenido, Playwright sigue paginando el PDF en múltiples páginas Letter/A4 con mucho espacio blanco. Resultado: 18 páginas, contenido cortado, aspecto roto.

## Solución correcta

### Paso 1 — Screenshot full-page a 2x

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    # device_scale_factor=2 = retina 2x (1800px de ancho real con viewport 900)
    page = browser.new_page(viewport={"width": 900, "height": 1200}, device_scale_factor=2)
    page.goto(file_url, wait_until="networkidle")
    page.wait_for_timeout(3500)  # esperar Google Fonts + imágenes
    page.screenshot(path=PNG_TMP, full_page=True)
    browser.close()
```

### Paso 2 — PNG → JPEG 85% → PDF

```python
from PIL import Image
import img2pdf

# PNG → JPEG para comprimir (PNG de 3x = 29 MB, JPEG 85% = 3 MB)
img = Image.open(PNG_TMP).convert("RGB")
img.save(jpg_tmp, "JPEG", quality=85, optimize=True, progressive=True)

# JPEG → PDF página única del tamaño exacto de la imagen
layout = img2pdf.get_layout_fun((img2pdf.in_to_pt(9), None))  # 9" de ancho, alto auto
with open(PDF_OUT, "wb") as f:
    f.write(img2pdf.convert(jpg_tmp, layout_fun=layout))
```

## Parámetros óptimos

| Parámetro | Valor | Razón |
|---|---|---|
| `device_scale_factor` | 2 | 3x es demasiado pesado (29MB). 2x = nítido y manejable |
| `viewport width` | 900 | Container de 800px + padding exterior 32px×2 = 864px mínimo |
| JPEG quality | 85 | Balance calidad/peso para fotos+texto |
| `wait_for_timeout` | 3500ms | Google Fonts necesita ~2-3s para cargar desde CDN |
| `img2pdf width` | 9 pulgadas | Representa 900px a 100 DPI — mantiene proporciones correctas |

## Resultados

- 900px viewport + 2x → PNG de ~1800×23000px
- PNG comprimido a JPEG 85% → ~3 MB
- PDF final: 1 página continua, sin cortes, calidad retina

## Instalación

```bash
pip3 install img2pdf pillow playwright
python3 -m playwright install chromium
```

## NO usar

- `page.pdf(width=..., height=...)` — pagina igual aunque el height sea custom
- `page.pdf()` con `@page { size: Letter }` en el HTML — mismo problema
- `device_scale_factor=3` — genera PNG de ~93M píxeles (30+ MB), muy lento
- PNG directo a img2pdf sin JPEG — demasiado pesado para compartir
