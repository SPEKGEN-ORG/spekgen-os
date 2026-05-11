---
name: PRIMER WIN — Ferreterías Duarte (cerrado 2026-05-06) → MUTADO a Ferre24 opción C (2026-05-07)
description: P-9001 cerrado fork 1 Duarte $17K. Mutado 2026-05-07 a Ferre24 opción C $32K + $10.5K/mes. Anticipo $8.5K reasignado. Marca Duarte invisible al frente
type: project
originSessionId: 9ad7acfb-0fe3-41d9-bfdb-39b5656a86ca
---
**Primer WIN oficial registrado en el pipeline del Operations Hub. Mutado al día siguiente del cierre.**

## Cierre original (2026-05-06) — fork 1 Duarte

- **Cliente:** Sergio Duarte / Ferreterías Duarte (Tinguindín, Michoacán)
- **ID:** P-9001
- **Cerrado:** 2026-05-06
- **Setup:** $17,000 MXN (one-time)
- **Retainer:** $7,500 MXN/mes (incluye 100 SKUs/mes; bloques adicionales de 50 SKUs a $1K c/u)
- **Vigencia propuesta:** REV.A locked al 19 mayo 2026
- **Mockup live:** https://spekgen.com/duartemockup
- **Hub local:** `PROSPECTOS/_prospectos/SERGIO DUARTE - FERRETERIA DUARTE/HUB_DUARTE_CLIENTE.html`
- **Anticipo:** depósito 5-may $8,500 (registrado en `SPEKGEN_AGENCIA_FINANZAS.xlsx` MOVIMIENTOS)
- **Folder oficial original:** `FD- FERRETERIAS DUARTE/` (creada 2026-05-06)

## Mutación (2026-05-07) — fork 2 Ferre24 opción C

Sergio mandó 2 audios WhatsApp 2026-05-07 proponiendo cambiar de fork 1 a fork 2 (Ferre24). Razones explícitas: cobertura territorial GDL + marca anónima (anti-envidia local) + impacto de marca nueva. Confirmado con imagen aclaratoria de las 3 opciones (precio C = $32K).

- **Setup mutado:** $32,000 MXN (+$15K delta vs fork 1)
- **Anticipo reasignado:** $8,500 (ya cobrado al fork 1) → setup C
- **Saldo go-live:** $23,500 MXN
- **Retainer mutado:** $10,500 MXN/mes (+$3K delta vs fork 1) — incluye rotación trimestral de 4 catálogos editoriales propios
- **Año 1 piso:** $32K + 11 × $10.5K = **$147,500 MXN** (vs $99,500 del fork 1)
- **Folder renombrado:** `F24- FERRE24/`
- **Marca pública:** Ferre24 (Duarte invisible al frente)
- **Dominio:** ferre24.com.mx (comprado por SPEKGEN, incluido en setup)
- **Pipeline ID:** P-9001 conservado (NO se abre P-9001-MERGE separado; P-9002 Ferre24 ya no existe como propuesta abierta — mergeado a P-9001)
- **Implementación reseteada:** 3-4 semanas desde 7-may → go-live target ~28-may a 4-jun
- **Pendientes bloqueantes (Sergio):** distribución 200 SKUs · 4 categorías editoriales · recursos branding · firma Addendum REV.B
- **Estado clientes activos:** F24 pasa a 5to cliente activo SPEKGEN con retainer $10.5K (vs $7.5K original). CLAUDE.md root + `_SERVICIOS_CONTRATADOS.md` + `delivery_data.json` actualizados 2026-05-07.

**Why:** Significancia financiera — primer ingreso confirmado de pipeline outreach SPEKGEN (no retainer recurrente preexistente). Mueve el indicador de "0 cerrados de pipeline" → "1 caso validado del modelo SPEKGEN end-to-end". Importante para Gibran dada la presión financiera (deuda Claude Max + meta $100K MXN/mes mayo 2026). **Bonus 2026-05-07:** la mutación a opción C subió el ticket total ~50% (de $99.5K a $147.5K año 1) sin renegociar — el cliente pidió más scope por más dinero el día siguiente del cierre.

**How to apply:**
- Cuando Gibran necesite confianza/prueba social interna sobre que el modelo SPEKGEN funciona, citar este caso.
- Estructura del deal (Setup ancla + retainer recurrente + bloques expandibles de SKUs) es el patrón a replicar para próximos cierres ecommerce/retail. Ver `project_sergio_duarte_ferre24.md` para detalles del deal pre-merge y `project_ferre24_active.md` para el estado activo post-merge.
- **Lección "merge mid-flight":** un cliente puede pedir mutación de scope el día siguiente del cierre formal. NO es renegociación, es upgrade natural. Aclarar delta económico explícito antes de aceptar verbalmente, NO abrir nuevo Pipeline ID, reasignar anticipo (no devolver), generar Addendum REV.B firmado. Detalle en `F24- FERRE24/_KNOWLEDGE_BASE.md` sección "Patrón merge mid-flight".
- Registrar TODO close futuro con shape: `priceClosed` + `dealType` + `closeDate` en el JSON del Operations Hub para que el deal pill verde de WIN muestre el monto en el kanban.
