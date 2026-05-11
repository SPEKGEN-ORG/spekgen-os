# Feedback: Prospects — validar leads 1x1 antes de marcar ready

**Incidente:** 2026-04-23. Generé 5 mockups + publiqué a spekgen.com + marqué 4 leads `outreachReady=True` para cron, pero los 5 tenían website en Google Maps. El pitch G "te armé algo para ti" no aplicaba. Gibran los catched antes del cron — "TODOS ESOS BUSINESSES YA TIENEN WEBSITE!!!!".

**Root cause (técnico):** `compute_qualification.py` tenía gate permisivo — `junk_aggregator` + `parked_or_down` calificaban como True. Cualquier HEAD request que fallara (rate limit, bot block, timeout) marcaba `qualifiesForMockup=True` aunque el site estuviera vivo.

**Root cause (proceso):** Confié en el count agregado (`1,825 califican`) sin validar cada lead que iba a enviarse. Los 5 específicos que marqué ready nunca los miré uno por uno — sólo miré que tuvieran email + mockup + tier G.

**Regla permanente:**
1. Gate `qualifiesForMockup` STRICT: sólo `websiteStatus == "no_website"`. Si Google Maps lista CUALQUIER website, no califica (aunque HEAD falle).
2. Antes de marcar `outreachReady=True` en CUALQUIER lead, imprimir: `id | business | website | email | mockupUrl` y validar 1x1 que:
   - `website` esté vacío O sea aggregator basura
   - `email` tenga dominio real resolvible (no Canva, no subdomains raros)
   - `firstName` sea personal o "Equipo" (nunca el primer token del business name)
   - `mockupUrl` responda 200 y tenga el slug correcto con sufijo `mockup`
3. Antes de generar mockups en batch, confirmar el batch con Gibran: "voy a generar mockups para estos N leads, aquí están sus websites, ¿procedo?"

**Contradicción estructural pendiente:**
- `qualifiesForMockup=True` requiere `no_website`
- Apollo email discovery requiere `domain` (= tienen web)
- ⇒ matemáticamente casi ningún lead tiene ambos. Resolver con: scraping de IG bios / scraping de descripción Maps / WhatsApp-only outreach.

**Feedback de Gibran literal:**
- "No quiero que te estés perdiendo en configuraciones que no servirán"
- "Haces un chingo de cosas, al final nada sirve"
- "Tengo que hacerlo yo desde 0"

**Implicación:** Para próxima sesión de prospects: pedir ICP + canal EXACTO al inicio. Validar 5 leads específicos 1x1 antes de publicar mockup. Cero batches ciegos.

**Commits relacionados:** `bd39754` · `c8805e3` · `ea63928` en `g-bran/spekgen-prospectos`.

---

## Update 2026-04-24 — Fork outreach: gate STRICT v2 + market_tier

**Fix al bug:** reescribí `compute_qualification.py`:
- Bug del `except RequestException` → devolvía `qualifiesForMockup=True`. **Fix:** ahora `False`.
- Añadí 2 gates adicionales: `market_tier ∈ {A,B}` + NOT (`active_in_meta_ads` con dominio detectado).
- Campo nuevo `qualifyReason` en cada lead (`pass` / `has_website` / `junk_aggregator` / `parked_or_down` / `market_tier_c` / `active_meta_ads_with_domain` / `exception_during_classify`) — auditable desde dashboard.
- Delta logging por industry antes/después, para cazar movimientos sospechosos en futuros runs.
- Flag `--no-http` para re-aplicar sólo el gate sin re-hacer requests HTTP.

**Market tier system:** detalle completo en `project_market_tier_system.md`. El gate ahora respeta el criterio Q4 2025: follower count (<1K skip, 1K-10K B, 10K+ A). Reemplaza validación manual.

**Apify enrichment:** detalle completo en `project_apify_enrichment.md`. Piloto 4/10 hits; los 4 Market A/B encontrados fueron leads que Gibran ya tenía en radar. Sanitizer regex crítico para el actor IG Search.

**Regla nueva:** antes de marcar `outreachReady=True`, validar también que `market_tier ∈ {A,B}`. Un lead Market C (<1K followers) indica negocio inactivo digitalmente → mockup no va a mover aguja. Dashboard filter chip "Market" permite hacerlo visualmente.
