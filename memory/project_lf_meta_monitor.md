# LF Meta Monitor

**Creado:** 2026-04-17
**Carpeta:** `LF - LO FITNESS/LF - 05. META ADS/04. MONITORING/`
**Codigo:** `g-bran/Spekgen-ops/scripts/meta-monitor/` (compartido con HC/GR, `--client lf`)
**Workflow:** `.github/workflows/lf-meta-monitor.yml`
**Cron:** dias pares 9:07 AM MX (15:07 UTC). Alterna con HC/GR (dias impares).

## Campana target

- **Nombre:** LF-VENTAS-ABR26
- **Campaign ID:** `120243602635060731`
- **Ad account:** `act_542994632175434`
- **Adsets activos:** LF_METAFIT_BROAD, LF_FITMAX_BROAD, LF_KIT_TRIO_BROAD (CBO)
- **15 ads activos** al 2026-04-17

## Reglas (CPA max = price - $150 por ad)

- **METAFIT** ($498 -> $348)
- **METAFIT 2-pack** ($896 -> $746)
- **FITMAX** ($598 -> $448)
- **FITMAX 2-pack** ($1076 -> $926)
- **KIT** ($1299 -> $1149)

Acciones: kill_ad_soft, kill_ad_hard, kill_high_cpa, kill_frequency, warn_underperformer, kill_switch_campaign. Scale disabled por default.

## Modo

- **DRY_RUN** hasta 2026-04-22 (primeros 5 dias). Registra decisiones en tab DECISIONS del sheet pero no pausa nada.
- Flip a LIVE: editar `rules/lf.json` -> `global.dry_run: false`, commit+push.

## Google Sheet

- **Nombre:** `LF_Meta_Monitor_Dashboard`
- **Doc ID:** PENDIENTE — Gibran tiene que crearlo en https://sheets.new y compartirlo con `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` como Editor. Luego correr `bootstrap_sheet.py <ID>` para inicializar tabs.
- **Tabs:** CURRENT, HISTORY, DECISIONS, RULES, CONFIG, DASHBOARD.

## Pendientes para activacion

1. [ ] Gibran crea el sheet + comparte con SA
2. [ ] Correr `scripts/bootstrap_sheet.py <SHEET_ID>` para inicializar tabs
3. [ ] Commit + push en `g-bran/Spekgen-ops`: workflow `lf-meta-monitor.yml` + `rules/lf.json`
4. [ ] Agregar GitHub Secrets: `META_TOKEN_LF`, `META_AD_ACCOUNT_LF`, `LF_CAMPAIGN_ID`, `LF_DASHBOARD_SHEET_ID`, `LF_ALERT_EMAIL`, `GOOGLE_SERVICE_ACCOUNT_JSON`
5. [ ] Trigger manual desde GH Actions con `init_sheet=true, execute=false`
6. [ ] Validar que las decisiones del tab DECISIONS serian correctas los primeros 5 dias
7. [ ] Flip a LIVE: `dry_run: false` en rules/lf.json, push

## Test local

```bash
cd "LF - LO FITNESS/LF - 05. META ADS/04. MONITORING/scripts"
./run_local.sh --skip-sheet --skip-email  # smoke test
./run_local.sh                            # full local run (requiere sheet_id)
```

Primer smoke test 2026-04-17: 15 ads, spend $3,478 MXN, 6 compras, 0 decisions generadas. Pipeline funcional.

## Notas

- Meta token LF es DIFERENTE al de HC/GR (token unificado SPEKGEN Agency). Por eso secret se llama `META_TOKEN_LF`.
- `META_CAMPAIGN_ID` en LF/.env apunta a una campana vieja (`120241746786300731` PH DETOX MAR26, pausada). El monitor usa la campana ABR26 hard-coded en `run_local.sh` y en el secret `LF_CAMPAIGN_ID` del workflow.
- Ads metadata en `rules/lf.json -> ad_metadata`. Para agregar nuevos ads, seguir el patron (ver README de la carpeta).
