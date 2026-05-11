# Prospects System — SPEKGEN OUTREACH

**Home:** `SPK - SPEKGEN AGENCY/PROSPECTOS/` — toda la infra vive aquí.
**README completo:** `SPK - SPEKGEN AGENCY/PROSPECTOS/README.md`

## Estructura

```
PROSPECTOS/
├── README.md                      ← mapa completo + pipeline + comandos
├── _publish_prospect.py           ← publica a spekgen.com (Shopify API, versioned)
├── config.json                    ← industrias (yates, hoteles_boutique, acuatico_lujo...)
├── dashboard/                     ← SOURCE OF TRUTH
│   ├── index.html · server.py
│   └── leads_data.json            ← 185 leads + status + URLs + Apollo
├── mockup_factory/
│   ├── build_mockup.py · fetch_place_data.py
│   ├── templates/mockup_v2.html   ← template {{PLACEHOLDER}}
│   └── generated/{slug}/          ← output por lead (index.html + photos/ + place_data.json)
├── outreach/                      ← Apollo enrich + email sender
└── ENLACE TELECOMUNICACIONES - LA PAZ/  ← primer LIVE
```

## Pipeline

1. `leads_data.json` tiene 185 leads (65 califican para mockup, 120 Falso Producto)
2. `build_mockup.py --lead-id P-XXX [--publish]`: scrape Google Maps → Apollo enrich → render template → publish a Shopify
3. `_publish_prospect.py` genera handle `/pages/{slug}mockup-v{hash}` + vanity redirect `/{slug}mockup`
4. Dashboard lee `leads_data.json` y muestra URLs reales + quick actions

## Qualification Gate (2026-04-21)

- `qualifiesForMockup` flag en cada lead
- `websiteStatus` field: `own_site` | `junk_aggregator` | `none`
- `JUNK_DOMAINS` list: facebook, tripadvisor, etc. (aggregators no cuentan como "web propia")
- Leads con web propia → status `Falso Producto` (pitchear otros servicios: content, ads, CRM)
- `--force` flag bypass para mockups de rediseño

## Gallery Design (uniform, no bento)

Post-iteración 2026-04-21: grid UNIFORME por row (cero bento, cero stretching, cero gaps). Layouts por count 1-8. Ver README para tabla.

## URLs publicadas

Always versioned `/pages/{handle}-v{hash}` para cache-bust. Vanity `/{slug}mockup` redirige.

Last 5 LIVE (2026-04-21):
- P-003 Mr. Bu Yachts · `/pages/mrbuyachtstravemockup-vc48665`
- P-044 Guaycura Tours · `/pages/guaycuratoursmockup-vf1a1fc`
- P-053 Lobitos Seafari · `/pages/lobitosseafarimockup-v04680a`
- P-082 Tridente Fishing · `/pages/tridentefishingmockup-v63cf78`
- P-108 Tu Polideportivo · `/pages/tupolideportivomockup-v4368cf`

## Apollo Integration

Free plan limitado a `/organizations/enrich`. Sobrescribe:
- Hero subtitle ← `apollo.description` (cleaned + truncated 200 chars)
- Services subtitle ← `apollo.keywords[:4]` joined
- Trust 3 num/label ← `apollo.founded_year` → "Desde YYYY"
- Category label ← `apollo.industry`

Fallback a `INDUSTRY_COPY` dict + `INDUSTRY_HERO_TEMPLATES` en `build_mockup.py`.

## Dashboard v2 (2026-04-23)

- **Sistema de archivado:** flag `archived: bool` en cada lead. Por default `filteredLeads()` excluye archivados. Toggle "📦 Ver archivados" en topbar. Contexto: 4,241 leads colgaban el UI (~60k nodos DOM). Ahora 28 activos = instantáneo.
- **Active set rule:** top 20 por (priority asc, rating desc, reviews desc) UNION (leads con msg1Date OR mockupLiveUrl OR status en `['Msg 1/2/3 Enviado','Propuesta Enviada','Respondio - Interesado','En Negociacion','CERRADO','Mockup Listo']`).
- **Columna "Progreso":** 3 dots coloreados (azul/teal/morado para Msg 1/2/3) + label `N/3`. Verde al CERRADO, rojo al Rechazo/Perdido. Tooltip con fechas.
- **Filter chips `0/3`, `1/3`, `2/3`, `3/3`** + **theme toggle 🌙/☀️** (localStorage persist, paleta light cream/navy/gold).
- **Quick launch:** `~/Desktop/SPEKGEN/Leads Dashboard.command` arranca server + abre browser. Symlinks a PROSPECTOS, outreach/emails, mockup_factory/generated.
- Backup pre-archive: `dashboard/backups/leads_data_pre_archive_YYYYMMDD_HHMMSS.json`.

## Outreach Email + WhatsApp (pattern validado 2026-04-23/24)

- **P-003 Mr. Bu** (23 abr): primer cold email enviado. Flujo: copy-paste HTML de Chrome → Gmail compose → "From" dropdown → `Spekgen Agency <outreach@spekgen.com>`. Alias verificado vía Gmail "Send mail as" (login real: `spekgen.ai@gmail.com` + app password en `SPK - SPEKGEN AGENCY/.env` como `SPEKGEN_GMAIL_APP_PASSWORD`).
- **P-082 Tridente Fishing** (24 abr): segundo envío real, multi-canal (email + WhatsApp). Email a `v.tridente@hotmail.com` + chain de 5 mensajes WhatsApp 9:12–9:17 AM. Mockup LIVE `spekgen.com/tridentefishingmockup`.
- **Template email:** HTML bulletproof navy/cream/gold en `PROSPECTOS/outreach/emails/P-XXX_slug/email.html`. Pattern: header navy con brand, body sin hero, keywords bolded en navy + 3 frases editorial italic gold (Instrument Serif), gold highlight gradient en línea clave, CTA gold + fallback URL + WhatsApp card + footer.
- **Pattern WhatsApp (5 mensajes en 5 min, validado Tridente):**
  1. Opener conversacional ("¿cuál es el canal indicado para una propuesta?")
  2. Contexto + link mockup (mencionar que ya se mandó por correo)
  3. Gancho de valor (observación específica del negocio)
  4. Credibilidad (nombre agencia + sitio web + ubicación)
  5. CTA suave ("quedo a sus órdenes")
  Tono: mexicano cordial, 1–2 emojis máximo. Hora óptima: 9:00–9:30 AM entre semana.
- **Cadencia:** D0 pitch (email+WA) + D3 bump "¿lo alcanzaron a ver?" + D7 breakup warm. Templates HTML+TXT por lead en `PROSPECTOS/outreach/emails/P-XXX_slug/` (email.html, followup_d3.html, followup_d7.html, whatsapp_sent.md, _send_instructions.md).
- **send_outreach.py** (batch automation) existe en `outreach/` pero para leads custom se usa flujo manual copy-paste. Para masivos: el script.

## Template Catalog (reutilizar, no construir desde cero)

- **T01 Premium Travel** (Mr. Bu) — yates/hoteles/tours high-end. Hero video + manifiesto editorial + testimonials Google.
- **T02 Ecommerce Retail** (Tridente) — retail físico con comunidad digital pero sin online. Catálogo + promos FB + add-to-cart mock + community stat. Incluye estandarizaciones aplicables a TODOS los mockups: accordion FAB 6 canales + anti-reuse triple-layer (ribbon + badge + watermark) + JS relocate a body.sample para escapar `transform` ancestor de Horizon. Ver `project_prospect_templates_catalog.md`.

## Estado 2026-04-24

- **Pool:** 4,241 leads totales. 26 activos · 4,215 archivados (archive masivo 2026-04-23 archivó false-positives Apify con 3 La Paz reales barridos por error).
- **Des-archivados manualmente:** P-061 IES Travel (8,506 fol), P-020 Baja Ocean Tours (5,016 fol), P-069 Viajes al Farah (1,818 fol).
- **P-082 Tridente Fishing:** tier=A manual (110K FB), ig_handle=tridentefishing, market_tier_source=manual. P-638 (dup) archivado.
- **Enrich La Paz archived job (PID 24933):** corriendo 747 targets rating≥4.7 + mentions La Paz/BCS. Auto-desarchiva tier A/B con bio La Paz real. Script: `PROSPECTOS/_enrich_la_paz_archived.py`. Wakeup 14:30 para revisar MAs encontrados.
- **Template general inline email (2026-04-24):** `PROSPECTOS/outreach/emails/_TEMPLATE_GENERAL/email.html` — 11 imágenes Shopify CDN + placeholders `{{NOMBRE}} {{NEGOCIO}} {{CIUDAD}} {{IG_HANDLE}}`. Script idempotente `_build_inline_email.py`. Reemplaza flujo con PDF adjunto (deprecated).

## Blockers / TODOs

- **Reviews scraping 0%**: tab selector Google Maps no matchea UI actual. `fetch_place_data.py` necesita fix. Mockups usan fallbacks honestos.
- **Build 16 mockups P1**: BajaProTours, WE BOAT BAJA, Casa 1880, Arena La Paz, Tu Polideportivo, Pescadería Punta Abreojos, Suites Hotel Baja Sol, BajaMark Fishing, Tecolote Beach, Las Gaviotas, Hotel Allende, New Baja Mex, Hotel Mágico del Mar, Parque Agua Escondida, Hotel Posadas Mora, Hotel Las Palmas. Meta pre-Japón (~7 días).
- **Dupes en leads_data.json:** P-722/P-053 Lobitos, P-712/P-044 Guaycura. Limpiar.
- **3 "Falso Producto" colados en activos** por msg1Date viejo: P-173, P-153, P-134. Re-archivar.
- **Re-run qualification** tras completar enrich job. Auditar leads con `websiteStatus` vacío (gate bug tipo P-027).
- **Dashboard tab communication:** reportar SIEMPRE qué tab del dashboard contiene el lead mencionado (Pending vs In Progress vs Archived) para evitar confusión tipo 2026-04-24.

## Referencias

- Skill `/publish-prospect`: encapsula Shopify publish logic (versioned handles, chrome hider, spk-grid rename)
- Memory sibling: `project_enlace_telecom_prospect.md` (primer LIVE) · `project_publish_prospect_skill.md` · `project_mrbu_outreach.md`
