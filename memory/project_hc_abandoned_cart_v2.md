# HC Abandoned Cart Flow V2 — Production-grade LIVE 2026-05-02

## Arquitectura final

```
Shopify HC (healthychuchos.com)
   ↓ webhook checkouts/update (hook 2208273)
Make Scenario A · Recorder (4845894)
   ├─ GetRecord guard: skip si existing.status IN [converted, completed, recovered]
   ├─ AddRecord con key cascade {{ifempty(1.token; ifempty(1.cart_token; 1.id))}}
   ├─ Filter: skip si email empty
   └─ overwrite: true
       ↓
Make Datastore 94470 (data store)
       ↓
Make Scenario B · Scheduler (4845938) — cron 15min
   ├─ SearchRecord: status=active AND last_step_sent<6, limit 500
   ├─ SetVariables: age_hours = (now - created_at) / 3600000
   └─ BasicRouter con 6 ramas M1-M6:
       ├─ M1 (15min-24h, last<1)
       ├─ M2 (24-36h, last<2, has_artridog=true)
       ├─ M3 (36-52h, last<3)
       ├─ M4 (52-72h, last<4, has_artridog=true)
       ├─ M5 (72-168h, last<5, total≥1000)
       └─ M6 (168h+, last<6) → status=completed
   Each rama: HTTP POST a Edge Function + UpdateRecord last_step_sent
       ↓
Supabase Edge Function `hc-abandoned-mailer` (project wjlwpfaogjpeqgyxxnwa)
   ├─ Auth: header x-spk-secret = "spk-hc-abandoned-2026"
   ├─ Fetch HTML template from CDN (TextDecoder UTF-8 forced)
   ├─ Render Liquid placeholders ({{customer.first_name}}, {{checkout.abandoned_checkout_url}})
   ├─ Inject <meta charset="utf-8"> if missing
   └─ POST a Resend API
       ↓
Resend (sender noreply@healthychuchos.com, reply-to hola@healthychuchos.com)
       ↓ Email al cliente
       ↓
Shopify webhook orders/create (hook 2208274)
   ↓
Make Scenario C · Converter (4845946) — marca status=converted
```

## Templates (6 mails)

CDN: `https://wjlwpfaogjpeqgyxxnwa.supabase.co/storage/v1/object/public/post-media/hc-abandoned-cart/`
Local: `HC - HEALTHY CHUCHOS/HC - CLIENT FLOWS/SHOPIFY MAILS/ABANDONED CART/03_DESIGNS/FINAL/`

| Mail | Trigger | Subject |
|---|---|---|
| M1 | 15min-24h | Olvidaste algo para tu chucho 🐾 |
| M2 | 24-36h, has_artridog | Por qué ArtriDog se agota tan rápido |
| M3 | 36-52h | Tu carrito tiene un descuento activo |
| M4 | 52-72h, has_artridog | "En 3 semanas volvió a saltar al sillón" |
| M5 | 72-168h, total≥$1K | PATITA10 — 10% extra, 48h |
| M6 | 168h+ | Última oportunidad antes de cerrar tu carrito |

## Reglas críticas

- **Código descuento real es PATITA10** (NO CHUCHO10). 10% off, prereq ≥$1,000, once/customer.
- **WhatsApp HC: `+52 33 2640 2219`** en M1, M3, M6.
- **Sender:** Resend con domain healthychuchos.com (verificar DKIM/SPF en panel).
- **NO usar Klaviyo ni GHL workflow legacy** "Carrito Abandonado Shopify" v30 — sigue published pero pendiente pausar.

## SOP cuando se modifica Make scenario con cron

Después de TODO `scenarios_update` al Scheduler 4845938 o Recorder 4845894:
1. Backup blueprint a `_BACKUPS/`
2. Apply scenarios_update
3. **`scenarios_deactivate` + `scenarios_activate`** ← evita nextExec stale
4. `scenarios_run` manual para validar
5. `executions_list` para ver que corrió OK

## Dashboard local

Path: `HC - HEALTHY CHUCHOS/HC - CLIENT FLOWS/SHOPIFY MAILS/ABANDONED CART/04_IMPLEMENTATION/dashboard/`
- `fetch_and_render.py` — pull datastore + render kanban HTML
- `dashboard.html` — 8 columnas estilo GHL workflow
- Cron auto via launchd 4h (instalar manual con plist)
- Refresh manual via `refresh.command` doble-click

## Bugs históricos resueltos

1. Encoding triple-UTF8 en CDN — re-uploaded clean
2. Liquid `{% for line_item %}` no rendea en Resend — removido bloque
3. Liquid placeholders no renderean — Edge Function v3 con regex replace
4. WhatsApp wrong number — actualizado
5. Records duplicados (3-6 por abandono) — key cascade + email filter
6. Status overwrite post-conversion — GetRecord guard
7. Scheduler nextExec freeze post-update — deactivate+activate fix

Ver memoria `feedback_make_scenarios_update_freezes_nextexec.md` para SOP detallado.

## Métricas reales (2026-05-02)

- Resend lifetime últimos 30 emails: 30/30 delivered, 0 bounces, 0 complaints
- Datastore: 6 records (4 reales + 2 placeholders), 1 converted (Giselle), 16.7% conversion
- Real abandons este mes: rubigzaldivar, leo0857cgjj, bovdikagrig, Giselle (converted)
