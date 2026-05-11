---
name: Tridente Fishing Outreach
description: P-082 Tridente Fishing Tackle (La Paz BCS). Segundo envío real SPEKGEN 2026-04-24. Email + WhatsApp multi-canal. Template 02 Ecommerce Retail nace de aquí.
type: project
originSessionId: 752aadd3-d2eb-41cf-a0d8-64e12b6a3f5a
---
# P-082 Tridente Fishing Tackle

**Negocio:** Tienda física de tackle de pesca en La Paz, BCS. Blvd. J. Mujica esq. Gama Secundaria Donceles 28, CP 23078.
**Comunidad:** 110K seguidores Facebook (mega activos), IG `@tridente_fishing_tackle`.
**Pain:** venta presencial o por Messenger. NO tienen ecommerce.
**Teléfono tienda:** 612 108 5700
**Email:** v.tridente@hotmail.com (probablemente Verónica)

## Mockup LIVE

- **URL vanity:** https://spekgen.com/tridentefishingmockup
- **Handle versionado (última v5):** `/pages/tridentefishingmockup-v469873` (cambia en cada republish)
- **Source:** `PROSPECTOS/mockup_factory/generated/tridentefishing/mockup_website/index.html`
- **Contenido:** catálogo (Wrath II 6000/5000, Prosteel, Combo Sierra) + 8 categorías + promos reales de FB (screenshots) + galería + community section 110K + contact + Maps embed.

## Outreach enviado (2026-04-24)

### Email 9:10 AM approx
- From: `Spekgen Agency <outreach@spekgen.com>` vía alias en spekgen.ai@gmail.com
- Subject: `Tridente Fishing — les armé la tienda en línea`
- HTML: `PROSPECTOS/outreach/emails/P-082_tridentefishing/email.html`

### WhatsApp 9:12–9:17 AM (5 mensajes)
Chain guardado en `PROSPECTOS/outreach/emails/P-082_tridentefishing/whatsapp_sent.md`:
1. "Hola ¿qué tal? Cual es el canal indicado para alguna propuesta?"
2. Contexto + link mockup
3. Gancho "viendo su negocio y comunidad me sorprendió que aún no cuenten con tienda en línea"
4. Credibilidad SPEKGEN + sitio
5. CTA suave

Estado: `✓✓` (leídos al 9:17 AM). Última actividad previa del chat: ayer 7:36 PM → alta probabilidad de lectura mismo día.

## Decisiones / Lecciones

1. **Hotfix FAB positioning:** v3/v4 tuvieron FAB cut-off bottom-left por `transform` ancestor de Horizon. Fix v5 = clase CSS `.spk-fab-root` con `!important` + JS que reubica el nodo a `document.body` on load + `setTimeout` re-assert. Aplicar a todos los templates futuros.
2. **Estandarización anti-reuse SPEKGEN triple-layer:** top ribbon + bottom-left badge + diagonal watermark. Aplicado a todos los mockups desde 2026-04-24.
3. **WhatsApp multi-mensaje > 1 solo bloque:** el chain de 5 mensajes cortos tuvo mejor lectura (`✓✓` completo) que un block largo. Replicar.

## Siguiente step

- **D3 (27 abr):** si no hay respuesta, bump corto por WhatsApp ("¿lo alcanzaron a ver?")
- **D7 (1 may):** breakup warm
- Gibran NO quiere que Claude arme followups D3/D7 hasta que él lo pida.

## Registro dashboard

`dashboard/leads_data.json` P-082:
- `status: Msg 1 Enviado`
- `msg1Date: 2026-04-24`
- `email: v.tridente@hotmail.com`
- `whatsappSent: true`
- `whatsappDate: 2026-04-24`
- `outreachReady: true`
- `mockupLiveUrl: https://spekgen.com/tridentefishingmockup`

## Referencias siblings

- `project_mrbu_outreach.md` (primer envío)
- `project_prospect_templates_catalog.md` (T02 Ecommerce Retail nace aquí)
- `project_prospects_system.md` (overview)
