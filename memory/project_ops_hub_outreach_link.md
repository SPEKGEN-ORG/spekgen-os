---
name: OPERATIONS HUB ahora linkea al outreach :8771 (cleanup 2026-04-28)
description: SPEKGEN Operations Hub (server.py :8765) limpiado y card "Prospectos" relinkeada al sistema nuevo de outreach
type: project
originSessionId: 99bf4022-b3d3-4cd0-8c8a-7e3e9230f758
---
El SPEKGEN Operations Hub (`SPK - 18. OPERATIONS HUB/server.py` en `localhost:8765`) tenía embebido el sistema viejo de outreach que ya no existe. Limpiado 2026-04-28.

**Why:** Card "Prospectos" del HUB apuntaba a `/prospects` (route interno que servía `PROSPECTOS/dashboard/index.html`). Esa carpeta `dashboard/` ya no existe — el sistema nuevo vive en `PROSPECTOS/_tools/serve_dashboard.py` corriendo en puerto independiente :8771. Resultado: 404 cada vez que Gibran abría la card.

**How to apply:**
- HUB (`:8765`) ahora sirve SOLO Delivery (cards Prospectos + Entregables, pero la card Prospectos abre `localhost:8771` en pestaña nueva con `target="_blank"`)
- Outreach (`:8771`) corre como server independiente en `PROSPECTOS/_tools/serve_dashboard.py --persistent` con LaunchAgent
- Decoupled: cero dependencias cruzadas entre los dos servers. Si uno cae, el otro sigue
- `server.py` del HUB pasó de 717 → 602 líneas. Eliminado: routes `/prospects*`, `/api/leads*`, POST `/save`, helpers `leads_to_csv` + `_serve_prospects_asset`, constants PROSPECTS_DIR/LEADS_FILE/LEADS_BACKUP/SNAPSHOTS_LEADS, imports csv/io
- Si en futuro hay que cambiar el target del link, está hardcoded en `index.html` línea 186 del HUB
- Si Gibran pide "agregar otra card al HUB", el patrón es: nueva card en `index.html` + (opcional) nueva route en `server.py` si hay endpoints write-back. Si solo es link a otro server, `target="_blank"` directo
