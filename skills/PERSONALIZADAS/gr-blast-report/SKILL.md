---
name: gr-blast-report
description: Genera reporte PDF de resultados de un WhatsApp Blast de GREENRAY — costos GHL, ventas Shopify, ROI, insights
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, Agent, mcp__Claude_in_Chrome__*, mcp__computer-use__*
---

# /gr-blast-report — Reporte de Resultados de WhatsApp Blast (GREENRAY)

> v1.0 — Analiza costos, ventas y ROI de un WhatsApp Blast ejecutado, y genera un PDF profesional con los resultados.

## Argumento

Numero de envio del blast (ej. "1", "2", "3") y opcionalmente la fecha de ejecucion.
Si no se proporciona fecha, buscar en `_CLIENT_CONTEXT.md` la fecha del blast correspondiente.

## Rutas base

```
GR_ROOT      = /Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/GR - GREENRAY
ENV_FILE     = {GR_ROOT}/.env
CONTEXT_FILE = {GR_ROOT}/_CLIENT_CONTEXT.md
KB_FILE      = {GR_ROOT}/_KNOWLEDGE_BASE.md
REPORT_DIR   = {GR_ROOT}/12. REPORTES
LOGO_PATH    = {GR_ROOT}/00. BRAND/00. VISUAL IDENTITY/LOGO/LOGO.png
TEMPLATE_PY  = {REPORT_DIR}/GR_WhatsApp_Blast1_Reporte.py
```

---

## FASE 0 — Pre-flight (automatico, no preguntar)

1. **Leer `.env`** para tener tokens de GHL y Shopify (no mostrar contenido)
2. **Leer `_CLIENT_CONTEXT.md`** para obtener:
   - Fecha de ejecucion del blast
   - Tag usado (ej. `blast-envio-1`, `blast-envio-2`)
   - Numero de contactos taggeados (si se registro)
3. **Determinar ventana de analisis**: desde la fecha del blast hasta hoy (o fecha especificada)
4. **Confirmar con Gibran**: "Voy a analizar el Blast Envio {N} ejecutado el {fecha}. Ventana de analisis: {fecha_blast} a {fecha_hoy}. Correcto?"

---

## FASE 1 — Recoleccion de Datos de Costos (GHL)

### Opcion A: Via GHL Agency Billing Dashboard (Chrome)
Si el navegador esta disponible:
1. Navegar a `https://app.gohighlevel.com/settings/billing?tab=wallet_transactions`
2. Filtrar por sub-account "GreenRay"
3. Filtrar por el mes correspondiente al blast
4. Leer los valores de:
   - **WhatsApp Usage** total (USD)
   - **WhatsApp Marketing Messages** cantidad y monto
   - **Communication** otros cargos
5. Capturar screenshot como evidencia

### Opcion B: Estimacion por contactos
Si no se puede acceder al dashboard:
1. Contar contactos con el tag del blast via GHL API:
   ```
   GET https://services.leadconnectorhq.com/contacts/?locationId={GHL_LOCATION_ID}&query=&limit=100
   ```
   Filtrar por tag `blast-envio-{N}`
2. Estimar costo: contactos × $0.032 USD por mensaje
3. Marcar claramente como ESTIMADO en el reporte

### Datos a registrar:
- `whatsapp_cost_usd`: Costo exacto WhatsApp Marketing Messages
- `whatsapp_messages`: Cantidad de mensajes cobrados
- `communication_cost_usd`: Otros cargos de comunicacion
- `make_cost_usd`: Costo de Make (generalmente $0 si se uso Python)
- `total_cost_usd`: Suma total
- `total_cost_mxn`: total_cost_usd × 17 (tipo de cambio aproximado)
- `contacts_tagged`: Total de contactos taggeados
- `delivery_rate`: whatsapp_messages / contacts_tagged

---

## FASE 2 — Recoleccion de Datos de Ventas (Shopify)

1. **Consultar ordenes de Shopify** en la ventana de analisis:
   ```python
   GET https://greenraynutraceuticos.myshopify.com/admin/api/2024-01/orders.json?status=any&created_at_min={fecha_blast}&created_at_max={fecha_fin}
   ```
   Headers: `X-Shopify-Access-Token: {SHOPIFY_ACCESS_TOKEN}`

2. **Para cada orden**, registrar:
   - Order number
   - Total (MXN)
   - Productos comprados
   - Tipo (regular vs draft order)
   - Si tiene codigo de descuento (no incluir el codigo en el reporte, solo si tuvo descuento o no)

3. **Validar atribucion**: Preguntar a Gibran cuales ventas son atribuibles al blast.
   - "Encontre {N} ordenes en la ventana de analisis. Cuales son atribuibles al blast?"
   - Si solo hay 1-2, probablemente todas son del blast
   - Si hay muchas, necesita confirmacion manual

### Datos a registrar:
- `orders`: Lista de ordenes atribuidas
- `total_revenue_mxn`: Suma de totales
- `total_orders`: Cantidad de ordenes

---

## FASE 3 — Calculo de Metricas

Calcular automaticamente:

```
roas = total_revenue_mxn / total_cost_mxn
roi_percent = ((total_revenue_mxn - total_cost_mxn) / total_cost_mxn) * 100
net_profit_mxn = total_revenue_mxn - total_cost_mxn
cpa_usd = total_cost_usd / total_orders
cpa_mxn = total_cost_mxn / total_orders
cost_per_message = total_cost_usd / whatsapp_messages
conversion_rate = total_orders / whatsapp_messages
```

---

## FASE 4 — Contexto y Comparacion

1. **Consultar ordenes del mes anterior** para baseline:
   ```python
   GET .../orders.json?status=any&created_at_min={mes_anterior_inicio}&created_at_max={mes_anterior_fin}
   ```

2. **Consultar respuestas en GHL** (opcional, si disponible):
   ```
   GET https://services.leadconnectorhq.com/conversations/search?locationId={GHL_LOCATION_ID}
   ```
   Contar conversaciones con mensajes sin leer en la ventana de analisis

---

## FASE 5 — Generacion del PDF

1. **Usar como base** el template Python en `{REPORT_DIR}/GR_WhatsApp_Blast1_Reporte.py`
2. **Crear una copia** con nombre: `GR_WhatsApp_Blast{N}_Reporte.py`
3. **Actualizar TODOS los valores** con los datos recolectados:

### Secciones del PDF:
1. **Header**: Logo GREENRAY, titulo "REPORTE DE RESULTADOS", subtitulo "WhatsApp Blast - Envio {N}", fecha de ejecucion
2. **KPI Cards**: ROAS, ROI, INVERSION, REVENUE — con valores y subtextos correctos
3. **Desglose de Costos**: Tabla con GHL WhatsApp, Communication, Make, Total (USD y MXN)
4. **Metricas de Entrega**: Contactos taggeados, mensajes cobrados, tasa de entrega, costo por mensaje, respuestas detectadas, ventas generadas, tasa de conversion
5. **Detalle de Venta(s)**: Tabla por cada orden (numero, productos, total, tipo, atribucion). NO incluir codigos de descuento.
6. **Analisis de ROI**: Tabla con inversion, revenue, ganancia neta, ROAS, ROI, CPA
7. **Insights y Recomendaciones**: 4 bullets con analisis inteligente:
   - Evaluacion de rentabilidad del canal
   - Analisis de tasa de entrega y recomendaciones
   - Respuestas activas y potencial de conversion futura
   - Proximos pasos (siguientes blasts programados o recomendaciones)
8. **Comparacion con periodo anterior**: Tabla comparativa ordenes/revenue/fuente

4. **Ejecutar el script** para generar el PDF
5. **Abrir el PDF** con `open` para que Gibran lo revise

### Output filename:
```
{REPORT_DIR}/GR_WhatsApp_Blast{N}_Reporte.pdf
```

---

## FASE 6 — Registro y Cierre

1. **Actualizar `_CLIENT_CONTEXT.md`**:
   - En la seccion de WhatsApp Blasts, agregar resultado del blast analizado
   - Formato: `Envio {N}: {fecha} | Costo: ${total_usd} USD | Revenue: ${total_mxn} MXN | ROAS: {roas}x | {total_orders} ventas`

2. **Actualizar `_KNOWLEDGE_BASE.md`** si hay aprendizajes nuevos:
   - Costo real por mensaje vs estimado
   - Tasa de entrega real
   - Tipo de productos que se vendieron
   - Cualquier insight sobre timing, dia de la semana, etc.

3. **Mostrar resumen a Gibran**:
   ```
   Blast Envio {N} — Reporte completo
   - Costo: ${total_usd} USD (~${total_mxn} MXN)
   - Revenue: ${total_revenue} MXN
   - ROAS: {roas}x | ROI: +{roi}%
   - PDF: {path_to_pdf}
   ```

---

## Reglas

- **Costos EXACTOS**: Siempre intentar obtener el costo real de GHL billing. Solo estimar como ultimo recurso y marcarlo claramente.
- **Atribucion honesta**: No inflar numeros. Si no esta claro que una venta es del blast, preguntar a Gibran.
- **Sin codigos de descuento**: NUNCA incluir codigos de descuento en el reporte (dato sensible).
- **Tipo de cambio**: Usar ~17 MXN/USD a menos que Gibran indique otro.
- **Copy en espanol correcto**: Tildes y acentos en el PDF (dentro de lo que permita reportlab con Helvetica).
- **Mantener diseño consistente**: Usar mismos colores, tipografia y estructura que el template base (green brand palette).

## GHL API Notes (de Knowledge Base)

- GHL API v2 NO soporta enviar WhatsApp templates directamente
- Workaround: Python taggea contactos → GHL Workflow detecta tag → envia template
- User-Agent debe ser "Make/2.0" (Cloudflare bloquea Python default)
- Rate limit: sleep 2s entre POSTs
- Billing de WhatsApp se cobra a nivel AGENCIA, no sub-account. Filtrar por "GreenRay" en el dashboard.
