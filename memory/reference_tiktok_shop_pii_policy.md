---
name: TikTok Shop PII policy and operational rules
description: TikTok Shop masks all PII on cancelled orders (hard wall). Rules for operating any client's TikTok Shop without violating ToS/LFPDPPP.
type: reference
---

## TikTok Shop PII — Hard Wall

TikTok Shop **enmascara del lado del servidor** toda la PII de pedidos cancelados/reembolsados:
```
Nombre:     A****** G******
Telefono:   (+52)753*****88
Email:      a*********@***********
Direccion:  ******,Ciudad,Estado,Pais
```

Aplica a: Seller Center UI, Open Platform API, CSV exports. Pedidos enviados exitosamente SI muestran PII completa (solo cancelados quedan redactados).

**Confirmado:** 2026-04-10 via Chrome MCP en seller-mx.tiktok.com (caso LO FITNESS).

## Reglas operativas (TODOS los clientes SPEKGEN con TikTok Shop)

**NO HACER NUNCA:**
- Outreach via WhatsApp/email/SMS a clientes de pedidos cancelados con datos obtenidos del Shop
- Exportar PII de TikTok Shop a herramientas externas (CRMs, listas de email) para marketing
- Prometer a un cliente "vamos a recuperar tus cancelados por WhatsApp" — es imposible Y ilegal

**Por que:**
1. TikTok Shop ToS: contactar clientes fuera de la plataforma para fines comerciales = strike / suspension de tienda
2. LFPDPPP Mexico: usar PII de transaccion cancelada para marketing sin consentimiento explicito = violacion (multas INAI $160K-$32M MXN)
3. UNA sola queja de cliente = store suspendido

**Alternativas legales para recuperacion:**
| Canal | Uso |
|---|---|
| Chat interno "Mensajes de clientes" | Solo responder, no iniciar |
| TikTok Pixel retargeting (viewed/no purchase) | Recuperar universo sin tocar PII |
| GMV Max ads con codigo promo publico | Re-engagement masivo anonimo |
| Responder reviews publicas | Reparacion reputacional |

## Onboarding checklist para cliente nuevo con TikTok Shop (OBLIGATORIO)

1. [ ] Vincular cuenta TikTok personal del cliente al Shop (desbloquea Video GMV)
2. [ ] Verificar TikTok Pixel en el sitio web del cliente
3. [ ] SLA firmado: <48h envio o escala a SPEKGEN
4. [ ] Make scenario: webhook nuevo pedido → notificacion WhatsApp/email
5. [ ] Make scenario: cron diario lee "Para enviar", alerta si algo >24h
6. [ ] Make scenario: cron semanal volcado de metricas a Google Sheets
7. [ ] Revisar si hay creditos GMV Max disponibles (programa promocional TikTok)
8. [ ] Dashboard cross-client en Content Hub con seccion TikTok Shop

## Como Claude puede gestionar TikTok Shop

| Metodo | Prioridad | Uso |
|---|---|---|
| Make.com (modulos oficiales TikTok Shop + Ads) | 1 | Scenarios automaticos, sync a Sheets |
| Chrome MCP (seller-mx.tiktok.com) | 2 | Operacion ad-hoc mientras Make no esta |
| TikTok Shop Open Platform API | 3 | Requiere developer approval 1-3 semanas |

**IDs conocidos de LO FITNESS (primer cliente con TikTok Shop):**
- Store: "LO Fitness by Lupita Orejel"
- oec_seller_id: `7496149780483312383`
- Business Center: `7492465198712979472`
- Ads Manager: `7492465224990130177`
- Warehouse: `7493537799993313032`
