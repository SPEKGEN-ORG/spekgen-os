---
name: HC Cloud Monitors — Meta Ads + Analytics (GA4 + Clarity)
description: Dos monitores auto-piloto para HC. Meta Ads Monitor via GitHub Actions (dias impares). Analytics Monitor (GA4+Clarity) via Claude Code Cloud Trigger (dias pares). Sheet compartido. Japan-proof.
type: project
originSessionId: 4b56d2c7-a077-4bf5-bfb2-333ae7dac9ba
---
## Sistema

Monitor end-to-end para campana HC-VENTAS-MES1 de HEALTHY CHUCHOS. Corre cada 2 dias, fetches metricas via Meta API v21.0, evalua reglas editables, ejecuta acciones (PAUSE/SCALE), escribe a Google Sheet, manda email resumen.

**Ubicacion codigo**: `HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/`
**Skill**: `/hc-meta-ads-analyzer` (global, en `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/`)
**Google Sheet**: `HC- META ADS -SPEKGEN DASHBOARD` ID `1LbL48DlaUfoo6-dJ2EK51CKFaTSsi-f2mqhbikEs3CI`
**Service account**: `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com`
**Sender email**: `spekgen.ai@gmail.com` (NO gibran.alonzo0506 — esa no tiene app password)
**Alert email**: `gibran.alonzo0506@gmail.com`

## Cron activo

Launchd plist: `com.spekgen.hc.meta-monitor` en `~/Library/LaunchAgents/`
- Corre dias impares del mes a las 9:07 AM MX (1,3,5,7,9,11,13,15,17,19,21,23,25,27,29)
- Modo: DRY_RUN por default — switch a `--execute` cuando se valide por 2 corridas
- Log: `04. MONITORING/logs/launchd_*.log` + `cron_*.log`
- **LIMITACION CRITICA**: requiere Mac encendida — NO funciona en Japon

**Why**: Gibran necesita auto-optimizacion de ads sin babysitting. Reemplaza el xlsx `SPEKGEN_CLIENTS_AD_LOG_v2.0.xlsx` que nunca se mantenia.

**How to apply**: Cuando Gibran pida "corre el monitor de HC ads", invocar skill. Cuando cambien thresholds (CPA, ROAS, freq), editar `config/rules.json` directamente — la siguiente corrida refresca el tab RULES del sheet automaticamente. Modo LIVE via flag `--execute` OR `global.dry_run: false` en rules.json.

## Reglas actuales

| Rule | Accion | Trigger |
|---|---|---|
| kill_ad | PAUSE_AD | spend≥150 AND purchases=0 AND CTR<0.6% |
| kill_ad_hard | PAUSE_AD | spend≥300 AND purchases=0 |
| kill_frequency | PAUSE_AD | freq≥3 AND CTR<1% |
| scale_winner | INCREASE_BUDGET +20% (cap $300/dia) | purchases≥3 AND ROAS≥2.5 AND CPA≤$150 — **DISABLED** |
| warn_underperformer | NOTIFY_ONLY | spend≥100 AND CTR<0.8% |
| kill_switch_campaign | PAUSE_CAMPAIGN | campaign spend≥1500 AND purchases=0 |

Min spend por ad para aplicar reglas: $50 MXN (protege ads recien lanzados).

## Cloud version — GitHub Actions (ACTIVA, validada 2026-04-10)

**Status**: Workflow `.github/workflows/hc-meta-monitor.yml` en `g-bran/Spekgen-ops` (commit c33bc45). Primer run exitoso: ID 24257874723 — 9 ads fetched, 0 decisions (esperado, campaña sin spend), Google Sheet actualizado, email via webhook entregado OK. **~15 segundos end-to-end en ubuntu-latest.**

**Why GitHub Actions y NO Claude Code Cloud RemoteTrigger**: El sandbox de Claude Code Cloud (env `claude-code-default`) bloquea requests salientes a `graph.facebook.com` con `HTTP 403: Blocked by egress policy`. El monitor no puede fetchear metricas de Meta API desde ahi. SkyDropx funciona porque habla con SkyDropx API + Make webhook (allowlisted). El plan original del RemoteTrigger (ver `cloud/CLOUD_TRIGGER_PROMPT.md`, ahora obsoleto) se descarto. GitHub Actions runners no tienen esa restriccion + tienen secret management nativo + logs persistentes 90 dias + GitHub mobile app para monitoreo.

**Schedule**: `cron: "7 15 1-31/2 * *"` = dias impares del mes 15:07 UTC = 9:07 AM MX (UTC-6 year-round). Mismo que launchd. Tambien `workflow_dispatch` con inputs `date_preset` (last_3d/7d/14d/30d) y `execute` (bool) para trigger manual.

**Secrets del repo** (configurados via `gh secret set NAME -R g-bran/Spekgen-ops` leyendo de stdin):
- META_TOKEN, META_AD_ACCOUNT, META_CAMPAIGN_ID
- HC_META_DASHBOARD_SHEET_ID, HC_SA_JSON_B64 (base64 del SA JSON)
- MAKE_WEBHOOK_URL, HC_ALERT_EMAIL

**Gotcha descubierto setteando secrets**: `gh secret set NAME -b-` NO lee de stdin — interpreta `-b-` como `--body=-` y guarda el literal `-`. Para stdin: **NO uses `-b` para nada**, solo pipea:
```bash
printf "%s" "$VALUE" | gh secret set NAME -R repo
```
(Documentacion: "reads from standard input if not specified".)

**Trigger manual desde local**:
```bash
# DRY_RUN default
gh workflow run hc-meta-monitor.yml -R g-bran/Spekgen-ops --ref main

# LIVE con ventana custom
gh workflow run hc-meta-monitor.yml -R g-bran/Spekgen-ops --ref main \
  -f date_preset=last_14d -f execute=true

# Ver runs
gh run list -R g-bran/Spekgen-ops --workflow hc-meta-monitor.yml --limit 5
gh run view <RUN_ID> -R g-bran/Spekgen-ops --log
```

**Editar reglas**: editar `scripts/hc-meta-monitor/rules.json` en el repo + commit + push. Proxima corrida usa las reglas nuevas sin re-deploy.

**Adaptaciones cloud vs local** (scripts en `scripts/hc-meta-monitor/` commit 4f3ef2c):
1. `monitor.py` reemplaza `orchestrator.py` — lee de `os.environ` solamente
2. `HC_SA_JSON_B64` decoded a `/tmp/hc_sa.json` en runtime + chmod 600 + unlink al final
3. `notifier.py` prefiere Make webhook si `MAKE_WEBHOOK_URL` set (payload `{to, subject, html_body}`)
4. Sin escritura a disco — solo stdout logs (GitHub Actions captura)
5. `meta_fetch.py` — removida `load_env()` y hardcoded path en `__main__`

**Workflow file path en repo**: `.github/workflows/hc-meta-monitor.yml` (68 lineas, Python 3.11, ubuntu-latest, timeout 10 min).

**Dual run transicion**: Launchd local sigue corriendo como backup hasta validar 2-3 runs exitosos del GitHub Actions workflow. Post-validacion, disable con:
```bash
launchctl unload ~/Library/LaunchAgents/com.spekgen.hc.meta-monitor.plist
```

**Archivos obsoletos** (no borrar, son historial): `cloud/CLOUD_TRIGGER_PROMPT.md` referencia el plan RemoteTrigger descartado. El directorio `cloud/scripts/hc-meta-monitor/` es un staging area — los archivos *reales* en produccion viven en `g-bran/Spekgen-ops` repo.

## Arquitectura

```
meta_fetch.py (urllib → Meta API v21.0)
    ↓
rules_engine.py (AND-logic + Template reasons + min_spend guard)
    ↓
meta_actions.py (PAUSE/INCREASE_BUDGET via urllib POST)
    ↓
sheets_io.py (6 tabs idempotent: CURRENT/HISTORY/DECISIONS/RULES/CONFIG/DASHBOARD)
    ↓
notifier.py (Gmail SMTP SSL 465, sender=spekgen.ai@gmail.com)
    ↓
logs/ (run_*.json + snapshot_*.json + last_run.json)
```

Orchestrator CLI: `--execute`, `--init-sheet`, `--date-preset last_3d|last_7d|last_14d|last_30d`, `--skip-email`, `--skip-sheet`.

## Analytics Monitor (GA4 + Clarity) — ACTIVO 2026-04-14

**Cloud Trigger**: `trig_01HfBBnHxi4SabUEJuXoLu9G` en `claude.ai/code/scheduled`
**Schedule**: `7 9 2-30/2 * *` = días pares 9:07 AM MX — intercala con Meta Monitor
**Scripts**: `scripts/hc-analytics-monitor/` en `g-bran/Spekgen-ops`
**Sheet**: mismo `1LbL48DlaUfoo6-dJ2EK51CKFaTSsi-f2mqhbikEs3CI` — tabs: GA4_Overview, GA4_History, GA4_Pages, GA4_Sources, Clarity_Overview, Clarity_History, Clarity_Pages
**Datos primer run** (2026-04-14, últimos 7d): 122 sesiones · 4 ATC · 1 compra · $381 MXN · conv 0.82%
**GA4 Property ID**: `529120588` — SA Viewer confirmado 2026-04-13
**Clarity Project ID**: `vy5jjgw9yi` — API key en HC `.env` como `CLARITY_API_KEY`

**Skill de replicación**: `/analytics-monitor-setup` — guía completa para GR y LF
**Replicación**: `ga4_fetch.py` refactorizado — `GA4_PROPERTY_ID` y `GA4_PRODUCT_SLUGS` desde env vars (defaults HC). Para GR: property `470503075`, para LF: `484501054`.

**Gotchas Analytics Monitor**:
- `analyticsdata.googleapis.com` debe habilitarse manualmente en GCP project `828252285603` (ya hecho 2026-04-14)
- Clarity overview endpoint sin `groupBy` puede devolver sessions=0 para algunos proyectos — `clarity_fetch.py` tiene fallback via `groupBy=url`
- Clarity tiene límite diario de llamadas API — 1 llamada/día en cron es fine; tests múltiples agotan la cuota
- SA fallback local: acepta `GOOGLE_APPLICATION_CREDENTIALS` (path al JSON) además de `HC_SA_JSON_B64`

## Gotchas documentadas

1. **Service accounts NO pueden crear spreadsheets** (0 Drive storage quota). Sheet debe crearse manualmente y compartirse con el SA como Editor.
2. **Python 3.9 compatibility**: usar `Optional[str]` no `str | None`.
3. **Gmail SMTP sender**: `spekgen.ai@gmail.com` + `SPEKGEN_GMAIL_APP_PASSWORD` (agency .env). NO usar `gibran.alonzo0506@gmail.com` como sender.
4. **SMTP bloqueado en Claude Code cloud**: puerto 465 bloqueado. Para cloud usar Make.com webhook como proxy.
5. **Token Meta**: unificado SPEKGEN Agency API (21+1 permisos, sin caducidad). Mismo para GR, HC, Gibran Ecom.
