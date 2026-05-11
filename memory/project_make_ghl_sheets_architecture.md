---
name: Make + GHL + Sheets Architecture
description: Standard data architecture for all forms/surveys/lead ads. Sheets = data warehouse, GHL = CRM comms, Make = router. No manual custom fields.
type: project
---

## Arquitectura estándar: Make + GHL + Sheets

**Decisión tomada:** 2026-04-03 por Gibran.

### Principio
- **Google Sheets = fuente de verdad** para datos de formularios, surveys, lead forms, quizzes
- **GHL = CRM de comunicación** (contacto + pipeline + SMS/email sequences + AI employee)
- **Make = router central** que distribuye datos a ambos destinos

### Por qué
- Custom fields en GHL no escalan (requieren config manual por cada form nuevo)
- SPEKGEN 100% AI necesita que nuevos forms/surveys se conecten sin tocar GHL settings
- Sheets permite columnas dinámicas sin configuración
- Claude puede leer Sheets directamente para análisis, cotizaciones, reportes
- GHL es valioso por comunicación, no por almacenamiento de datos

### Flujo estándar

```
[Fuente de datos] → Make Webhook/Trigger
                        ↓
                    Make Router
                   ↙         ↘
             Sheets            GHL
        (todos los campos)   (nombre, tel, email, tags,
                              source, 1 campo "Notas" resumen)
                                ↓
                          GHL automático
                    (SMS bienvenida, email sequence,
                     pipeline move, AI employee)
```

### Fuentes de datos soportadas
1. **HTML Forms** (como discovery form de Iris) → Make Custom Webhook
2. **Facebook/IG Lead Ads** → Make Facebook Lead Ads trigger
3. **GHL Forms/Surveys** → Make GHL trigger o webhook
4. **Website Quiz** (como MetaGreen) → Make Custom Webhook

### Mapeo a GHL (siempre igual)
- `firstName` → nombre
- `phone` → teléfono/whatsapp
- `email` → email
- `tags` → tipo de form (ej: "discovery-form", "lead-ad", "quiz")
- `source` → origen (ej: "SPEKGEN Discovery Form", "FB Lead Ad - Campaign X")
- `customField.agssMpYplnBAYYgdV0zf` (Notas Adicionales) → resumen de TODOS los campos en texto

### Mapeo a Sheets (siempre igual)
- Una hoja por cliente o por tipo de form
- Columnas = todos los campos del form tal cual
- Columna extra: Timestamp, Source

### Para AI Employee de GHL
El resumen en "Notas Adicionales" contiene suficiente contexto. Si necesita más detalle, Make puede jalar de Sheets y pushear a GHL on-demand.

### Infra actual en Make
- **Team ID:** 354061
- **Org ID:** 2681221
- **Conexión Facebook:** ID 8150575 (Gibran Alonzo García, expira May 31 2026)
- **Conexión GHL:** ID 8175036 (Location: METAGREEN)
- **Webhook Discovery Forms:** `https://hook.us2.make.com/r1birk8x9s7x2wg9fujojvx5db4zgnj2`

**How to apply:** Cada vez que se cree un nuevo form, survey, quiz, o lead ad para cualquier cliente, seguir este patrón. No crear custom fields en GHL. Sheets es el data warehouse.
