# Project — IES Travel (P-061) Outreach

**Status:** Mockup Listo — cita martes 5 mayo 2026 (hora pendiente confirmar)

## Quick reference

| Campo | Valor |
|---|---|
| ID interno | P-061 |
| Negocio | IES Travel |
| Industria | agencia_viajes / dive_snorkel / tour operator |
| Tier | C (lead) / market_tier B (8.5K IG) |
| Ubicación | Muelle Fiscal, Zona Comercial, La Paz BCS |
| Tel/WA | 612 161 8821 / wa.me/526121618821 |
| Email | iestravelreservaciones@gmail.com |
| IG | @ies_travel (verificada, 8.5K followers) |
| FB | facebook.com/iestravelmx |
| Google | 4.8★ con 22 reviews · cid=3714063782779657803 |
| Slug | iestravel |
| Mockup LIVE | https://spekgen.com/iestravelmockup (handle `iestravelmockup-vb08d7d`) |
| Propuesta | NO existe aún (pendiente generar si hay interés) |

## Servicios reales del cliente (del FB)

- **Credenciales:** Guías certificados NOM-09 turismo de naturaleza · Capitanes certificados Tiburón Ballena
- **Especialidades:**
  1. Alimentos frescos en todos los tours
  2. Campamento o día en Espíritu Santo
  3. Balandra + nado con lobos en San Rafaelito (lugar específico, NO "Los Islotes")
  4. Pesca con "El Rey" (capitán experto, nombre real)
  5. Avistamiento y nado con tiburón ballena
  6. Apnea, SCUBA, senderismo en áreas remotas y zonas de refugio

## Material real disponible

Ubicación: `SPK - SPEKGEN AGENCY/PROSPECTOS/mockup_factory/generated/iestravel/photos/`

- `IES TRAVEL LOGO.jpg` — logo oficial (barco navy + olas turquesa + wordmark)
- `CAMPAMENTO.jpg` — comedor bajo toldo con mantel azul marino
- `CAMPAMENTO 2.jpg` — tiendas de campaña en playa con montañas
- `CAMPAMENTO 3.jpg` — toldo azul marino tensado, mesas y sillas blancas
- `video1_web.mp4` — intro general (3.5MB, 720p)
- `video2_lobos_web.mp4` — lobos marinos (5.8MB)
- `video3_fauna_web.mp4` — fauna marina (1.8MB)
- `video4_tours_web.mp4` — tours generales (1.5MB)
- `video5_camp_web.mp4` — campsite (1.3MB)
- + balandra.jpg, camping.jpg, espiritusanto.jpg, hero.jpg (Unsplash que sí pegaron)

## Paleta visual del mockup (basada en logo real)

- `--ies-navy: #0d2845` — primary
- `--ies-deep: #061a30` — dark sections
- `--ies-cyan: #5fb3d6` — accent
- `--ies-turquoise: #7ed4e6` — highlight
- `--ies-sand: #f5e9d4` — warm neutral
- `--ies-pearl: #fdfaf3` — body bg

## Pendientes críticos

- [ ] **CRÍTICO:** Confirmar hora + contacto del meeting de mañana 5 mayo por WA al 612 161 8821
- [ ] Crear evento en Google Calendar con datos confirmados
- [ ] Generar `iestravelpropuesta` con paquetes/pricing si Gibran lo pide post-cita
- [ ] Post-cita: actualizar P-061 status según resultado (Mockup Listo → Reunion Hecha → Esperando Respuesta → Cerrado Ganado/Perdido)
- [ ] Si firma: pedir 30+ fotos reales adicionales (lobos, tiburón ballena, pesca)

## Aprendizajes aplicables a futuros prospects

- **NUNCA inventar branding del cliente** — usar logo real, paleta del logo, fotos reales. Si no hay, pedir antes de codear.
- Videos FB/IG → bajar con yt-dlp + comprimir con ffmpeg + usar `<video>` nativo (NO iframes plugin). Detalle en `feedback_fb_ig_videos_yt_dlp_pipeline.md`
- FAB widget en Shopify-deployed mockups → re-parentear al body con JS. Detalle en `feedback_fab_widget_shopify_reparent.md`
- Cuando el lead aparece en otro batch del xlsx con LP-XXX distinto: append manualmente al xlsx con id P-XXX (igual que Green & Rosse P-1353 row 192)

## Origen del lead

Encontrado el 2026-05-04 buscando en xlsx batch #7 + JSON canonical después de que Gibran olvidó iniciar el flow del mockup. Status original "MAYBE MOCK UP" en notas de cold outreach del jueves 30 abril 2026.
