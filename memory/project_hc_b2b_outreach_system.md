# HC B2B Outreach System (Japan-proof, 2026-04-27)

Sistema completo de cold outreach B2B para Healthy Chuchos, **100% autónomo en GH Actions**, escribe a Google Sheets `HC_OUTREACH_MASTER`.

## Sheet — fuente de verdad

- **Doc ID:** `15_SC6wZqA9gXttw59PI7gzy2BnKO6pv9HYbJfspwBLo`
- **Pointer local:** `HC - 17. OUTREACH/HC_OUTREACH_MASTER.gsheet`
- **Service account:** `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com` (Editor)
- **Tabs:** `PROSPECTS_B2B`, `PROSPECTS_D2C`, `SEND_LOG`, `REPLIES_LOG`, `STATE`
- **Schema PROSPECTS_B2B (18 cols):** id, email, first_name, last_name, company, city, phone, segment, signal, dog_breed, dog_age, status, current_step, first_sent_date, last_sent_date, reply_notes, source, added_date

## 3 Workflows en `g-bran/Spekgen-ops` `.github/workflows/`

| Workflow | Cron | Función |
|---|---|---|
| `hc-outreach-batch.yml` | L-V 10 AM MX (16:00 UTC) | Sender — manda step N pendiente, max 25/día, delays 45-120s |
| `hc-outreach-reply-monitor.yml` | Cada 15 min | IMAP poll Gmail, marca status=replied, alerta a Gibran |
| `hc-outreach-scraper.yml` | Lunes 9 AM MX (15:00 UTC) | Scrape Google Maps, rota presets w16/w17/w18/w19 por ISO week |

## Scripts en `Spekgen-ops/scripts/hc-outreach/`

- `sender.py` — batch sender, lee PROSPECTS_*, manda emails con cadencia 1:0/2:3/3:6/4:9/5:12 días
- `reply_monitor.py` — IMAP poll cursor `last_imap_uid` en STATE
- `gmaps_scraper.py` — scraper Sheets-native (deployed 2026-04-27, reemplaza viejo `hc_gmaps_scraper.py`)
- `sheets_backend.py` — capa CRUD compartida (auth SA, read_tab, append_row, update_prospect_row, find_prospect_by_email)
- `migrate.py` — one-time xlsx→Sheets

## Secrets en GH (configurados)

`HC_GMAIL_USER`, `HC_GMAIL_APP_PASSWORD`, `HC_SA_JSON_B64`, `HC_OUTREACH_SHEET_ID`, `HC_NOTIFY_EMAIL`, `SPEKGEN_GMAIL_SENDER`, `SPEKGEN_GMAIL_APP_PASSWORD`, `REPORT_RECIPIENT`

## Cadencia secuencia B2B (5 steps)

```
DAYS_BETWEEN_STEPS = {1:0, 2:3, 3:6, 4:9, 5:12}
```
Sender solo avanza UN step por corrida. Templates en `outreach_templates/b2b/step_{N}.html` + `subjects.json`.

## Estado de prospects (status válidos)

- **Activos**: `new` (o vacío) → step 1 | `sent` → avanza si días cumplen
- **Terminales (skip)**: `replied`, `bounced`, `unsubscribed`, `opted_out`, `won`, `blocked`
- **Sin email**: `no_email` (no es terminal pero email vacío bloquea envío)

## Bug fixes aplicados al scraper (2026-04-27)

1. `extract_emails_from_website()` — paths probados de 3 → 7 (incluía aviso-de-privacidad, /legal). Ver memoria scraper viejo `hc_gmaps_scraper.py`
2. `_retry()` helper exponential backoff para SSL/timeout/5xx en Google API calls (causó crash run 25026786755)
3. State precomputado en `run()` y pasado a `write_leads_to_sheet()` — antes lo re-leía y duplicaba API calls
4. Per-lead append wrapped en try/except — un fail no aborta el batch entero

## Proceso semanal autónomo

**Lunes 9 AM**: scraper escribe ~30-100 leads nuevos al Sheet (algunos con email, otros `no_email`)
**Lunes-Viernes 10 AM**: sender manda step 1 a los nuevos con email + avanza secuencia de los `sent` que cumplen días
**Cada 15 min**: reply_monitor marca replies → status=`replied` → alerta a `gibran.alonzo0506@gmail.com`
**Falla cualquiera**: notify-on-failure manda email desde `spekgen.ai@gmail.com`

## Apify enrichment (pendiente — bloqueado hasta ~24 mayo)

- Cuenta `quenchless_nomad` exhausted ($5 free/mes hard limit)
- Script `HC - 17. OUTREACH/scripts/enrich_b2b_with_facebook.py` listo para correr al reset
- 67 leads `no_email` en lista de espera. Cuando reset llegue: actor `apify/facebook-pages-scraper` (~$0.05 USD total) recupera ~50 emails vía FB Pages
- Alternativa pre-Japón: pivote a campaña WhatsApp con esos 67 (todos tienen `phone`, bot HC ya LIVE)

## Estado al 2026-04-27 (post-deploy)

- 18 prospects originales completaron secuencia (step 5 enviado hoy 11:13 AM, 0 errores)
- 4 leads enriched manualmente (B2B-0018 MADIVET, 0023 GrandPET, 0056 VETME, 0062 Shuncu Vet) reciben step 1 mañana 28-abr
- Scraper deployed + dry-run validado + run real con fix corriendo
- Pipeline empieza a llenarse automáticamente desde lunes 4-mayo (próximo cron real cae 5-mayo lunes)

## Cómo accionar reply caliente (durante Japón)

1. Reply monitor detecta → email automático a `gibran.alonzo0506@gmail.com`
2. Email contiene: prospect_id, company, snippet de la respuesta
3. Responder desde teléfono al hilo Gmail original (firma HC manual)
4. Lead avanza orgánico, status queda `replied` (sender no le manda más)

## Comandos útiles (local)

```bash
# Trigger scraper manualmente
gh workflow run hc-outreach-scraper.yml -f dry_run=false -f preset=auto -f limit=25 -R g-bran/Spekgen-ops

# Ver últimas runs
gh run list -w hc-outreach-batch.yml --limit 10 -R g-bran/Spekgen-ops

# Ver log de un run específico
gh run view <RUN_ID> --log -R g-bran/Spekgen-ops
```
