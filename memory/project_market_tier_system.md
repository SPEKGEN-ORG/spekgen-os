# Market Tier System (SPEKGEN Prospects — 2026-04-24)

**Objetivo:** replicar la metodología SPEKGEN 2025 Q4 (xlsx "February DM DB") que filtraba prospects por **follower count** antes de contactar. Gibran validó manualmente en su momento: "Solo 700 Follows" → skip; "16mil follows" → contactar. Automatizado ahora con Apify.

## Definición

Field nuevo en `leads_data.json`: `market_tier` ∈ {`A`, `B`, `C`, `null`}.

| Tier | Followers (IG/FB max) | Etiqueta | Acción |
|------|-----------------------|----------|--------|
| **A** | ≥ 10,000 | Sweet spot / ideal | Priority outreach + mockup custom |
| **B** | 1,000 – 9,999 | Entry/mid | Outreach estándar |
| **C** | < 1,000 | Skip | NO outreach (inactivos/sin tracción) |
| `null` | No enriched aún | Pending | Correr Apify |

Campos relacionados en cada lead:
- `market_tier`                     → A/B/C
- `market_tier_source`              → `ig` | `fb` | `combined` | `none`
- `market_tier_max_followers`       → el follower count usado
- `market_tier_classified_at`       → timestamp ISO
- `ig_handle`, `ig_url`, `ig_followers`, `ig_fullName`, `ig_bio`, `ig_match_score`, `ig_enriched_at`, `ig_enrich_error`

## Pipeline (orden obligatorio)

```
1. compute_qualification.py        → websiteStatus + qualifyReason (gate STRICT)
2. enrich_leads_apify.py --limit N → ig_handle + ig_followers (Apify IG Search)
3. clasificar_market_tier.py       → market_tier A/B/C/null
4. compute_qualification.py --no-http → re-aplica gate con market_tier cargado
5. Dashboard muestra columna Market + chips filter
```

**Nota:** paso 1 es orthogonal a los otros — market_tier es ADICIONAL al tier interno (G/A/B/C/FP por industria+rating). Ambos coexisten en columnas separadas del dashboard ("Tier" legacy vs. "Market" nuevo).

## Gate STRICT v2 (compute_qualification.py)

`qualifiesForMockup = True` SOLO si TODAS:
1. `websiteStatus == "no_website"` (confirmed, no inferred de HEAD fail — fix bug 2026-04-23)
2. `market_tier ∈ ["A", "B"]`  (si está seteado; null pasa por ahora)
3. NOT (`active_in_meta_ads is True` AND `meta_ads_domain` detectado)

Cuando excepción ocurre en classify → `qualifiesForMockup=False` (fix del bug original que devolvía True).

## Dashboard (2026-04-24)

- **Columna nueva "Market"** entre Tier y ★: muestra badge `MA/MB/MC` o `—` (pending), + follower count fmt ("22K"), + link IG clickable
- **Filter chips "Market (followers)"**: MA / MB / MC / Pending con counts
- **Filter chips "Tier"** renombrados (antes decían "Market A/B/C" — confusos): ahora "Tier A/B/C" para distinguir
- Paleta: MA verde, MB azul, MC slate, Pending dashed gris

## Resultados piloto (2026-04-24, 10 leads)

Hit rate inicial: **4/10 (40%)**. Hits:
- P-053 Lobitos Seafari → @lobitosseafari · **4,049 → MB**
- P-003 Mr. Bu Yachts — no_results (retry con sanitizer fix también no_results — probablemente IG con handle no matcheable)
- P-046 BajaProTours → @bajaprotours · **549 → MC**
- P-027 WE BOAT BAJA → @weboatbaja · **21,991 → MA** 🔥
- P-044 Guaycura Tours → @guaycuratourslapazbcs · **1,702 → MB**
- P-128 Casa 1880 — no_match
- P-116 Arena La Paz → @arenablancalpz · **122 → MC**
- P-108 Polideportivo — no_results
- P-184 Suites Baja Sol — no_results
- P-095 Pescadería Punta Abreojos — no_results

Misses genuinos: 4-5 / 10. Probablemente no tienen IG, o IG con handle no relacionado al business name. Tasa ~40% esperada para BCS small-business (muchos sin IG, otros con handle personal del dueño).

## Budget & Costo

- Apify free plan: **$5 USD / ciclo mensual**
- Costo/lead: ~$0.003 USD (IG Search con `resultsLimit=5`)
- Mass run sobre 1,825 qualifying = ~$5.5 → **consume todo el budget**
- Escalonado recomendado: 500 leads / corrida = $1.5 → 3-4 corridas caben en budget

## Referencias

- Memoria hermana: `project_prospects_system.md` · `project_apify_enrichment.md` · `feedback_prospects_validation_gates.md`
- Script entrada: `SPK - SPEKGEN AGENCY/PROSPECTOS/{compute_qualification,enrich_leads_apify,clasificar_market_tier}.py`
- Dashboard: `PROSPECTOS/dashboard/index.html` (1,455 líneas post-update)
- Backup pre-migration: `dashboard/backups/leads_data_pre_market_tier_20260424_083026.json`
