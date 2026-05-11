---
name: kill-prospect skill
description: Skill /kill-prospect cierra prospectos fríos — borra Shopify pages+redirects, actualiza xlsx, archiva carpetas, soporta gracia 24h con cola JSON
type: project
originSessionId: 1a3e4951-226a-45ac-81c7-76d3508337d0
---
Skill `/kill-prospect` creada 2026-05-06 (sesión Mariscos Los Laureles + Terraza RealMar + Aventuras Naturales).

**Path:** `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/kill-prospect/SKILL.md`
**Script:** `SPK - SPEKGEN AGENCY/PROSPECTOS/mockup_factory/_kill_prospect.py`
**Runner:** **`/usr/bin/python3`** (Python 3.9 con openpyxl + requests preinstalados). NO `/opt/homebrew/bin/python3` (no tiene `requests`).

**Subcomandos:**
- `kill --query <id|nombre|tel> [--reason ...] [--in 24h] [--dry-run]`
- `process-pending` — ejecuta los kills cuyo `execute_at` ya pasó
- `list-pending` — lista la cola

**Qué hace:** (1) borra Shopify pages cuyo handle = `{slug}{mockup|propuesta}` o empieza con `{slug}{mockup|propuesta}-v` + redirects, (2) update `SPEKGEN_PROSPECTOS.xlsx` status → "No interesado" + nota fechada, (3) mueve `mockup_factory/generated/{slug}/` → `_KILLED/{slug}_{ts}/` y `_prospectos/{NOMBRE}/` → `_ARCHIVED/{NOMBRE}_{ts}/`, (4) append a `PROSPECTOS/_kill_log.md`.

**Resolver:** ID exacto, substring en biz/url, o teléfono purely-numeric ≥7 dígitos. Multi-match → error con lista.

**Cola (Japan-proof):** vive en `Spekgen-ops/state/pending_kills.json` (cloud source of truth). El local script auto-pushea via `git_sync_queue()` después de enqueue/process-pending. Si el repo no existe, fallback a `PROSPECTOS/_pending_kills.json`.

**Cloud processor:** GH Action `kill-prospect-processor.yml` (cron `5 14 * * *` = 8:05 AM La Paz). Script en `Spekgen-ops/scripts/kill-prospect-processor/process_pending.py`. Solo borra Shopify + manda email + commitea queue actualizada (NO toca xlsx ni carpetas locales — eso lo hace el script local cuando Gibran corre `process-pending` post-Japón). Secrets reusados del Content Hub + cross-client-intel: `SHOPIFY_SHOP/CLIENT_ID/CLIENT_SECRET`, `SPEKGEN_GMAIL_SENDER/APP_PASSWORD`, `REPORT_RECIPIENT`.

**Trigger manual:** `gh workflow run kill-prospect-processor.yml --repo g-bran/Spekgen-ops`

**Timestamps:** todos los entries usan UTC con timezone (`...+00:00`). Legacy entries naive se asumen UTC al parse. Display al usuario siempre en hora La Paz BCS (UTC-7).

**Estado actual cola (2026-05-06):** 3 prospectos encolados para 2026-05-07 14:00:
- LP-090 Mariscos Los Laureles
- LP-154 Aventuras Naturales
- LP-156 Terraza RealMar

**Por qué:** Gibran les mandó "se elimina en 24h" hoy 6 may ~14:00. Mañana hay que correr process-pending (o invocarme y digo "procesa la cola de kills").

**Why:** evitar dejar links públicos colgados de prospectos fríos + mantener pipeline limpio (status real). Reusable: 2-4 muertes/semana esperadas.

**How to apply:** Cuando Gibran diga "kill prospect X" / "da de baja a X" / "borra el link de X" → invocar este skill. Cuando diga "procesa kills" o sea día siguiente con cola pendiente → `process-pending`.
