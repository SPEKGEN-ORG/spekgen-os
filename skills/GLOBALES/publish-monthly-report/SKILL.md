---
name: publish-monthly-report
description: Genera y publica un reporte mensual de performance como dashboard HTML en spekgen.com (Shopify Content Hub). Toma un context JSON con KPIs, tablas, insights → renderea template Jinja2 → publica con URL pública limpia (ej. spekgen.com/hc-reporte-marzo-abril) usando versionado por hash para bypass del page_cache. Usar cada mes para cada cliente (HC, LF, GR, MG) cuando haya que cerrar el ciclo y mandar entregable público. Reusa shopify_client.py y patrones de publish-prospect.
---

# publish-monthly-report

Skill para generar el reporte mensual de cualquier cliente como dashboard HTML público en `spekgen.com/{handle}`.

## Cuándo usar

- Día 20 de cada mes (cierre del ciclo de retainer)
- Cada vez que haya que mandar al cliente un entregable visual y honesto del mes anterior
- Antes de una junta mensual con cliente → el reporte es el soporte

## Arquitectura

```
publish-monthly-report/
├── SKILL.md
├── scripts/
│   └── publish_report.py          # Main: Jinja2 render + Shopify publish
├── templates/
│   └── monthly_report.html.j2     # Dark dashboard dark theme, Chart.js, namespaced .spk-*
├── contexts/
│   └── {cliente}_{YYYY-MM}.json   # Context dict con KPIs y narrativa (input)
├── reports/
│   └── {handle}.html              # HTML renderizado (output local para QA)
└── config/                        # (futuro: clients.yaml con accent colors, fuentes)
```

El template vive en `templates/monthly_report.html.j2`. El context JSON tiene la estructura que el template espera (ver `contexts/hc_2026-03.json` como referencia canónica).

## Workflow

### Opción A — Manual (para el primer reporte de cada cliente)

1. **Recolectar data del período:**
   - Meta Ads → Marketing API via `{CLIENTE}/05. META ADS/.../04. MONITORING/`
   - GA4 → Data API con service account del cliente
   - Shopify → Admin GraphQL `shopify_client.py` del `_CONTENT_HUB_SHOPIFY/`
   - Organic → `{CLIENTE}_SOCIAL_MEDIA_CALENDAR.xlsx` + Meta Graph `/insights`
   - Outreach → `{CLIENTE}/17. OUTREACH/00. DATABASE/*.xlsx`
   - WhatsApp blasters → screenshots/logs manuales

2. **Escribir el context JSON** a mano en `contexts/{cliente}_{YYYY-MM}.json` siguiendo la estructura del template (client, period, summary, contract, value_adds, meta_ads, organic, ga4, shopify, whatsapp, outreach, learnings).

3. **Render + publish:**
   ```bash
   python3 scripts/publish_report.py \
     --context contexts/hc_2026-03.json \
     --handle hc-reporte-marzo-abril \
     --title "Healthy Chuchos · Reporte Marzo-Abril 2026"
   ```

4. **Verificar:**
   - `curl -I https://spekgen.com/{handle}` → 301 → 200
   - Abrir URL, revisar Chart.js, responsive, colores correctos

### Opción B — Semi-auto (futuro, una vez probado el skill)

Agregar `scripts/build_{cliente}_context.py` que jala data automáticamente de las fuentes y genera el JSON. Luego llamar a `publish_report.py`.

### Opción C — Full auto (cron día 20, Japan-proof)

GitHub Actions workflow corre día 20 de cada mes 10:00 AM MX, matriz por cliente activo. Template en `.github-workflow-template.yml` (TBD).

## Context JSON — Estructura esperada

Ver `contexts/hc_2026-03.json` como ejemplo completo. Las claves obligatorias:

```jsonc
{
  "generated_at": "20 Abril 2026",
  "client": {
    "name": "Healthy Chuchos",
    "tagline": "Reporte de performance",
    "accent_color": "#f59e0b",          // color del cliente
    "accent_soft": "rgba(245,158,11,.14)"
  },
  "period": {
    "label": "19 Mar – 19 Abr 2026",
    "days": 30,
    "month_number": 1,
    "executive_headline": "…"           // 1-3 frases
  },
  "summary": {
    "narrative": "…",
    "kpis": [ {"label":"", "value":"", "sub":"", "tag":"", "tag_type":"good|warn|info"} ]
  },
  "contract": {
    "retainer_mxn": "7,500",
    "deliverables": [ {"item":"", "contracted":"", "delivered":"", "pct":0-100, "bar_class":"good|warn|danger", "status":"", "status_class":"good|warn|danger", "note":""} ],
    "honest_note": "…"
  },
  "value_adds": [ {"title":"", "desc":""} ],
  "meta_ads": {"context":"…", "kpis":[…], "ads_top":[…], "insight":"…"},
  "organic": {
    "context":"…", "kpis":[…],
    "status_labels":[…], "status_values":[…],   // Chart.js doughnut
    "product_labels":[…], "product_values":[…], // Chart.js bar
    "insight":"…"
  },
  "ga4": {"context":"…", "kpis":[…], "top_pages":[…], "top_sources":[…], "insight":"…"},
  "shopify": {"context":"…", "kpis":[…], "by_product":[…], "honest_note":"…"},
  "whatsapp": {"context":"…", "blasters":{"title":"","desc":""}, "bot":{"title":"","desc":""}},
  "outreach": {"context":"…", "kpis":[…], "insight":"…"},
  "learnings": {"wins":[{"title":"","desc":""}], "fixes":[{"title":"","desc":""}], "next_step":"…"}
}
```

Secciones opcionales: `whatsapp` y `outreach` se esconden si no están en el context.

## Pitfalls críticos (heredados de publish-prospect)

1. **Shopify page_cache poisoning** → El script versiona el handle con hash SHA-256 del body (`{handle}-v{hash6}`) y crea un redirect `/{handle}` → `/pages/{handle}-v{hash6}`. Nunca editar en sitio un handle ya existente.
2. **Horizon theme `.grid` collision** → `rename_colliding_classes()` renombra `class="grid"` → `class="spk-grid"` automáticamente. El template ya usa `.spk-*` namespace en todas sus clases.
3. **Shopify strips `gid://`** → No embeder gids de Shopify en el HTML del reporte.
4. **Chrome hider** → `CHROME_HIDER_CSS` oculta header/footer de Horizon automáticamente. No tocar — si algo del template necesita width completo ya está cubierto por `#spekgen-prospect-wrap`.
5. **PII financiera pública** → El reporte tiene revenue por producto, spend de ads, etc. La URL pública no tiene password. Si el cliente quiere privacidad, discutir pre-publish.

## Reglas de contenido (tono)

- **Honesto total.** Si hay gaps (ej. Meta Ads solo 17/20, orgánico 9/22), mostrarlos con la pct real en la barra de progreso. El `honest_note` de `contract` explica el contexto.
- **Sin maquillar.** Si el revenue externo real fue ~0 (como HC mes 1, todo MONSEVIP interno), decirlo en `shopify.honest_note`.
- **Value-adds son el contrapeso.** Todo lo entregado fuera del scope (Content Hub, bots, automations, outreach system) va en `value_adds` — balancea los gaps.
- **Sin proyecciones.** El reporte es retrospectiva. El plan del mes siguiente se discute en vivo en la call, no en el reporte.
- **Español correcto.** Todo copy con tildes y ñ. Palabras críticas del nicho (articulación, inflamación, daño, años, crónico).

## Clientes configurados

| Cliente | Handle sugerido | Accent color |
|---|---|---|
| HC | `hc-reporte-{mes-corto}` | `#f59e0b` (naranja ámbar) |
| LF | `lf-reporte-{mes-corto}` | TBD |
| GR | `gr-reporte-{mes-corto}` | `#4ade80` (verde) |
| MG | `mg-reporte-{mes-corto}` | TBD |

## Comandos

```bash
# Render local (no publica) para QA
python3 scripts/publish_report.py \
  --context contexts/hc_2026-03.json \
  --handle hc-reporte-marzo-abril \
  --title "Healthy Chuchos · Reporte Marzo-Abril 2026" \
  --dry-run

# Publish a spekgen.com
python3 scripts/publish_report.py \
  --context contexts/hc_2026-03.json \
  --handle hc-reporte-marzo-abril \
  --title "Healthy Chuchos · Reporte Marzo-Abril 2026"

# Verify
curl -sIL "https://spekgen.com/hc-reporte-marzo-abril" | grep -iE "^(HTTP|location)"
```

## Primer uso

- **2026-04-20** — Healthy Chuchos, período Mar 19 – Abr 19. Publicado en `spekgen.com/hc-reporte-marzo-abril`. Handle versionado `hc-reporte-marzo-abril-vbfc84f`.
