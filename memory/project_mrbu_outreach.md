# Mr. Bu Yachts & Travel (P-003) — Primer Cold Email Real SPEKGEN

**Contexto:** Primer envío real de la operación de outreach SPEKGEN. Marca la validación del flujo completo mockup → email → tracking → secuencia.

## Datos del lead

- **ID:** P-003
- **Nombre:** Mr. Bu Yachts & Travel
- **Industria:** yates / travel premium
- **Email destino:** `mr.butravel@gmail.com`
- **WhatsApp:** `+52 33 5121 2595`
- **IG:** `@mr.bu_travel`

## Mockup LIVE

- URL versionada canónica: `https://spekgen.com/pages/mrbuyachtstravemockup-v96bbc2`
- Vanity: `https://spekgen.com/mrbuyachtstravemockup`
- Template base: **Template 01 — Premium Travel** (`PROSPECTOS/mockup_factory/templates/01_premium_travel/`)
- Fotos: 4 reseñas reales de Google extraídas de screenshots (scraping falló 2x), FAB WhatsApp verde con pulse + acordeón hacia arriba, iOS autoplay fix aplicado.

## Envío

- **D0 (2026-04-23)** ENVIADO. Flujo:
  1. Abrir `email.html` en Chrome
  2. Cmd+A → Cmd+C
  3. Gmail compose (login `spekgen.ai@gmail.com`)
  4. From dropdown → `Spekgen Agency <outreach@spekgen.com>` (alias verificado via Gmail "Send mail as" + app password en `SPK - SPEKGEN AGENCY/.env` como `SPEKGEN_GMAIL_APP_PASSWORD`)
  5. Subject: `Mr. Bu Travel, les armé algo`
  6. Paste HTML → Send
- Template HTML final vive en `PROSPECTOS/outreach/emails/P-003_mrbu/email.html` (bulletproof navy/cream/gold).

## Secuencia Follow-up

| Día | Fecha | Archivo | Subject | Nota |
|---|---|---|---|---|
| D0 | 2026-04-23 ✅ | `email.html` | `Mr. Bu Travel, les armé algo` | ENVIADO |
| D3 | 2026-04-26 | `followup_d3.html` | `¿lo alcanzaron a ver?` | Bump corto |
| D7 | 2026-04-29 ⚠️ | `followup_d7.html` | `Se los dejo — último` | Breakup. Adelantado 1 día porque 30 abr = vuelo Japón |
| D14 | 2026-05-07 | — | — | Archive → `Perdido` si no responde |

**Si responde cualquier cosa (incluso "no me interesa"):** DETENER cadencia, actualizar `leads_data.json` → `status: "Respondió"` + `response: "<texto>"`.

## Pattern a replicar para próximos emails

- **Estructura HTML:** header navy + logo SPEKGEN, body sin hero image, keywords bolded en navy, 3 frases editorial italic gold (Instrument Serif), gold highlight gradient en línea clave, CTA gold + fallback URL + WhatsApp card + footer con link a spekgen.com.
- **Subject editorial:** formato `{Brand}, les armé algo` funciona bien en primer send. Alternativas: `Un sitio para {Brand} ↗` / `Una idea para su sitio — spekgen.com` para resends.
- **Copy español correcto:** tildes/ñ siempre verificadas (armé, día, mensaje).
- **Frase clave:** "agencia de marketing digital llegando a {ciudad del lead}" (no genérico).

## Pendientes Mr. Bu

- [ ] WhatsApp manual al `+52 33 5121 2595` con link al mockup
- [ ] Propuesta PDF cuando/si responde
- [ ] D3 follow-up 2026-04-26
- [ ] D7 follow-up 2026-04-29 (antes del vuelo)
- [ ] ClickUp/scheduled reminders para D3/D7 (no confiar en memoria humana pre-Japón)

## Archivos relacionados

- `PROSPECTOS/outreach/emails/P-003_mrbu/` — email.html/.txt, followup_d3.html/.txt, followup_d7.html/.txt, _send_instructions.md
- `PROSPECTOS/mockup_factory/templates/01_premium_travel/` — template reusable
- Dashboard lead: `PROSPECTOS/dashboard/leads_data.json` → P-003 (status Msg 1 Enviado, msg1Date 2026-04-23)
