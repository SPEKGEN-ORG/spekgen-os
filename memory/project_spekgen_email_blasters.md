---
name: SPEKGEN Email Blasters — Serie de servicios
description: Estado de producción de los correos HTML de outreach por servicio. Diseño "Rojo Diego", tabla-based, WhatsApp CTA.
type: project
originSessionId: 752aadd3-d2eb-41cf-a0d8-64e12b6a3f5a
---
## Estado (2026-04-16)

### Correos individuales completados

| Archivo | Servicio | ED. | Preheader | WA prefill |
|---|---|---|---|---|
| `CATALOGOS_AI_EMAIL/email.html` | Catálogos AI | 04 | "Un catálogo editorial en 1 semana..." | "vi tu correo del catálogo AI" |
| `CONTENIDO_PUBLICITARIO_EMAIL/email.html` | Contenido Publicitario | 05 | "30 ads al mes. Sin productora..." | "vi tu correo de contenido publicitario" |
| `WEB_EMAIL/email.html` | Diseño Web + CRO | 06 | "Una web que convierte. En 2 semanas..." | "vi tu correo del diseño web" |

### Brochure stack completo
- `BROCHURE_STACK_EMAIL/email.html` — Los 3 servicios en un scroll continuo (source con paths relativos)
- `BROCHURE_STACK_EMAIL/email.pdf` — 3.1 MB, 1 página, 2x retina (JPEG 85%) — **DEPRECATED como attachment**
- **`PROSPECTOS/outreach/emails/_TEMPLATE_GENERAL/email.html` (2026-04-24)** — versión inline con 11 imágenes CDN Shopify + placeholders `{{NOMBRE}}` `{{NEGOCIO}}` `{{CIUDAD}}` `{{IG_HANDLE}}`. Esta es la que se usa para outreach MB/MC. NO se adjunta PDF. Script idempotente `_build_inline_email.py` + cache `.cdn_cache.json`.

### Servicios pendientes (no iniciados)
- Manejo de Redes — ED. 07
- Chatbots — ED. 08
- Automatizaciones — ED. 09

## Ubicación base

```
SPK - SPEKGEN AGENCY/SPK - 12. SOCIAL MEDIA/SPEKGEN COLABS/EMAIL_BLASTERS/
```

## Sistema de diseño "Rojo Diego"

- **Paleta:** `#D94423` (rojo) · `#F1EADA` (crema) · `#0A0A0A` (negro) · `#E8E2D5` (fondo exterior)
- **Fuentes:** Playfair Display (italic + bold) · Bebas Neue (titulares/pills) · Inter (body) · Caveat (firma/detalle)
- **Container:** 800px, `box-shadow:0 24px 60px rgba(10,10,10,0.12)`
- **Imágenes:** Full-width 800px, sin padding lateral, `font-size:0;line-height:0;` en el `<td>`
- **Pills de énfasis:** `background:#0A0A0A;color:#F1EADA;padding:2px 12px;border-radius:4px;` + Bebas Neue 26px
- **Botón WhatsApp:** `#25D366` pill + SVG glyph inline + "ESCRÍBEME" Bebas 32px + `box-shadow:0 8px 0 rgba(0,0,0,0.18)`
- **Separadores entre servicios (brochure):** `bgcolor="#0A0A0A" padding:2px 0` (banda negra delgada)

## Estructura por correo individual (12 bloques)

```
Ribbon negro → Greeting (cream) → IMG hook → Bridge 1 (cream, kicker + cuerpo)
→ Lead-in "Así lo hacemos —" (cream) → IMG proceso → Bridge 2 (red) → Kicker "· EL RESULTADO ·" (cream)
→ IMG proof → Bridge 3 (cream, Playfair italic 22px) → IMG cta → CTA button (red)
→ Firma (cream) → Divider → Footer legal (cream) → Ribbon negro final
```

## Estructura brochure (por servicio × 3)

```
[Ribbon negro] [Hero greeting] [Banda roja "ESTO ES LO QUE HACEMOS"]
  [Header 01 cream] [IMG hook] [Lead-in] [IMG proceso] [Bridge red] [IMG proof] [Stats strip]
  [Banda negra 2px]
  [Header 02 cream] ... (igual)
  [Banda negra 2px]
  [Header 03 cream] ... (igual)
[Cierre negro "UNA SOLA AGENCIA. TODO EL STACK."]
[CTA WhatsApp red] [Firma] [Footer legal] [Ribbon negro]
```

## WhatsApp

- Número: `523339829069`
- URL base: `https://wa.me/523339829069?text=...`
- Prefill brochure: `Hola%20Gibran%2C%20vi%20tu%20correo%20del%20stack%20completo%20de%20SPEKGEN%20y%20me%20interesa%20saber%20m%C3%A1s.`

## Notas de copy

- Nunca mencionar precio de SPEKGEN. Solo el dolor de la competencia (lo que cobran otros).
- "México" en firma. Nunca "La Paz".
- Saludo: siempre "Buen día." (sin guión, sin género)
- ED. número va en ribbon superior e inferior
- Fuente de logo: `CATALOGOS_AI_EMAIL/spekgen_logo_white.png` y `spekgen_logo_black.png`
