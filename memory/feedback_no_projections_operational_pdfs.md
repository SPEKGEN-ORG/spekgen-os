---
name: No proyecciones en PDFs operativos
description: PDFs operativos (arquitectura de campañas, planes de trabajo) NUNCA deben incluir proyecciones de revenue, conversiones, escenarios Conservador/Realista/Optimista, ni funnels proyectados. Solo targets operativos y costos reales.
type: feedback
---

**Regla:** PDFs operativos (arquitectura de campañas, planes mensuales, dashboards de trabajo) NUNCA incluyen proyecciones de revenue, escenarios Conservador/Realista/Optimista, funnels con números proyectados ("de 1000 clics → 25 compras"), ni comparaciones "Costo vs Revenue Proyectado". Solo incluir **targets operativos** (CPL ≤ $X, completion ≥ X%, opt-in ≥ X%) y **costos operativos reales** (tokens, spend, infraestructura).

**Why:** Las proyecciones son ficción que sesga la toma de decisiones. En 2026-04-10, regenerando el PDF de GREENRAY Abril, Gibran pidió explícitamente eliminar las 3 secciones de escenarios ($4,100/$10,250/$20,500 revenue proyectado), el funnel "1000 clics → 450 quiz → 130 email → 25 compras", y el "Costo vs Revenue Proyectado" del blast ($200 vs $9,000). Razón directa: "no pongas proyecciones". Las proyecciones disfrazan supuestos como hechos y cuando no se cumplen generan falsa decepción o, peor, falsa confianza. Los targets operativos son medibles el día 1 (CPL real vs target); las proyecciones de revenue solo se pueden "validar" a fin de mes cuando ya es tarde para corregir.

**How to apply:**
- Aplica a TODO PDF operativo, dashboard de estrategia, reporte de planeación. NO aplica a: propuestas comerciales pre-contrato (donde el cliente pide ROI esperado), reportes post-campaña con métricas reales, modelos financieros explícitos.
- Si un PDF tiene `phase_summary` con escenarios de revenue, reemplazar con targets operativos (CPL, CTR, completion rate, opt-in rate, ROAS mínimo viable).
- Si tiene `budget_viz` con funnel proyectado, reemplazar con: stack de tracking (eventos GA4/Pixel), desglose de costos reales, distribución de presupuesto entre campañas.
- Si tiene líneas tipo "Revenue proyectado $X con conv 2.5%", borrar.
- Objetivo siempre: **lo que voy a medir**, no **lo que espero ganar**.
- Excepción única: cuando el cliente pide explícitamente "¿cuánto puedo esperar ganar?" en pre-venta — ahí sí modelar con escenarios, pero siempre etiquetado como "modelado, no garantizado".
