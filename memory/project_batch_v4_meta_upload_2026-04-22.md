# project: BATCH_CROSS_2026-04-21-v4 — Upload 10 ads a Meta (2026-04-22)

10 ads ACTIVE en Meta tras validación + organización de finales. 5 ads `-P` pendientes de corrección.

## Destinos finales

| Cliente | Ads | Adset | Adset ID | Campaña |
|---|---|---|---|---|
| GR (6) | 019, 019C, 020, 020C, 021, 021C | **GR_LINEAS_MX_25-65** (nuevo, CBO) | `23855538375090796` | GR_CONV_PRODUCTS_ABR26 (`23855052698520796`) |
| HC (3) | 019, 020, 021 | HC-BROAD-MX-PURCHASE | `6899759030034` | HC-VENTAS-MES1 (`6899758932234`) |
| LF (1) | 062 | LF_METAFIT_BROAD_MX_30-55 | `120243602938040731` | LF-VENTAS-ABR26 (`120243602635060731`) |

## Ad IDs (todos ACTIVE 2026-04-22)

- GR-AD-019 `23855538972080796` → `/collections/hormonal`
- GR-AD-019C `23855539022060796` → `/collections/hormonal`
- GR-AD-020 `23855539076470796` → `/collections/digestivos`
- GR-AD-020C `23855539114150796` → `/collections/digestivos`
- GR-AD-021 `23855539264280796` → `/pages/proteicos`
- GR-AD-021C `23855539291000796` → `/pages/proteicos`
- HC-AD-019 `6917051943034` → `/products/artridog`
- HC-AD-020 `6917052014634` → `/products/artridog`
- HC-AD-021 `6917052139034` → `/products/artridog`
- LF-AD-062 `120244060003660731` → `/products/metafit`

## GR adset nuevo

`GR_LINEAS_MX_25-65`:
- Geo: MX, age 25-65, Advantage+ audience
- Pixel `1694343195291445`, PURCHASE event
- CBO (sin daily_budget propio — hereda $180/día de la campaña)
- Status ACTIVE
- Razón: los 3 adsets existentes (HERO_PROTOCOLO_BELLSAN_HORMO, DYNAMIC_GXAMIN, DYNAMIC_COLFIT_GXAMIN) son product-specific para SKUs distintos. Los 6 ads nuevos apuntan a 3 líneas (hormonal/gastro/proteicos), Gibran pidió 1 solo adset consolidado.

## Pendientes `-P`

5 ads no subidos, en sus respectivos `RESOURCES/{ad_code}-P/FINAL/`:
- GR-AD-019B-P (Pack 40+ $990 fake → real $799/$875)
- GR-AD-020B-P (Sistema digestivo $1,280 fake)
- GR-AD-021B-P (Trio shakes $999 fake)
- LF-AD-063-P (FitMax testimonial — revisión)
- LF-AD-064-P (Kit $699 fake → real $1,077/$1,267)

## Copy pre-upload `_COPY_*.md`

**NO creados.** Gibran declinó. Copy vive solo en `ads_batch.json` del factory. Convención de CLAUDE.md sugiere guardar también `_COPY_*.md` en `{CLIENTE}/05. META ADS/` — pendiente para el futuro si surge auditoría.

## Decisión arquitectural

Ads logs se mantienen SEPARADOS por cliente (no centralizar). Cross-client view vive en `/cross-client-intel` PDF cada 3 días, no en los dashboards operativos. Gibran declinó la propuesta de 4ª sheet `SPEKGEN_AGENCY_OVERVIEW` (IMPORTRANGE read-only).

## Scripts usados

- `/tmp/create_gr_adset.py` — crea adset nuevo via `meta_helpers.create_adset` + `build_advantage_targeting`
- `/tmp/upload_batch_v4.py` — parsea `ads_batch.json`, sube imagen + crea creative (static) + crea ad en adset + verifica IG/UTMs para cada uno de los 10
- `/tmp/activate_batch_v4.py` — POST `status=ACTIVE` al árbol completo (campaña GR + adset GR + 10 ads)

Log: `SPK - SPEKGEN AGENCY/SPK - 15. FACTORY/ads/BATCH_CROSS_2026-04-21-v4/_upload_log_2026-04-22_0912.json`

## Monitoreo

- HC+GR dashboards: mañana 23 abril 9:07 AM MX (monitor GH Actions día impar)
- LF: próximo 24 abril (día par) — dashboard sheet aún pendiente crear
- Cross-client intel PDF: próxima corrida cada-3-días
