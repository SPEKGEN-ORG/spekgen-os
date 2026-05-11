# Green & Rosse — P-1353-B (fork web CERRADO 8-may, fork bot abierto)

**Última update:** 2026-05-08

## Status global

- **Fork WEB:** ✅ CERRADO 2026-05-08. Setup único $3,500 + IVA = **$4,060 MXN**. Pendiente depósito Banco Azteca CLABE 1273 2001 3042 310803. Sin mantenimiento contratado (en evaluación). Onboarding pack entregado: brief PDF + carpeta `client_assets/` 16 subcarpetas + xlsx tracking interno 39 assets. Mockup live `spekgen.com/greenrossemockup` con fix Lenis (drag/swipe + VER button). Source of truth: `PROSPECTOS/_prospectos/GREEN AND ROSSE - LA PAZ/_CLIENT_CONTEXT.md`
- **Fork BOT:** 🟡 ABIERTO. Pedro construye demo, deadline demo 15-may, propuesta vence 19-may. Detalle abajo.

## Quién es

Restaurante de **brunch all-day** frente al Malecón de La Paz BCS. Álvaro Obregón S/N, Centro. Operando desde 2021. 5★ TripAdvisor, 4.7★ Google. Sano · Fresco · Natural · Pet friendly · Gluten free real · Café de altura · Panadería propia.

**Horario:** Lunes a Domingo, **7:30 AM – 4:00 PM** (cocina cierra 3:30). Sin servicio nocturno.

**Capacidad:** 12 mesas total = **6 terraza** (vista Malecón, las VIP) + **6 interior**.

**Idiomas:** español + inglés (turismo nacional/extranjero).

## Pipeline

- Carpeta: `SPK - SPEKGEN AGENCY/PROSPECTOS/_prospectos/GREEN AND ROSSE - LA PAZ/`
- Mockup web: `mockup_website/index.html` (paleta sage/cream/coral/honey, fonts DM Serif Display + Cormorant Garamond + Pinyon Script + Inter)
- Propuesta bot: `propuesta_bot/PROPUESTA_BOT_GREEN_ROSSE.pdf` — 3 planes mensuales sin setup
  - Básico $3,500 MXN/mes (bot WA bilingüe + reservas web + lista espera + recordatorios + reporte mensual + mejoras semanales)
  - Esencial $5,500 (mejoras diarias + reportes semanales + soporte <4hr) ← recomendado
  - Avanzado $8,500 (+voice notes WA + recepcionista IA llamadas + reporte ejecutivo)
- Plazo mínimo 3 meses, mes a mes después
- **Vigencia propuesta: 19 mayo 2026**

## Demo en construcción

- Pedro construye el demo bot. Brief en `propuesta_bot/BRIEF_DEMO_PEDRO.md`.
- **Deadline demo:** 15 mayo (4 días antes que venza la propuesta).
- Stack acordado: WhatsApp Cloud API directo de Meta (NO GHL) + Make + GPT-4o-mini + Google Sheets como DB.
- 8 casos obligatorios: reserva nueva, lista espera terraza llena, cancelación con avance de cola, modificación, recordatorio día-antes con confirma/no-confirma/no-responde, fuera de horario, auto-detect inglés, notif staff por WA.
- Tono bot: cálido, casual-elegante, breve, máximo 1 emoji temático (🌿 ☕ 🥐 🐾), nunca corporativo.
- Datos demo: 12 mesas con IDs (T1-T6, I1-I6), slots 90 min, 6 reservas precargadas en terraza para forzar mostrar lista de espera durante la venta.

## Pain points del prospecto (lo que les dolió en la llamada)

1. Llamadas perdidas en hora pico (9–11 AM sábado/domingo) — nadie del piso puede contestar.
2. No-shows ~20% por no haber recordatorio automático.
3. Terraza se asigna a ojo, no saben en tiempo real qué está ocupado.
4. Turismo bilingüe — clientes USA/CAN preguntan en inglés y a veces no contestan rápido.

## Pendientes Gibran

- [ ] Mandar brief a Pedro + alinear 30 min antes que empiece a construir
- [ ] Decidir si crear WA Cloud API nueva en BM Agencia (`2131750914244150`) o usar número personal de prueba
- [ ] Revisar primera versión cuando Pedro tenga 3 casos funcionales
- [ ] Probar demo end-to-end antes de la llamada de venta
- [ ] Agendar llamada de venta (target: semana 12-19 mayo)
