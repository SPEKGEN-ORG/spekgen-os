# Cross-Client Intel — 2026-04-17 (Snapshot)

Primer ejercicio formal cross-client de Meta Ads. Ventana 14d (2026-04-03 → 2026-04-17), 3 cuentas (LF, HC, GR). Meta Marketing API v21.0 via `SPK - SPEKGEN AGENCY/SPK - 00. COMMAND CENTER/03. HERRAMIENTAS/_cross_client_intel/cross_client_pull.py`.

## Snapshot de cuentas

| Cliente | Ads activos | Spend | Compras | ROAS |
|---|---:|---:|---:|---:|
| LF | 21 | $4,035 | 6 | 2.11 |
| GR | 5 | $1,476 | 1 | 1.92 |
| HC | 13 | $1,188 | 1 | 0.76 |

## 5 ads pausados hoy ($4,264 total quemado)

- `LF-049_METAFIT_PROBLEM_SOLUTION` — ad_id 120243603540450731 ($2,138)
- `LF-047_METAFIT_TESTIMONIAL` — ad_id 120243603475990731 ($516)
- `GR-AD-004_GXAMIN` — ad_id 23855052716580796 ($650)
- `HC-AD-DOLOR-SILENCIOSO-CAROUSEL` — ad_id 6911066326834 ($374)
- `HC-DR-ESTRES-CAROUSEL` — ad_id 6911066404634 ($366)

Log JSON: `SPK - SPEKGEN AGENCY/SPK - 00. COMMAND CENTER/03. HERRAMIENTAS/_cross_client_intel/pause_log_20260417_0909.json`.

## Winners identificados

1. **UGC_PERSONA (LUPITA)** — LF ROAS 16.55. Replicar en HC (tutor perro) y GR (mujer 40+).
2. **OFFER 2PACK/KIT** — LF ROAS 4.37, HC 27x micro. Replicar en GR, escalar en HC $33 → $150/dia.

## Docs creados

- `SPK - SPEKGEN AGENCY/SPK - 00. COMMAND CENTER/02. DOCS OPERATIVOS/NAMING_CONVENTION_ADS.md` — estandar `[CLIENT]-AD-[NNN]_[FORMATO]_[PRODUCTO]_[VARIANTE]` + plan migracion GR (14d).
- `SPK - SPEKGEN AGENCY/SPK - 00. COMMAND CENTER/02. DOCS OPERATIVOS/FORMAT_TAXONOMY.md` — 16 formatos con ejemplos reales, ROAS observado, receta.
- Updates a 3 `_CLIENT_CONTEXT.md` (LF, HC, GR) + `_KNOWLEDGE_BASE.md`.

## Automatizacion programada

- **Skill**: crear `/cross-client-intel` (pendiente) que ejecute el pull + parser + reporte.
- **GH Actions**: workflow semanal (domingo 9 AM MX) o cada 3 dias. Envio a email + Drive.
- **Objetivo Japan-proof**: correr sin Gibran, alertar solo si hay decisiones humanas criticas (ads > $300 sin conversion, nuevo naming no compliant).

## Gap crítico descubierto — GR

GR usa `GR-AD-NNN_PRODUCTO` sin formato. Parser cross-client cae todo en `PRODUCT_FOCUS`. Plan migracion en `NAMING_CONVENTION_ADS.md`. Deadline 2026-05-01.

## Siguientes pulls — señales a vigilar

1. LUPITA al escalar: si ROAS cae <5 con 3x budget, es outlier low-budget.
2. HC-OFFER sostiene con $150/dia × 7d: ROAS 27 en $33 puede ser suerte.
3. GR replica OFFER: debe rendir >ROAS 2 en 14d para validar taxonomia.
4. HC sin conversiones (1 en 14d): revisar si es creative o fricción en funnel.

## Por que importa

Sin cross-client, cada cliente reinventa la rueda. LF descubrio UGC_PERSONA ROAS 16 mientras HC quemaba $1K en CAROUSEL. Este ejercicio identifico $2K ahorrables/semana + 2 recetas replicables. Repetir minimo quincenal pre-Japan.
