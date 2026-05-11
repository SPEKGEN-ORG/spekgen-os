# project: spekgen.com/chatbots — landing de servicio chatbots

**LIVE:** https://spekgen.com/chatbots (clean) → redirects a `/pages/chatbots-v{hash}` versionado

**Source:** `SPK - SPEKGEN AGENCY/WEBSITE/pages/chatbots.html`

**Publish:** `python3 _publish_pages.py chatbots` desde `WEBSITE/`. El script ahora crea AMBOS redirects: `/pages/chatbots` y `/chatbots` apuntan al hash actual.

## Audiencia + ICP

PyMEs $80K-500K MXN/mes que ya ven valor en chatbots (raised hand) pero quieren info por correo antes de agendar llamada. Foco La Paz BCS + Jalisco (alineado a operación SPEKGEN).

## CTAs

- Primario: WhatsApp `wa.me/523339829069?text=...Servicio%20de%20Chatbots...`
- Secundario: `mailto:hola@spekgen.com?subject=Servicio:%20Chatbots...`
- Sin precios visibles, agenda llamada como conversion.

## Componentes clave (referencia para futuras landings)

- **Smart layer:** progress bar fixed top, side-rail dots con TOC inteligente + active highlight via IntersectionObserver, scroll-reveals con stagger, eyebrow CTA adaptativo (cambia copy según max scroll depth via 4 breakpoints 25/50/75/95%), mobile sticky bar
- **Phone mockup 3D premium:** notch + cámara + side buttons + multi-shadow + parallax cursor + float animation (todas respetan `prefers-reduced-motion`)
- **Chat paced:** 6 items secuenciados con setTimeout (timings 900/2400/4000/6000/7600/8800ms), pantalla 780px tall para que TODO quepa sin scroll. Conversación demuestra capacidades reales del bot: reconoce cliente Andrea, jala compra del 12 marzo, manda product card (image gradient + tag + título + URL + precio + stock), quick reply chips
- **Casos de uso:** 6 industrias (bienes raíces, ecommerce, consultorios, servicios, restaurantes, gimnasios) con mini-chats animados por card via IntersectionObserver `chat-active` class

## Pendiente

- `automations.html` mismo sistema visual + smart layer (Form → Make → Sheets/GHL/Email mockup en lugar de phone)
- Email outreach que apunta a ambas landings
- Indexar `/automations` al menú home también

## Aprendizajes

Ver `feedback_shopify_horizon_class_collisions.md` — todas las clases prefijadas `cb-` para evitar collisions.
