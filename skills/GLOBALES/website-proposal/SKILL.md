---
name: website-proposal
description: Genera mockup HTML + propuesta de website Shopify para un prospecto y lo publica en spekgen.com/{slug}. Flujo completo: investigar negocio → crear mockup → crear propuesta → publicar → generar email de outreach.
---

# /website-proposal — SPEKGEN Website Outreach

## ¿Cuándo usar este skill?

Cuando Gibran quiera crear y mandar una propuesta de website Shopify a un prospecto nuevo. Este skill hace TODO el flujo de principio a fin.

## Input requerido

Gibran te da (mínimo):
- Nombre del negocio
- Industria / nicho (yates, hotel, boutique, inmobiliaria, etc.)
- Slug para URL (ej: "sunnydip" → spekgen.com/sunnydip)
- Ciudad / ubicación
- Website actual (si tienen uno, aunque sea malo)
- Cualquier info adicional: redes sociales, servicios, teléfono, email

## Flujo completo

### PASO 1 — Investigar el prospecto
1. Si tienen website, léelo con el Chrome MCP o WebFetch
2. Busca en Google Maps / redes sociales cualquier info adicional
3. Arma un brief interno del negocio:
   - Nombre, industria, ciudad
   - Servicios principales (3-5)
   - Tone/estética (lujo, familiar, aventura, profesional)
   - Color palette sugerida según industria
   - Pain points: ¿qué les falta digitalmente?

### PASO 2 — Clasificar (Market A / B / C)

| Tier | Criterio | Pricing one-time | Retainer |
|---|---|---|---|
| **Market A** | Alto ticket, lujo, extranjeros | $27,500 MXN / $1,400 USD | $7,500 MXN/mes |
| **Market B** | Mediano ticket, mercado local | $19,000 MXN / $1,000 USD | $4,500 MXN/mes |
| **Market C** | Bajo ticket, volumen | $12,000 MXN / $650 USD | $3,000 MXN/mes |

### PASO 3 — Crear el mockup HTML

Usa el template de la industria correspondiente (ver sección Templates). El mockup debe:
- Verse como una web real de Shopify profesional
- Usar el nombre/logo del negocio
- Incluir sus servicios reales
- Tener paleta de colores apropiada para su industria
- Secciones: Top Bar → Nav → Hero → Servicios → Sobre Nosotros → Galería/Stats → CTA → Footer

Guarda en:
```
SPK - SPEKGEN AGENCY/PROSPECTOS/{NOMBRE_NEGOCIO}/
├── mockup_website/
│   ├── index.html
│   └── assets/          ← imágenes si hay
└── propuesta/
    └── PROPUESTA_{SLUG}.html
```

### PASO 4 — Crear la propuesta HTML

La propuesta debe incluir:
1. **Header**: Logo SPEKGEN + nombre del prospecto + fecha
2. **El problema** (2-3 bullets de lo que les falta digitalmente)
3. **La solución** (qué incluye la web: secciones, funcionalidades)
4. **Lo que van a obtener** (benefits, no features)
5. **Pricing** (one-time + retainer como bundle)
6. **CTA**: "Ver tu mockup en vivo: spekgen.com/{slug}"
7. **Sobre SPEKGEN** (1 párrafo)
8. **Siguiente paso**: agendar llamada de 20 min

### PASO 5 — Publicar en spekgen.com

```bash
cd "SPK - SPEKGEN AGENCY/PROSPECTOS"
python3 _publish_prospect.py \
  --slug {slug} \
  --prospect-dir "{NOMBRE_NEGOCIO}" \
  --propuesta "propuesta/PROPUESTA_{SLUG}.html" \
  --brand "{Nombre del negocio}"
```

Esto genera:
- `spekgen.com/{slug}` → mockup navegable
- `spekgen.com/{slug}propuesta` → propuesta con pricing

### PASO 6 — Generar email de outreach

Genera el email personalizado listo para copiar y mandar desde spekgen.ai@gmail.com.

**Template por industria:**

Para yates/náutico:
```
Asunto: Tu presencia digital en La Paz — [NOMBRE NEGOCIO]

Hola [NOMBRE],

Vi [NOMBRE NEGOCIO] buscando [servicios náuticos / yates / etc.] en La Paz y me llamó la atención.

Hice algo específico para ustedes — un mockup de cómo se vería su nueva web:
👉 spekgen.com/{slug}

Y la propuesta completa (con inversión y detalle):
👉 spekgen.com/{slug}propuesta

¿Tienen 20 minutos esta semana para platicar?

— Gibran Alonzo
SPEKGEN Digital Agency
gibran.alonzo0506@gmail.com
```

### PASO 7 — Registrar en pipeline

Registrar en `PROSPECTOS/_PIPELINE.md`:
- Nombre, slug, industria, market tier, fecha de envío, status

---

## Templates HTML por Industria

### Paletas de colores recomendadas

| Industria | Primary | Accent | BG |
|---|---|---|---|
| Yates / Náutico | `#0A2342` (navy deep) | `#1E88E5` (ocean blue) | `#F0F7FF` |
| Hotel boutique | `#1A1A1A` (black luxury) | `#C9A84C` (gold) | `#FAFAF8` |
| Boutique / Moda | `#2D2D2D` (charcoal) | `#E8C4B8` (rose gold) | `#FFFDF9` |
| Inmobiliaria lujo | `#1C3A4A` (slate navy) | `#8FA89C` (sage) | `#F5F5F3` |
| Acuático / Aventura | `#003D52` (teal dark) | `#00B4D8` (cyan) | `#EAF7FB` |
| Restaurante lujo | `#1A0A00` (espresso) | `#C17D11` (amber gold) | `#FFFBF5` |

### Secciones estándar del mockup

```html
<!-- TOP BAR: teléfono + horario + badge de credencial -->
<!-- NAV: logo + links: Servicios, Nosotros, Galería, Contacto + CTA botón -->
<!-- HERO: fondo con imagen/gradiente + headline + subheadline + 2 CTAs -->
<!-- STATS: 3-4 números (años de experiencia, clientes, etc.) -->
<!-- SERVICIOS: grid de 3-6 cards con ícono, nombre, descripción -->
<!-- NOSOTROS: texto + imagen o split layout -->
<!-- GALERÍA o TESTIMONIOS: 3-6 items -->
<!-- CTA FINAL: banner con botón de contacto / WhatsApp -->
<!-- FOOTER: logo + links + redes + copyright -->
```

---

## Notas operativas

- El mockup NO necesita ser perfecto — necesita verse profesional y personalizado
- Si el prospecto no tiene imágenes, usa gradientes CSS o unsplash URLs (landscape/ocean/hotel)
- El slug debe ser corto y limpio: "palmira", "costamar", "sunnydip" — nunca espacios
- SIEMPRE generar el email de outreach al final del flujo
- Registrar en `_PIPELINE.md` cada prospecto procesado

## Archivo de seguimiento

`SPK - SPEKGEN AGENCY/PROSPECTOS/_PIPELINE.md` — fuente de verdad del pipeline de outreach
