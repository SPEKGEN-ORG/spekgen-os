---
name: Yerena outreach state
description: Veterinaria Yerena (P-4242, LP-149) — meeting 29-abr 1PM con Roberto, mockup v2 + bonus blaster propuesta vigente al 15 mayo
type: project
originSessionId: da1ea852-33c3-4508-b8cc-7503488f1d6d
---
**Negocio:** Veterinaria Farmacia y Accesorios Yerena · Av Reforma 3120, Francisco Villa, La Paz BCS · 612 139 5539
**Owner:** Roberto Antonio Romero Yerena (M.C. M.V.Z. ced 6611266)
**Equipo:** 3 MVZ con cédula (Roberto + Mayra Montoya + Alondra Álvarez)
**USPs:** farmacia propia, abierto 7 días incl. festivos, visitas a domicilio, 4.7★ (40 reviews)

**Meeting:** 2026-04-29 1PM PRESENCIAL con Roberto. Status pipeline: `Reunion Agendada` (P-4242 en `_data/contactos_por_revisar.json`).

**LIVE URLs:**
- Mockup: `spekgen.com/yerenamockup` → `/pages/yerenamockup-v30cf35`
- Propuesta: `spekgen.com/yerenapropuesta` → `/pages/yerenapropuesta-vac425d`

**Stack mockup actual (v2):** v1 estructura/copy/imágenes + motion stack v2 encima (Lenis + GSAP ScrollTrigger + clip-path door reveals + Ken Burns hero + scale-in stagger reviews + parallax sutil + magnetic CTAs 0.25 + char-stagger pulido). Backup v1 en `index.html.bak.before-v2-replace.20260429-100738`.

**Bonus en propuesta** (29-abr): bloque "Anunciamos su sitio a hasta 600 contactos por WhatsApp — sin costo" inserto debajo de la promo del 30%. CSS variant `.promo--bonus` (gradient navy royal + accent gold). Vigente solo si firman antes del 15 de mayo. Sin valor monetario explícito.

**Update 2026-05-02 — meeting #1 outcome + bot pivot:**
- Mockup web LE GUSTÓ pero NO es prioridad #1.
- Necesidad #1 que Roberto verbalizó: **bot WhatsApp para "preguntones"** (clientes repetitivos consultando lo mismo).
- Necesidad #2 (mencionada pero menor): subirse a plataformas de delivery (Rappi/Uber/Didi). Plan piloto en `DELIVERY SERVICES/07. PILOT_YERENA/pilot_plan.md` (cofinanciado $5K + $2.5K/mes). NO se presenta el lunes — se reserva para después del bot.
- **Meeting #2: lunes 2026-05-04** con propuesta bot + propuesta delivery. Gibran NO va a llevar bot custom desplegado — va a mostrar bot de HC y Wizzybot de LF como demo en vivo.

**Decisión arquitectural bot Yerena (2026-05-02):**
- Stack final: **Wizzybot** ($69 USD/mes) + **Shopify Starter** ($5 USD/mes "tienda fantasma" para que Wizzybot sirva un negocio de servicios). Total infra ~$1,290 MXN/mes.
- Custom build Make+GHL DESCARTADO (overkill, mucho mantenimiento, deadline Japón).
- Wizzybot validado: WhatsApp ✓, custom prompt suficiente ✓, dashboard incluido ✓, Shopify Starter funciona ✓. Lo que NO hace: agendado complejo (Yerena no lo pidió, bot solo Q&A + handoff a humano para agendar).
- GHL sub-account NO es necesario (Yerena no pidió CRM, solo bot). Visibilidad para Yerena = dashboard de Wizzybot + notification a Roberto en handoff.

**Pricing bot final acordado (consistente con narrativa "no fee forzoso" de Gibran):**
- Setup: $3,900 MXN one-time
- Licencia plataforma (passthrough sin markup): ~$1,290 MXN/mes (Wizzybot + Shopify, costo real)
- Mantenimiento SPEKGEN: **OPCIONAL** — Sin retainer ($0, on-demand cotizado por evento) / Cuidado ($1,500/mes, 2 updates + monitor + reporte) / Total ($3,500/mes, ilimitado + alertas + analytics)
- Plazo implementación: 3-5 días hábiles tras llenar INTAKE_FORM.

**Folder asset bot:** `PROSPECTOS/mockup_factory/generated/yerena/bot_demo/`
- `KNOWLEDGE_BASE.md` — datos públicos extraídos de Maps + BRIEF (post-firma se complementa con INTAKE)
- `SYSTEM_PROMPT.md` — prompt vet "Yere" v0 (cliente puede renombrar)
- `INTAKE_FORM.md` — 26 preguntas + 20 FAQs para post-firma. Tiene numeración desfasada por edit, pendiente reescribir.
- `PROPOSAL.md` + `PROPOSAL.html` + `PROPOSAL.pdf` — versión actual con modelo viejo ($4,500 setup, mantenimiento $1,800). PENDIENTE regenerar con modelo Wizzybot pasthrough+opcional.
- `_DEPRECATED/` — SETUP_GUIDE_GIBRAN + DEMO_SCRIPT (ya no aplican porque no construimos bot demo)

**Pendientes pre-lunes:**
- [ ] Validar si Wizzybot $69 USD es por sub-account o cuenta total (Gibran sabe via LF setup)
- [ ] Regenerar PROPOSAL.html + .pdf con modelo Wizzybot final (setup $3,900 + licencia $1,290 passthrough + mantenimiento OPCIONAL 3 planes)
- [ ] Regenerar INTAKE_FORM con numeración limpia + version HTML+PDF branded
- [ ] Decidir: framing "Construido sobre Wizzybot" (transparente, mi voto) vs "Yere by SPEKGEN" white-label

**Pattern replicable:** modelo Wizzybot + Shopify Starter para cualquier negocio local de servicios (vet, salón, mecánico, contador, etc.) — ahorro masivo vs custom. La "tienda fantasma" Shopify es el unlock para que Wizzybot atienda negocios no-ecommerce.

**Why del bot pivot:** bot custom Make+GHL hubiera tomado 5-10 días de Gibran setup + mantenimiento contínuo. Wizzybot es 3-5 días, autoescala con voice + image día 1, mantenimiento bajo. Mejor producto para Yerena, mejor margen recurrente para SPEKGEN.

**How to apply:**
- Si Roberto firma bot → arrancar setup Wizzybot + Shopify Starter el mismo día.
- Si Roberto firma web → mover P-4242 a `Cerrado Ganado` en dashboard (sync xlsx auto).
- El "bonus" blaster expira 15 mayo — coordinar con Gibran si va a renovar/extender o dejar morir.
- Pattern bonus blaster + "Wizzybot stack" replicable a futuras propuestas vet/restaurant/local-business.
- Folder cliente: `PROSPECTOS/mockup_factory/generated/yerena/`. Propuesta web source: `propuesta/PROPUESTA_YERENA.html`. Propuesta bot source: `bot_demo/PROPOSAL.html`.
