---
name: hc-meta-ads-analyzer
description: >
  Monitorea la campana Meta Ads de HEALTHY CHUCHOS (HC-VENTAS-MES1), descarga
  metricas cada corrida via Meta Marketing API v21.0, evalua reglas de
  optimizacion editables (rules.json) y ejecuta acciones automaticas (pausar
  ads con CPA alto, kill frequency, scale winners). Cada corrida escribe al
  Google Sheet "HC- META ADS -SPEKGEN DASHBOARD" (tabs CURRENT, HISTORY,
  DECISIONS, RULES, CONFIG, DASHBOARD) y envia email resumen a Gibran.
  Soporta DRY_RUN (default) para validar reglas antes de ejecutar cambios.
  Activar cuando: "corre el monitor de HC meta ads", "analiza ads de HC",
  "que esta pasando con los ads de HC", "aplica las reglas a HC meta ads",
  "pausa los ads de HC que no estan convirtiendo", "saca reporte de HC ads",
  "actualiza el dashboard de HC".
---

# hc-meta-ads-analyzer

Skill para monitorear y auto-optimizar la campana Meta Ads de HEALTHY CHUCHOS
(HC-VENTAS-MES1). Corre end-to-end: fetch → rules → execute → sheet → email.

## Cuando Invocar

Cuando Gibran pida cualquiera de:

1. **Ver estado de ads HC**: "que tal van los ads de HC", "saca snapshot"
2. **Correr monitor**: "corre el monitor", "analiza ads", "ejecuta reglas"
3. **Aplicar acciones**: "pausa los que no convierten", "ejecuta las reglas en vivo"
4. **Actualizar dashboard**: "actualiza el sheet de HC ads"
5. **Ver/editar reglas**: "que reglas tiene el monitor", "cambia el CPA max a X"
6. **Ver historial**: "historial de decisiones del monitor"

## Archivos y Rutas

Todo el codigo y datos del monitor vive en:
```
HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/
├── scripts/
│   ├── orchestrator.py     ← entry point
│   ├── meta_fetch.py       ← pull insights via Meta API
│   ├── rules_engine.py     ← evalua reglas contra metricas
│   ├── meta_actions.py     ← ejecuta PAUSE_AD / INCREASE_BUDGET / etc.
│   ├── sheets_io.py        ← escribe al Google Sheet
│   └── notifier.py         ← email resumen via Gmail SMTP
├── config/
│   ├── rules.json                        ← reglas editables
│   └── spekgen_service_account.json      ← credenciales GCP (NUNCA commit)
├── logs/
│   ├── last_run.json                     ← run log mas reciente
│   ├── last_snapshot.json                ← snapshot mas reciente
│   └── run_YYYYMMDD_HHMM.json            ← historial
└── README.md
```

Google Sheet: `HC- META ADS -SPEKGEN DASHBOARD` — 6 tabs (CURRENT / HISTORY /
DECISIONS / RULES / CONFIG / DASHBOARD). El sheet_id vive en `.env` de HC como
`HC_META_DASHBOARD_SHEET_ID`.

## Comandos

### 1) Correr el monitor (DRY_RUN, safe)

```bash
cd "HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/scripts"
python3 -W ignore orchestrator.py
```

Esto fetches metricas ultimos 7 dias, evalua reglas, **NO** aplica cambios en
Meta (dry_run), escribe al Sheet, manda email.

### 2) Correr en modo LIVE (ejecuta cambios)

Antes de esto: verifica al menos 2 corridas en dry_run sin decisiones erroneas.

```bash
python3 -W ignore orchestrator.py --execute
```

Tambien poner `global.dry_run: false` en `config/rules.json` para activar LIVE
por default (cron).

### 3) Inicializar/repoblar Google Sheet (tabs + headers)

Primera vez (o si Gibran crea un sheet nuevo):

1. Gibran abre https://sheets.new → renombra a `HC- META ADS -SPEKGEN DASHBOARD`
2. Comparte con `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` como **Editor**
3. Agrega a `HC - HEALTHY CHUCHOS/.env`:
   ```
   HC_META_DASHBOARD_SHEET_ID=<ID del sheet>
   GOOGLE_APPLICATION_CREDENTIALS=/Users/.../04. MONITORING/config/spekgen_service_account.json
   ```
4. Correr una vez con `--init-sheet`:
   ```bash
   python3 -W ignore orchestrator.py --init-sheet
   ```

### 4) Ver reglas actuales

```bash
cat "HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/config/rules.json"
```

Claude puede editar directamente ese JSON. Las reglas se refrescan en el tab
RULES del Google Sheet en la siguiente corrida.

### 5) Ver ultimo run

```bash
cat "HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/logs/last_run.json"
```

## Regla de Oro — SAFETY

1. **SIEMPRE dry_run primero** cuando Gibran cambia reglas o umbrales nuevos.
2. **Nunca ejecutar LIVE** sin confirmar con Gibran la 1era vez.
3. **Kill switch campaign** es el ultimo recurso — si se dispara, pausar
   TODA la campana y notificar a Gibran inmediatamente.
4. **Min spend $50 MXN** antes de tomar decisiones (evita falsas alarmas por
   ads recien lanzados).

## Reglas actuales (resumen — ver rules.json para detalle)

| Rule | Accion | Condicion |
|---|---|---|
| `kill_ad` | PAUSE_AD | spend≥$150 AND purchases=0 AND CTR<0.6% |
| `kill_ad_hard` | PAUSE_AD | spend≥$300 AND purchases=0 |
| `kill_frequency` | PAUSE_AD | freq≥3.0 AND CTR<1.0% |
| `scale_winner` | INCREASE_BUDGET_PCT +20% (max $300/dia) | purchases≥3 AND ROAS≥2.5 AND CPA≤$150 — **disabled by default** |
| `warn_underperformer` | NOTIFY_ONLY | spend≥$100 AND CTR<0.8% |
| `kill_switch_campaign` | PAUSE_CAMPAIGN | campaign spend≥$1500 AND purchases=0 |

## IDs Clave (HC)

| Asset | Value |
|---|---|
| Campaign | `HC-VENTAS-MES1` — ID en `.env` → `META_CAMPAIGN_ID` |
| Ad Set | `HC-BROAD-MX-PURCHASE` — ID en `.env` → `META_ADSET_ID` |
| Ad Account | `act_1626923298353925` |
| Pixel | `1813096612719811` |
| Budget | `$120 MXN/dia` a nivel ad set |

## Troubleshooting

### "GOOGLE_APPLICATION_CREDENTIALS no set"
Agregar al `.env` de HC:
```
GOOGLE_APPLICATION_CREDENTIALS=/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 1/04. MONITORING/config/spekgen_service_account.json
```

### "HC_META_DASHBOARD_SHEET_ID no set"
Gibran debe crear el sheet manualmente, compartirlo, y pegar el ID en `.env`.

### "The caller does not have permission" al escribir al sheet
El service account no esta compartido como Editor. Agregar
`spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` al sheet.

### "Meta API HTTP 190" o similar
Token expirado. Renovar `META_TOKEN` en HC/.env (mismo token unificado SPEKGEN).

### Reglas disparan demasiadas decisiones en DRY_RUN
Revisa `global.min_spend_for_decision_mxn` y los thresholds. El `min_spend`
protege ads recien lanzados.

## Flow End-to-End

```
┌─────────────────┐   ┌───────────────┐   ┌─────────────────┐
│ 1. meta_fetch   │──>│ 2. rules_eng  │──>│ 3. meta_actions │
│   /insights     │   │   evalua      │   │   PAUSE/INCR    │
└─────────────────┘   └───────────────┘   └─────────────────┘
         │                    │                    │
         v                    v                    v
┌────────────────────────────────────────────────────────────┐
│ 4. sheets_io → Google Sheet "HC- META ADS -SPEKGEN DASH..."│
│    Tabs: CURRENT | HISTORY | DECISIONS | RULES | CONFIG    │
└────────────────────────────────────────────────────────────┘
         │
         v
┌─────────────────┐      ┌────────────────────────────────┐
│ 5. notifier     │─────>│ Email a gibran.alonzo0506@...  │
│   HTML summary  │      │ Subject: [DRY_RUN|LIVE] HC...  │
└─────────────────┘      └────────────────────────────────┘
         │
         v
┌─────────────────┐
│ 6. run_log      │
│   logs/*.json   │
└─────────────────┘
```

## Notas

- **Autonomia**: Este skill esta disenado para correr sin Gibran. La cron
  scheduled la configura `/schedule` o GitHub Actions con `orchestrator.py --execute`.
- **Frequencia**: Cada 2 dias a las 9 AM Mexico City.
- **Observabilidad**: El tab DASHBOARD y el email de resumen son la unica forma
  de supervisar mientras Gibran esta en Japon.
- **Extensibilidad**: Para agregar mas clientes (GR, MG, LF), copiar la carpeta
  `04. MONITORING/` al cliente y ajustar campaign_id en rules.json.
