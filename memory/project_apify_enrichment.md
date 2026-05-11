# Apify Enrichment (SPEKGEN Prospects — 2026-04-24)

Reemplazo de Apollo ($50/mo, rechazado) por Apify (~$0.003/lead) para descubrir IG handles + follower counts.

## Cuentas

| Cuenta | Username | Plan | Budget mes | Token env var | Estado |
|--------|----------|------|-----------|----|--------|
| Principal | `gibran_alonzo` | FREE $5/mo | $5.02/$5 consumido | (exhausted) | ciclo reset 2026-05-12 |
| Secundaria | `quenchless_nomad` | FREE $5/mo | exhausted 2026-04-25 | `APIFY_API_TOKEN` (en `SPK - SPEKGEN AGENCY/.env`) | EXHAUSTED — reset ~2026-05-24 |

**2026-04-25:** la cuenta secundaria también se agotó. HTTP 403 `platform-feature-disabled / Monthly usage hard limit exceeded` en TODAS las queries IG search. Bloqueante hasta reset (~1 mes desde activación). Para continuar enrichment: (a) crear 3a cuenta gratis, (b) upgrade a paid, o (c) esperar reset.

Token activo en `.env`: `apify_api_bn5Qt3qW4wF9ttgCCI2i3Hl9UOXboA1swIj6`

## Actor

**`apify/instagram-search-scraper`** (actor id con tilde: `apify~instagram-search-scraper`)
- Input: `{ "search": "business name", "searchType": "user", "resultsLimit": 5 }`
- Output: dataset items con `username`, `fullName`, `followersCount`, `biography`, `verified`, `isBusinessAccount`
- Endpoint: `POST https://api.apify.com/v2/acts/apify~instagram-search-scraper/run-sync-get-dataset-items?token=X&timeout=120`
- Cost: ~$0.003 per call con 5 results

## Input Validator — CRITICAL

El actor tiene regex estricto en `input.search`:
```
^[^!?.,:;\-+=*&%$#@/\~^|<>()[\]{}"'`]+(?:,[^...]+)*$
```

Cualquiera de estos chars → `400 invalid-input`: `! ? . , : ; - + = * & % $ # @ / \ ~ ^ | < > ( ) [ ] { } " ' `` –  —`

**Sanitizer obligatorio antes de enviar** (implementado en `enrich_leads_apify.py` fn `sanitize_query`):
1. Strip all forbidden chars → reemplazar con espacio
2. Drop noise suffixes ("Adults Only", "Boutique")
3. Collapse whitespace
4. Truncate a 60 chars

## Empty Results Handling

El actor NO devuelve `[]` cuando no hay matches — devuelve:
```json
[{"error": "no_items", "errorDescription": "Empty or private data for provided input"}]
```
Filtrar items con `error` key o sin `username`/`fullName` **antes** de scorear, o el matcher asigna score=0 a item vacío.

## Fuzzy Matching

`difflib.SequenceMatcher` ratio entre business name y (fullName OR username), con bonus a substring match. Threshold: **0.55** (ajustable). Arriba del threshold → persist el top-1. Debajo → guardar error `no_match` con top_score + candidate para auditar.

## Uso

```bash
# Dry run (preview, no cost)
python3 enrich_leads_apify.py --dry-run --limit 10

# Real batch de 10 ($0.03)
python3 enrich_leads_apify.py --limit 10

# Re-enrich leads específicos
python3 enrich_leads_apify.py --refresh --lead-ids P-003,P-082

# Mass enrich (~$5.5 total para 1825)
python3 enrich_leads_apify.py --limit 2000
```

Flags: `--dry-run`, `--limit N`, `--lead-ids P-001,P-002`, `--refresh`, `--batch-size 10`, `--sleep 2`

## Rate limit behavior

- Free plan: 30 runs concurrentes máx
- Script usa `run-sync-get-dataset-items` (bloqueante per-lead) con sleep 2s entre batches de 10
- No se necesita backoff explícito — Apify devuelve 403 `platform-feature-disabled` cuando se consume el budget

## Target selection

Orden de procesamiento (`select_targets`):
1. Filter: `qualifiesForMockup == True` (websiteStatus=no_website)
2. Skip: `ig_enriched_at` already set (a menos que `--refresh`)
3. Sort: priority asc, rating desc, reviews desc → mejores primero
4. Limit: `--limit N`

## Piloto (2026-04-24, 10 leads)

Hit rate: **4/10 (40%)**. Ver `project_market_tier_system.md` para lista completa.

Issues resueltos durante piloto:
- Error 400 con `&`/`-`/`.` → sanitizer regex completo
- "no_match" con username=None → filter de sentinel items con `error` key
- Retry fallback: si primera llamada falla, retry con primeros 2 tokens del query

## Referencias

- Script: `SPK - SPEKGEN AGENCY/PROSPECTOS/enrich_leads_apify.py`
- Sister: `project_market_tier_system.md`
- Actor docs: https://apify.com/apify/instagram-search-scraper
