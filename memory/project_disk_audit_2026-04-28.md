---
name: Disk audit + cleanup ejecutado 2026-04-28
description: Liberados 64 GB del disco (de 178 GB → 114 GB usados). Catálogo de qué se borró y qué sigue intacto.
type: project
originSessionId: 99bf4022-b3d3-4cd0-8c8a-7e3e9230f758
---
Auditoría de disco ejecutada 2026-04-28. Disco pasó de 178 GB usados (90%) → **114 GB (58%)**, recuperados **64 GB**.

**Why:** La compu se saturaba constantemente y MacBook tenía solo 21 GB libres de 228 GB. Drive y Chrome se comportaban raro por falta de espacio.

**How to apply:**
- Si Gibran reporta compu lenta otra vez, primer paso = `df -h` y `du -sh ~/Library/Caches/*`
- Lo borrado y por qué (todos regenerables o confirmados deprecated):
  - Claude `vm_bundles` (19 GB) — `~/Library/Application Support/Claude/vm_bundles`. Regenera al usar local-agent-mode
  - Claude `local-agent-mode-sessions` (5.3 GB) — sesiones viejas
  - Chrome HTTP cache (11 GB) — `~/Library/Caches/Google/Chrome`
  - GREENRAY legacy (20 GB) — `~/Documents/GREENRAY` (lo borró Gibran). Carpeta vieja pre-reorganización a `CLIENTS OFFICIAL/GR - GREENRAY/`
  - `~/editor-pro-max` (960 MB) — proyecto inactivo confirmado
  - `~/Developer/spekgen-hub` (854 MB) — Hub viejo Vercel/Next, deprecated. Hub vive ahora 100% en Shopify
  - node_modules + __pycache__ + .venv dentro de `CLIENTS OFFICIAL/` (cleanup masivo)
  - Caches: WhatsApp, Playwright, Loom ShipIt, OpenAI Atlas/Chat, loom-updater
- Apps confirmadas que NO tocar nunca: Ableton Live 11 Suite, CapCut, Discord, Antigravity (ver `feedback_apps_no_borrar.md`)
- `.gitignore` global activo en `~/.gitignore_global` configurado via `git config --global core.excludesfile`. Cubre node_modules, __pycache__, .venv, .next, dist, build, .DS_Store
- Drive saturado al 100% CPU como efecto colateral del borrado masivo — fix con `pkill -9 -f "Google Drive"` + `open -a "Google Drive"` (ver `feedback_drive_overload_after_mass_delete.md`)
- Pendiente: script `disk_cleanup.sh` en `SPK - 03. SCRIPTS/` para correr 1x/semana. Gibran lo postergó.
