# Proposal Template + Pricing Model — Quick Cash La Paz

**Origen**: 2026-04-28 Mariscos Los Laureles Las Garzas
**Status**: probado en producción, falta validar conversión

## Pricing Model — "Quick Cash, Clientes Pequeños La Paz"

Para prospectos pequeños/medianos (negocios locales La Paz/Cabos sin web):

| Item | Precio | Costo real SPEKGEN |
|---|---|---|
| **Setup** | $5,990 MXN one-time (30% off de $8,557 "normal") | ~$400 MXN dominio |
| **Mantenimiento mensual** | $1,990 MXN/mes | ~$0 (Vercel + ImprovMX free) |
| **Plan anual prepagado** | $19,900 MXN (paga 10 lleva 12) | $0 incremental |
| **Sesión fotos** (add-on opcional) | Desde $3,500 MXN | depende |
| **Gestión redes** (add-on opcional) | $4,990 MXN/mes | depende |
| **Meta Ads** (add-on opcional) | $5,990 MXN/mes honorarios | sin presupuesto del ad |

### Stack de cierre — 3 niveles de oferta

Pitch escalonado para presionar cierre mismo día:

1. **Nivel 1 (cliente cómodo)**: Setup + mensual con 1 mes gratis si firman este mes
2. **Nivel 2 (cliente con cash)**: Setup + plan anual ($19,900 = paga 10 lleva 12)
3. **Nivel 3 (killer offer)**: Setup + anual + firmando este mes = **3 meses GRATIS** (1 bienvenida + 2 anual). Ahorro total $8,537

Cash inmediato si cierran nivel 3: $25,890 ($5,990 setup + $19,900 anual). Margen año 1 ~91%.

### Por qué $X,990 (psychology)

- $5,990 > $5,000 (no se siente "barato/sospechoso")
- $5,990 < $6,000 (psicológicamente bajo el milestone)
- $1,990 < $2,000 (mismo principio)
- Deja margen para descuentos en negociación si hace falta

## Template Propuesta HTML

**Path**: `PROSPECTOS/mockup_factory/generated/mariscosloslaure/propuesta/index.html`

**Estructura de 8 secciones** (matching design language del mockup):

1. **Mockup banner** slim (atribución SPEKGEN)
2. **Cover hero** — logo + título punchy + 3 stats (30% OFF · 5 días · 3 meses gratis) + meta de fecha de validez
3. **Lo que ya tienen** — recap del mockup con thumbnail + CTA "Ver el sitio completo"
4. **Inversión (2 packages cards)** — Setup card + Mantenimiento card (oscura, marcada "Recurrente"). Setup con strike-through + badge 30% OFF
5. **Annual plan callout** — sección destacada navy/gold con badge "Mejor valor" + stack callout coral
6. **Promo banner** — gradiente coral con stack máximo + savings badge
7. **Beneficios — Lo que cambia** — 6 cards en cream con SVG icons (NO emojis): aparecen Google, reservas directas, menú actualizable, reseñas que venden, profesionalismo, datos para crecer
8. **Timeline 4 pasos** — Día 1 firma, Día 1-2 dominio, Día 3-4 conexión, Día 5 lanzamiento (en navy con badges coral)
9. **CTA section** — "Aceptan hoy y arrancan con 3 meses gratis" + 2 botones gigantes (WA verde + Llamar outline) + 3 trust items (sin contrato, cancelan cuando quieran, si no les gusta no pagan)
10. **FAQ** — 5 preguntas con accordion (qué pasa si no nos gusta, cancelación, por qué tan rápido, fotos, pagos)
11. **Final CTA strip** — última urgencia + WA mega button
12. **Footer** simple

### Reglas de diseño

- Misma paleta que mockup (navy/cream/coral/gold)
- Cormorant Garamond + DM Sans
- Mismo iOS dark mode fix obligatorio
- WhatsApp SVG real (no moon-arc)
- Mobile responsive: 880px breakpoint principal

### Variables a parametrizar para reusar

Para convertir en template genérico (futuro):
- `{{BRAND_NAME}}`, `{{LOCATION}}`, `{{LOGO_PATH}}`
- `{{WA_NUMBER}}`, `{{WA_PRESET_MSG}}`, `{{PHONE}}`
- `{{MOCKUP_URL}}`, `{{HERO_IMAGE}}`
- `{{DOMAIN_SUGGESTION}}` (ej. mariscosloslaureles.com.mx)
- `{{VALID_UNTIL_DATE}}`
- `{{INDUSTRY}}` para personalizar copy de beneficios

## Costo real operativo (Vercel + Cloudflare + ImprovMX)

Stack recomendado para máximo margen:

- **Dominio .com.mx**: Cloudflare Registrar ~$10 USD/año = **$400 MXN/año**
- **Hosting**: Vercel free tier (sites estáticos, CDN global) = **$0**
- **Email**: ImprovMX gratis (forwarding a Gmail del cliente) = **$0**
  - Si cliente quiere enviar también desde su email corporativo: Zoho Mail Lite $1 USD/mes = $240/año
- **DNS**: Cloudflare (gratis con el registrar)

**Costo real año 1**: $400 — $1,600 MXN según opciones email
**Setup fee**: $5,990 → margen $4,390 — $5,590 sobre trabajo ya hecho

## Cuándo NO usar este modelo

- Clientes grandes que quieren ecommerce real (LF, GR, HC nivel) → propuesta diferente, custom
- Sitios con backend dinámico → necesitas hosting de pago (Vercel Pro, AWS, etc.)
- Clientes que piden multilingual / multi-region → más trabajo en mantenimiento
- Industrias premium-premium (lujo, B2B serio) → pricing más alto justifica más trabajo

## Trigger para leer este file

Cualquier task que mencione:
- "propuesta para [prospecto]"
- "pricing para website" / "cotización web"
- "cuánto cobrar a [negocio local]"
- Uso del directorio `PROSPECTOS/mockup_factory/generated/*/propuesta/`
