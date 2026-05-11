---
name: Operational deliverables require PDF copy alongside MD
description: Gibran no consume .md files comodamente. Todo doc operativo entregable debe tener copia PDF visual ademas del .md de trabajo.
type: feedback
---

Todo entregable operativo (auditorias, planes, briefs, propuestas, analisis, reportes) debe entregarse en **dos formatos simultaneos**:
1. `.md` — fuente de trabajo que Claude usa para editar/buscar/actualizar
2. `.pdf` — version visual que Gibran lee

**Why:** Gibran opera desde Drive/vista humana. Los .md se ven crudos en Drive/Finder y los recibe mal. Cuando un cliente los pide (Lupita, Monse, Enrique) necesita un PDF presentable para compartir.

**How to apply:**
- Al crear CUALQUIER entregable operativo, generar ambas versiones en el mismo paso
- PDF debe usar estilo SPEKGEN (tipografia limpia, headers visibles, tablas legibles)
- Guardar ambos en la misma carpeta con el mismo nombre (e.g. `TIKTOK_SHOP_AUDIT_2026-04-10.md` y `TIKTOK_SHOP_AUDIT_2026-04-10.pdf`)
- Al comunicar a Gibran, incluir ambos paths con `open` clickable, pero destacar el PDF

**NO aplica a:** memoria interna (`~/.claude/memory/`), CLAUDE.md files, _CLIENT_CONTEXT.md, _KNOWLEDGE_BASE.md, MEMORY.md. Esos son infraestructura operativa de Claude, no entregables para humanos.

**Precedente:** Regla `feedback_no_projections_operational_pdfs.md` ya establece que entregables operativos son PDF. Esta regla lo refuerza y lo hace default para CUALQUIER deliverable, no solo propuestas con proyecciones.
