---
name: SPEKGEN Finanzas Tracker (Carpeta 09. FINANZAS)
description: Source of truth finanzas. Desde mayo 2026 cuenta dedicada Banco Azteca SPEKGEN — agencia separada de personal. Fuente nueva = SPEKGEN_AGENCIA_FINANZAS.xlsx (compartido con Pedro)
type: project
originSessionId: d8d67927-4170-4520-8588-26528a98b57d
---
## Ubicacion

`SPK - SPEKGEN AGENCY/SPK - 09. FINANZAS/`

- **`SPEKGEN_AGENCIA_FINANZAS.xlsx` ← FUENTE DE VERDAD desde mayo 2026** (cuenta Banco Azteca SPEKGEN, agencia pura)
- `_build_agencia_finanzas_xlsx.py` — script para regenerar el xlsx (correr con `/usr/bin/python3`, NO `python3` brew — openpyxl solo está en /usr/bin/python3)
- `_FINANZAS_CONTEXT.md` — narrativa + histórico personal+agencia
- `SPEKGEN_CASHFLOW.xlsx` — legacy mezclado (no tocar)
- `_GHL_BILLING_AUDIT.md` — desglose GHL por cliente
- `01-04. ESTADOS / SCREENSHOTS / COMPROBANTES / FACTURAS/` — soporte documental

## Cambio mayo 2026 (Why)

Primer ingreso real de cliente nuevo (Ferreterias Duarte, $8,500 anticipo 50% setup, 5-may-2026) → cuenta dedicada Banco Azteca SPEKGEN. Visibilidad compartida con Pedro vía Drive. Marca el split entre "mismo bolsillo personal+agencia" (legacy) y "agencia pura" (nuevo).

## Estructura del xlsx nuevo (7 hojas)

1. `DASHBOARD` — KPIs con fórmulas (saldo, P&L mes, ad spend, SaaS consumido). Sin captura.
2. `MOVIMIENTOS` — append-only. UNA fila = UN movimiento. Fuente de verdad.
3. `INGRESOS_CLIENTES` — proyección + tracking retainers + setup
4. `GASTOS_FIJOS` — SaaS recurrentes (Make + Google One placeholder, Pedro/Gibran llenan)
5. `AD_SPEND` — presupuesto vs consumido por cliente/mes (HC LF GR MG)
6. `NOMINA_SOCIOS` — vacío (nadie cobra todavía). Estructura lista.
7. `CATEGORIAS` — taxonomía/dropdowns

## Calendario cobros base ($38,096/mes)

| Cliente | Día | Monto | Origen | Factura |
|---|---|---|---|---|
| HC | 19 | $7,500 | Monse Alonzo | No |
| LF | 28 | $17,400 | Lupita | CFDI (sub $15K + IVA $2.4K) |
| GR | 30 | $6,198 | Papá (Enrique Alonzo) | No |
| MG | 30 | $6,998 | Papá (Enrique Alonzo) | No |

**Adicional mayo 2026:** Duarte 50% restante setup $8,500 al entregar (~19 may)

## How to apply

1. Cuando Gibran hable de finanzas SPEKGEN agencia (mayo 2026 en adelante) → trabajar sobre `SPEKGEN_AGENCIA_FINANZAS.xlsx`. El xlsx legacy es solo histórico.
2. Para registrar nuevo movimiento → agregar fila en hoja `MOVIMIENTOS` (no en otras hojas — el dashboard jala de ahí con fórmulas).
3. Cuando un retainer se cobra → marcar `pagado` + `fecha_real` en `INGRESOS_CLIENTES` Y agregar fila en `MOVIMIENTOS` con categoria `retainer_cliente`.
4. Si cambia la estructura → editar `_build_agencia_finanzas_xlsx.py` y regenerar (script reescribe el xlsx desde cero — perderías datos capturados, así que mejor para cambios estructurales tempranos).
5. NO meterse en temas fiscales (declaraciones, IVA, retenciones) — Gibran lo ve con contador externo.
6. NO mezclar movimientos personales (Nu/Albo/MP) en este xlsx — son cuentas distintas. Para histórico personal usar `_FINANZAS_CONTEXT.md`.

## Banco Azteca API

No es self-service para cuentahabientes. APILab solo B2B con contrato comercial firmado (apertura de cuentas como servicio, no "lee mis movimientos"). Para automatizar pull de transacciones futuro → Belvo (~$0.30 USD/sync, soporta Banco Azteca como institución conectable). Por ahora volumen es bajo (4-5 mov/mes) → captura manual desde el xlsx.
