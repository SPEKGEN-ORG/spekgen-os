---
name: Dashboard interno /pages/clientes (Shopify)
description: Bookmark interno de Gibran — spekgen.com/pages/clientes — 3 cards HC/GR/MG con links a sus portales, logo SPEKGEN, toggle light/dark
type: project
originSessionId: 2026-04-24
---
**URL bookmark:** `https://spekgen.com/pages/clientes` (2026-04-24, LIVE 200 OK, 7.5 KB).

**Propósito:** Gibran guarda este link en bookmarks y desde ahí salta al portal del cliente que quiera (HC Monse / GR Gibran / MG Gibran).

**Ubicación Shopify:** store `yca1z0-wf.myshopify.com` (Horizon), page id `133676925185`, handle `clientes`, template_suffix `clientes`. `noindex,nofollow` meta → no aparece en Google.

**Files:**
- Template: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/theme/page.clientes.liquid` (standalone HTML, usa `{% layout none %}` para bypassear chrome de Horizon)
- Setup script: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/04_setup_clientes_dashboard.py` (idempotente — re-ejecutar para iterar)
- Logos binarios (1080x1080 PNG transparencia) subidos al CDN del theme:
  - `assets/spekgen-logo-black.png` (para light mode)
  - `assets/spekgen-logo-white.png` (para dark mode)
  - Source files: `SPK - SPEKGEN AGENCY/SPK - 01. BRAND MEDIA/00. LOGO/SPEKGEN LOGO BLACK.png` y `BLANCO.png`

**Cards:**
- 🟣 HC · Healthy Chuchos → `/pages/hc-stage`
- 🟢 GR · GreenRay → `/pages/gr-stage`
- 🔵 MG · Metagreen → `/pages/mg-stage`

**Theme toggle:**
- Botón fixed top-right (luna/sol SVG). Click → flip `data-theme="dark"` ↔ `"light"` en `<html>`.
- Persiste en `localStorage['spk-theme']`. Script pre-paint en `<head>` lee el valor ANTES del primer paint para evitar flash blanco en recarga.
- Dark palette: bg `#0a0a0b`, accent `#c4a8ff` (morado SPEKGEN). Light palette: bg `#f7f7f8`, accent `#6b46ff`.
- Logo swap automático via CSS: `:root[data-theme="light"] .logo-dark { display: none }` y mirror.

**Binary asset upload pattern (Shopify REST):**
```python
data = local_path.read_bytes()
b64 = base64.b64encode(data).decode("ascii")
sc.put(f"/themes/{theme_id}/assets.json", {
    "asset": {"key": "assets/spekgen-logo-black.png", "attachment": b64}
})
```
Campo `attachment` (base64) en vez de `value` (string). Para text assets seguir usando `value`.

**Para agregar un 4to cliente (LF por ejemplo):**
1. Agregar `<a class="card" href="/pages/lf-stage">...</a>` dentro de `.spk-grid` en el liquid
2. Agregar `.dot.lf { background: #colorDeLF; }` en el CSS
3. Re-run `python3 04_setup_clientes_dashboard.py`
