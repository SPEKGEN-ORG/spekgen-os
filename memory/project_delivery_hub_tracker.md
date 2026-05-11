---
name: Delivery Hub Tracker
description: Dashboard local agency-wide en SPK - 17. TRACKER/. Servicios por cliente, progreso, faltantes, ciclo de cobro. App nativa macOS para Dock.
type: project
originSessionId: 3585f9e9-12e1-4bbc-8e9d-05fb0539a4fb
---
**Qué es:** Dashboard interno de Gibran para ver qué servicios contratados faltan por entregar a cada cliente (HC/LF/GR/MG), progreso actual, reinicio de ciclo.

**Path:** `SPK - SPEKGEN AGENCY/SPK - 17. TRACKER/`

**Entry point:**
- **Archivo a abrir:** `delivery_hub.html` (overview 4 clientes)
- **App nativa:** `SPEKGEN Tracker.app` (en la misma carpeta, Gibran lo tiene en el Dock)
  - Compilado con `osacompile` desde `/tmp/spk_tracker.applescript`
  - Abre Chrome en `--app` mode (sin barra URL) con `--user-data-dir=$HOME/Library/Application Support/SPK-Tracker`
  - Regenera HTML via `build_hub.py` cada vez que se abre

**Arquitectura:**
- `delivery_data.json` — source of truth (servicios contratados, fechas de cobro, ciclo)
- `build_hub.py` — genera 5 HTMLs (overview + 4 per-client)
- `build_evidence_report.py` — resuelve thumbnails de posts (con `recursive=True` glob + fallbacks a `SPK - 15. FACTORY/`)
- `delivery_hub_{HC,LF,GR,MG}.html` — vistas per-client con nav sticky, prev/next, keyboard shortcuts ←/→/Esc

**Fechas de cobro:**
- HC: día 19 (ciclo 18→17 del mes siguiente)
- LF: día 28
- GR: día 30
- MG: día 30

**Cómo iterar:**
1. Editar `delivery_data.json` o `build_hub.py`
2. El `.app` regenera al abrir — no hay paso manual de rebuild

**Regla:** Gibran seguirá usándolo e iterándolo según descubra gaps. No agregar features por anticipado.
