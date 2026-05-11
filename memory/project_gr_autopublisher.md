---
name: GR Organic Autopublisher (DEPRECATED 2026-04-24 — reemplazado por Content Hub edge function)
description: GR Daily Organic Autopublisher GH Actions DESHABILITADO 2026-04-24. GR ahora publica via edge function `auto-publish` central (misma que HC/MG). Ver project_autopublisher_real_location.md.
type: project
originSessionId: 538253e6-95dc-4eb8-a1c8-52f9bff8a837
---
**⚠️ DEPRECATED 2026-04-24.** Workflow `GR Daily Organic Autopublisher` (gh workflow id 262432572, repo g-bran/Spekgen-ops) deshabilitado via `gh workflow disable`. GR ahora publica por la edge function Supabase `auto-publish` (id `d34687a4-6944-4150-906c-59777a196b04`) igual que HC y MG, triggered hourly. Single-source-of-failure-detection cross-client.

**Por qué se eliminó:** Gibran armó el Content Hub para GR y MG el 2026-04-24 (portales `spekgen.com/pages/{gr,mg}-stage` live). Tener dos autopublishers (GH Actions GR + edge function HC) significaba bugs no compartidos entre clientes. Unificar los 3 clientes en un solo publisher → si falla en uno, sabemos que puede fallar en los demás. Triple-guard anti-dedup de la edge function ahora protege a GR también.

**Para reactivar (si alguna vez):** `gh workflow enable "GR Daily Organic Autopublisher" --repo g-bran/Spekgen-ops`. Pero antes: confirmar que el flow nuevo (upload → portal → aprobación → edge function) no lo cubre ya.

---

## Histórico (pre-deprecation)

**Fact:** GR organic posts se publicaban via GH Actions, no crontab local ni FB native scheduling.

**Why:** Gibran viaja a Japón ~30 abril sin WiFi 21 días. Toda infra debe correr sin depender de su Mac. Pivote ejecutado 2026-04-22 tras consolidar workflow MG content.

**How to apply:**
- **Repo:** `g-bran/Spekgen-ops`
- **Workflow:** `.github/workflows/gr-daily-autopublisher.yml` — cron `5 16 * * *` (9:05 AM La Paz BCS = 16:05 UTC, sin DST)
- **Script:** `scripts/gr-organic-publisher/publisher.py`
- **Fuente de verdad:** `GR - 06. SOCIAL MEDIA/GR_SOCIAL_MEDIA_CALENDAR.xlsx` → sheet `CALENDARIO`
- **Trigger:** filas con `Estado == "Imágenes listas"` Y `Fecha == today`
- **Imágenes:** Drive folder `06. SOCIAL MEDIA/{MES}/{SEMANA}/GR-0XX/00. IMAGENES FINALES/*.png` via Service Account (`GR_SA_JSON_B64`)
- **Post-publish:** updatea xlsx → `Estado="Publicado"` + guarda IG permalink/FB post_id en Notas, sube xlsx a Drive, notifica via Make webhook

**Para agregar nuevos posts:**
1. Crear carpeta `GR - 06. SOCIAL MEDIA/<MES>/<SEMANA>/GR-0XX/00. IMAGENES FINALES/` con imagen(es)
2. Agregar fila al xlsx: Col A `GR-0XX`, Col B fecha, Col M `Imágenes listas`, Col U caption
3. Esperar 9:05 AM La Paz BCS del día

**Columnas clave (0-indexed):** ID=0, Fecha=1, Estado=12, Notas=19, Caption=20

**IDs operativos:**
- GR IG User: `17841474779124860`
- GR FB Page: `472031575985263`
- Pixel: `1694343195291445`

**Ejecución manual / DRY_RUN:**
```
gh workflow run gr-daily-autopublisher.yml -f dry_run=true
```

**Scripts deprecados (NO usar):** `GR - 06. SOCIAL MEDIA/_scripts/_DEPRECATED/publish_gr_organic.py` + `run_queue.sh`. Crontab local removido.

**Calendar view local:** `GR - 06. SOCIAL MEDIA/_views/GR_CALENDAR_VIEW.html` — HTML dark mode con filtros Estado/Semana, útil para verificar estado antes de agregar posts.
