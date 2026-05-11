---
name: hc-lead-scraper
version: v001
description: "Scrapea leads B2B para Healthy Chuchos desde Google Maps (veterinarias, pet shops, groomers) + enrichment automatico de emails desde websites. Dedupe automatico contra master list y blocklist. ACTIVAR cuando Gibran diga: 'scrape leads HC', 'busca leads B2B', 'consigue prospects', 'actualiza master list', 'corre el scraper', 'trae leads nuevos', 'weekly scrape HC', 'necesito mas leads B2B', 'leads de veterinarias', 'leads en [ciudad]', o cualquier variante de conseguir nuevos contactos B2B para el outreach de HC. Output: filas nuevas en B2B_MASTER tab de HC_PROSPECTS_MASTER.xlsx."
---

# HC Lead Scraper — B2B desde Google Maps

## Qué hace este skill

Scrapea Google Maps para conseguir leads B2B (veterinarias, pet shops, groomers) en ciudades objetivo, extrae nombre/website/teléfono/dirección/rating, visita el website de cada negocio y extrae emails públicos, deduplica contra la master list existente, y guarda todo directo en `HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/00. DATABASE/HC_PROSPECTS_MASTER.xlsx` tab `B2B_MASTER`.

No requiere login ni API keys. Usa Playwright para scraping web.

## Cuándo usar

- **Cada lunes 9 AM** como parte del weekly scrape workflow (SOP completo en `HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/HC_WEEKLY_SCRAPE_SOP.md`)
- Cuando se necesiten leads frescos antes de un envío
- Al inicializar una nueva ciudad/preset
- Para hacer backfill (ej. ciudades no scrapeadas antes)

## Workflow

### PASO 1: Decidir qué scrapear

Hay 2 modos:

**Modo A — Preset semanal (recomendado):**
Usa un preset predefinido (w16, w17, w18, w19) que combina múltiples queries × ciudades. Un preset ≈ 4 queries × 12 results = ~48 raw, ~30-35 después de dedupe, ~20% con email válido.

| Preset | Ciudades cubiertas | Queries |
|---|---|---|
| `w16` | Guadalajara, Zapopan | veterinaria, pet shop, estetica canina |
| `w17` | CDMX | veterinaria, pet shop, hospital veterinario |
| `w18` | Monterrey | veterinaria, pet shop, estetica canina |
| `w19` | Querétaro, Puebla | veterinaria |

**Modo B — Query única (debug o ad-hoc):**
Scrape una query específica en una ciudad específica. Útil para ciudades nuevas o debugging.

### PASO 2: Correr el scraper

```bash
cd "HC - HEALTHY CHUCHOS/HC - 17. OUTREACH"

# Preset
python3 hc_gmaps_scraper.py --preset w16 --limit 12

# Query única
python3 hc_gmaps_scraper.py --query "veterinaria" --city "Monterrey" --limit 20

# Sin email enrichment (más rápido, solo para tener company+phone)
python3 hc_gmaps_scraper.py --preset w16 --limit 10 --no-emails

# Debug visible (no headless)
python3 hc_gmaps_scraper.py --query "veterinaria" --city "CDMX" --limit 5 --show-browser
```

**Flags:**
- `--limit N` — máximo resultados por query (default 20). Subir para más volumen.
- `--no-emails` — skip email enrichment (útil para first-pass rápido)
- `--show-browser` — modo headful para debug (ver qué hace el scraper)

### PASO 3: Verificar output

El script imprime:
- Queries ejecutadas + places encontrados por query
- Lista de nombres + websites + teléfonos
- Dedupe summary (raw → nuevos)
- Email enrichment por fila
- Total agregado al xlsx + % con email

**Target de calidad:**
- ≥20% de rows con email válido (los demás van como `status=no_email`, útiles para WA_MASTER luego)
- 0 emails obviamente falsos (tu@email.com, info@example.com, etc.) — si aparecen, actualizar lista de blocks en el script

### PASO 4: Review manual (rápido)

Abrir el xlsx y revisar las últimas 30-40 filas agregadas:

```bash
open "HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/00. DATABASE/HC_PROSPECTS_MASTER.xlsx"
```

Cosas a verificar:
1. Emails claramente falsos o genéricos (info@, contacto@) — decidir si se envía o no
2. Duplicados que pasaron el filter (ej. misma clínica con 2 sucursales → OK mantener)
3. Segment correcto (veterinaria → clinica, pet shop → petshop, estetica → groomer)

### PASO 5: Log semanal

Registrar la ejecución en el tab `SCRAPE_LOG` del xlsx con:
- Fecha, week, source (google_maps), categoria (B2B), volumen bruto, post-dedupe, post-validation, issues, tiempo

## Archivos clave

| Archivo | Ubicación |
|---|---|
| `hc_gmaps_scraper.py` | `HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/` — el scraper |
| `HC_PROSPECTS_MASTER.xlsx` | `HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/00. DATABASE/` — output |
| `HC_WEEKLY_SCRAPE_SOP.md` | `HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/` — SOP completo |

## Dependencias

```bash
pip install playwright openpyxl
playwright install chromium
```

Ya instaladas en el entorno SPEKGEN.

## Rotación de queries (importante)

Cada semana usar un preset distinto para evitar:
- Ser detectado por anti-bot de Google Maps
- Saturar una ciudad con leads de baja calidad
- No diversificar geográficamente

Ciclo sugerido:
- W16, W20, W24 → w16 (GDL/Zapopan)
- W17, W21, W25 → w17 (CDMX)
- W18, W22, W26 → w18 (MTY)
- W19, W23, W27 → w19 (QRO/Puebla)

Cada ciudad se vuelve a scrapear cada ~4 semanas con criterios frescos.

## Notas legales

- Google Maps data es pública y scrapeable (ToS debatible pero no ilegal en MX)
- Emails del website del negocio también son públicos
- El outreach que sigue respeta LFPDPPP: opt-out claro, sin venta directa en E1, unsubscribe en cada email

## Limitaciones conocidas

- **FB Pages como website:** ~40% de las veterinarias pequeñas solo tienen FB Page. No podemos scrape FB → estas quedan sin email (pero sí con teléfono → WA_MASTER)
- **Rate limit GMaps:** si se corre muchas veces seguidas, GMaps puede pedir captcha. Solución: esperar 2-4 horas o usar VPN
- **Websites con Cloudflare:** algunos blockean Playwright → esos quedan sin email
- **Enrichment solo busca `/contacto`, `/about`:** sitios con contacto en JS dinámico no se capturan

## Expansión futura (backlog)

- Agregar scraping de directorios públicos: AMMVEPE, SECCAM, páginas amarillas MX
- Apollo.io free tier integration (50 credits/mes gratis con cuenta nueva)
- Enriquecer también con LinkedIn profiles cuando haya website empresarial
- D2C scraper: Facebook Groups + Instagram hashtags (requiere cuenta humana logueada)
