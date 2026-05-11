---
name: GR Blaster Abril 2026 — campaña completa
description: Resultado de la campaña WhatsApp 3-envíos de GreenRay Abril 2026, status final por envío y aprendizajes operativos
type: project
originSessionId: 92abcfdc-f4fe-4e9f-9af3-be0db482e65f
---
Campaña WhatsApp Abril GreenRay completada 2026-04-17. 3 envíos a base de ~398 contactos GHL (390-400 universo, -2 excluidos).

**Status por envío:**
- Envío 1 (Catálogo, `blast-envio-1`, template `mensaje_1_blaster_abril`) — 6 Abr — 253/389 OK, 136 fallidos (retry pendiente al cierre)
- Envío 2 (Top 5, `blast-envio-2`, template `blaster_mensaje_2_abril`) — 8 Abr — Ejecutado
- Envío 3 (Oferta GREENRAY10, `blast-envio-3`, template `blaster_3 (es_MX)`) — 17 Abr — 398/398 OK + retry 69/69 (msj3notdelivered) OK

**Why:** Cerrar campaña 3-touch con CTA fuerte (10% OFF + envío gratis +$1500, 48h) antes del análisis ROI consolidado. Envío 1 generó ROAS 10.5x ($1,455 MXN) — base que justifica seguir invirtiendo en blasters mensuales.

**How to apply:**
- Patrón estándar para futuros blasters GR: tag GHL → workflow "BLASTER ABRIL" (1 WF, N triggers por tag, N templates) → drip interno de GHL maneja WhatsApp throttle. Bulk-tag desde `blast_tag_contacts.py --no-drip` es seguro porque GHL hace el rate-limit.
- Retry pattern: contactos con tag `msj{N}notdelivered` se re-procesan con `retry_envio{N}_failed.py` (delete tag, delete blast tag, re-add blast tag → re-dispara WF).
- Pitfall observado: si el template GHL fue renombrado/reemplazado (ej. `mensaje_3_blaster_abril` → `blaster_3`), TODOS los pasos del WF deben actualizarse. Si queda un step apuntando al viejo, falla con error #132001 "Template name does not exist in the translation". Verificar TODOS los branches del WF antes de disparar.
- Próximo entregable: `/gr-blast-report 3` 48-72h después del envío para PDF de ROI consolidado (ventas Shopify atribuidas a código GREENRAY10 + costos GHL).
