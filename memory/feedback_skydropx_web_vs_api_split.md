---
name: Skydropx web UI ≠ Skydropx Pro API v1
description: La cuenta web de skydropx.com y la cuenta Pro API v1 son spaces distintos. Guías generadas en web NO aparecen via API. Descubierto fixeando pedido HC #1035.
type: feedback
originSessionId: 35260a28-0365-4b13-99d0-cb2bb8960ecf
---
Skydropx tiene DOS productos con cuentas separadas:

1. **skydropx.com (web UI)** — generación manual de guías. Login web normal.
2. **Skydropx Pro API v1** — `https://pro.skydropx.com/api/v1`. OAuth client_credentials con `SKYDROPX_CLIENT_ID` + `SKYDROPX_CLIENT_SECRET`.

**Reglas:**
- **Las guías generadas en web UI NO aparecen via API**. `GET /shipments` solo lista las creadas via API misma.
- Tracking numbers de web UI no se pueden consultar via API endpoints (404).
- No hay forma de "sincronizar" — son universos paralelos.

**Por qué importa:** Cuando el flow auto falla (ej. Skydropx API rechaza dirección con `#`, `&`, "dentro del módulo X"), la fallback típica es generar guía manual desde web UI. Eso significa que el sistema NO puede recuperar la guía programáticamente — hay que pedirle el PDF al humano que la generó.

**Cloudflare gotcha:** ambos endpoints (api.skydropx.com y us2.make.com) bloquean requests sin `User-Agent` header → 403 Forbidden. Siempre incluir `User-Agent: Mozilla/5.0 ...` en scripts.

**Implicación de diseño:** el sistema HC tiene fallback manual cubierto via Make alert (scenario 4780569 nuevo módulo 5 que avisa a Gibran cuando edge function devuelve sin `tracking_number`). El humano genera guía → reenvía PDF al equipo manualmente. No hay automation cross-API posible.

**Origen:** sesión 2026-04-30 fixeando pedido HC #1035 (Giselle Giovanna Román, dirección "Murcielago #41 dentro del módulo murciélago" rechazada por Pro API).
