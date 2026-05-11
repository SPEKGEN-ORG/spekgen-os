---
name: HC Ticket Branded — Design & Generation
description: Cómo generar tickets de pedido/regalo brandeds de HC que coincidan con el diseño real
type: feedback
originSessionId: 2817c81e-c3c2-4e4a-b9ee-d599bf410956
---
Siempre replicar el diseño del ticket original de HC. No inventar uno desde cero.

**Diseño real del ticket HC:**
- Top gradient bar: teal `#2A9D8F` → naranja `#F7941D`
- Header: blanco, logo centrado
- Thank-you band: fondo `#EBF8F6` (teal muy claro)
- Colores navy del ticket: `#1A1E6B` (azul-indigo, NO el `#0C2D3F` teal-dark del visual system)
- Total card: background `#1A1E6B`, descuento en `#2ECBBA`, badge PAGADO en teal
- Footer: gradiente teal → naranja
- Badges de categoría: pill teal; Regalos: pill naranja `#F7941D`
- Qty circles: teal para compras, naranja para regalos

**Assets disponibles:**
- Logo: `HC - 01. BRAND MEDIA/00. LOGOS/logohc-12.png`
- QR Tienda: `HC - 01. BRAND MEDIA/02. QR CODES/HC_QR_TIENDA.png`
- QR Instagram: `HC - 01. BRAND MEDIA/02. QR CODES/HC_QR_INSTAGRAM.png`
- Mockups: `HC - 02. PRODUCTOS/{PROD}/04. MOCK UPS/*.jpeg`

**PDF con Playwright (no wkhtmltopdf — no está instalado):**
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html, wait_until="networkidle")
    height = page.evaluate("document.body.scrollHeight")
    page.pdf(path=out_pdf, width="600px", height=f"{height+2}px",
             print_background=True, margin={"top":"0","bottom":"0","left":"0","right":"0"})
```

**Template reutilizable:** `HC - HEALTHY CHUCHOS/HC - 10. LOGS/TICKET_REGALO_VERONICA_2026-04-24.html`

**Why:** Primera versión fue rechazada por no seguir el diseño branded real. Siempre revisar el PDF original antes.
**How to apply:** Cuando pidan generar un ticket de pedido, compra, regalo o cortesía para HC — partir del template existente en `HC - 10. LOGS/`.
