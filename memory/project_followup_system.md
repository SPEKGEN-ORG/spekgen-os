---
name: Follow-up system architecture
description: Sistema de seguimientos automaticos — ClickUp + Cloud Scheduled Task + Gmail SMTP
type: project
---

## Arquitectura

1. **ClickUp lista "Seguimientos"** (list ID: 901712468948, espacio Spekgen) — una sola lista para todos los clientes
2. **Cloud Scheduled Task** "SPEKGEN Follow-up Notifier" — corre diario a 9am GMT-7, en la nube (sin PC)
3. **Script `send_email.py`** en `SPK - SPEKGEN AGENCY/SPK - 10. AUTOMATION/followup-notifier/` — envía via Gmail SMTP desde spekgen.ai@gmail.com
4. **Credencial**: SPEKGEN_GMAIL_APP_PASSWORD en SPK - SPEKGEN AGENCY/.env

## Formato de tareas en ClickUp

La descripción de cada tarea debe tener:
```
EMAIL_CONTACTO: correo1@ejemplo.com,correo2@ejemplo.com
NOMBRE_CONTACTO: Nombre o grupo
CLIENTE: HC | LF | GR | MG
MENSAJE:
Texto del follow-up que se enviará tal cual.
```

## Flujo
- Gibran dice "mandé X a Y, follow up en Z días"
- Claude crea tarea en ClickUp con due date y mensaje pre-escrito
- A las 9am, agente cloud revisa tareas vencidas → manda correo → comenta en ClickUp
- Gibran recibe copia de cada correo + digest resumen diario

**Why:** Gibran pierde follow-ups porque se le pasan las fechas. Automatizar evita pérdida de oportunidades.
**How to apply:** Cada vez que Gibran mencione que mandó algo a un cliente, ofrecer crear el follow-up en ClickUp.
