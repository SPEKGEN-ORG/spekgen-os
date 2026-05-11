---
name: Agency emails come from spekgen.ai@gmail.com, not client gmail
description: Automations/ops emails to warehouses, vendors, partners must be sent from spekgen.ai@gmail.com (SPEKGEN = the agency managing HC/LF/GR/MG). Client gmails (healthychuchos@, lofitness@, greenraymx@, metagreenlabs@) are only for direct client-facing communication.
type: feedback
originSessionId: 3a9fb5be-5b36-4397-870f-d6f45e992e8d
---
**Regla:** Cualquier email automatizado/operativo (almacén, guías, notificaciones internas, reportes, follow-ups) debe salir desde `spekgen.ai@gmail.com`, NUNCA desde el gmail del cliente (healthychuchos@, lofitness@, etc.).

**Why:** SPEKGEN es la agencia que gestiona las automatizaciones. El cliente (HC/LF/GR/MG) recibe el servicio — no es quien ejecuta. Enviar desde el gmail del cliente confunde al destinatario (parece que la notificación viene del cliente mismo) y rompe la trazabilidad operativa.

**How to apply:**
- Credencial: `SPEKGEN_GMAIL_APP_PASSWORD` en `SPK - SPEKGEN AGENCY/.env`. User: `spekgen.ai@gmail.com` (no hay `SPEKGEN_GMAIL_USER` var explícita, hardcodear el user).
- From header: `SPEKGEN (Nombre del Cliente) <spekgen.ai@gmail.com>` para que se vea de qué cuenta de cliente es el tema.
- Reply-To: `gibran.alonzo0506@gmail.com` para que respuestas lleguen a Gibran directo.
- Excepción: emails directos al cliente final (ej. cliente final que compró en la Shopify de HC recibe su ticket) → ahí sí va desde el gmail del cliente porque es customer-facing de esa marca.
- Los gmails de cliente (healthychuchos@, lofitness@, greenraymx@, metagreenlabs@) quedan SOLO para: comunicación directa con el cliente final de esa marca, outreach B2B de esa marca, y Google Business de esa marca.
