---
name: publish-monthly-report skill
description: Skill global /publish-monthly-report para generar reportes mensuales HTML y publicarlos a spekgen.com. Primer uso HC 2026-04-20
type: project
originSessionId: cc9a53ea-14de-469a-9ef4-f9341518672d
---
Skill `/publish-monthly-report` (globales) para generar y publicar el reporte mensual de cualquier cliente como dashboard HTML en `spekgen.com/{handle}`.

**Path:** `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/publish-monthly-report/`

**Arquitectura:**
- `scripts/publish_report.py` — render Jinja2 + publish a Shopify. Reusa `shopify_client.py` de `_CONTENT_HUB_SHOPIFY/` y helpers de `PROSPECTOS/_publish_prospect.py` (CHROME_HIDER_CSS, rename_colliding_classes, extract_body_with_head, upsert_page, upsert_redirect, delete_stale_versions).
- `templates/monthly_report.html.j2` — dashboard dark theme, namespaced `.spk-*`, Chart.js 4.4.1, CSS var `--accent` por cliente, 10 secciones (hero, resumen, contratado, value-adds, meta ads, orgánico, GA4, shopify, whatsapp, outreach, aprendizajes).
- `contexts/{cliente}_{YYYY-MM}.json` — context dict input. Ver `contexts/hc_2026-03.json` como referencia canónica.
- `reports/{handle}.html` — output local para QA.

**Uso:**
```bash
python3 scripts/publish_report.py \
  --context contexts/hc_2026-03.json \
  --handle hc-reporte-marzo-abril \
  --title "Healthy Chuchos · Reporte Marzo-Abril 2026"
```

Flag `--dry-run` renderea solo local sin publicar.

**Primer uso (2026-04-20):** HC mes 1, período Mar 19 – Abr 19. Publicado LIVE en https://spekgen.com/hc-reporte-marzo-abril.

**Segundo uso (2026-04-24):** GR mes 1, período 30 Mar – 24 Abr. Publicado en https://spekgen.com/gr-reporte-abril. Adición clave: galería de imágenes de contenido (organic posts + ads) embebida como base64 via `scripts/inject_gallery.py` + publicación con `scripts/publish_prebuilt.py` (bypassa el re-render de Jinja2 para preservar la galería). Límite de Shopify body: ~500KB. Reducir imágenes a 220px/q55 para caber. Después de publicar: añadir `client_document` metaobject (category: `report_monthly`) para que aparezca en tab "Mis documentos" del Content Hub del cliente. También actualizar `contracted_service` en `_SERVICIOS_CONTRATADOS.md` + correr `update_services_hub.py --client {slug}`.

**Why:** Reporte mensual estandarizado para 4 clientes × 12 meses. El skill elimina el trabajo manual y deja todo para automatizar con GH Actions día 20 cada mes pre-Japón.

**How to apply:** Cuando haya que cerrar ciclo mensual de cualquier cliente (LF, GR, MG, HC), usar este skill. Para nuevos clientes: copiar `contexts/hc_2026-03.json` como base, cambiar accent color (ver tabla en SKILL.md), llenar KPIs del mes, publish. Futuro: `scripts/build_{cliente}_context.py` que jala data autómatica + GH Actions cron día 20.

**Pitfalls reusados de publish-prospect:** page_cache poisoning → versionado `{handle}-v{hash6}`; Horizon `.grid` collision → `.spk-grid`; chrome hider CSS ya incluido.
