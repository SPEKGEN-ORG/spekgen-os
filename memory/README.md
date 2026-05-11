# memory/ — Claude knowledge files

Archivos `project_*.md` y `feedback_*.md` que documentan el conocimiento acumulado de SPEKGEN. Claude los lee automáticamente al inicio de cada sesión (vive simbólicamente en `~/.claude/projects/.../memory/` del usuario, este folder es el repo-tracked source de verdad).

## Convención de nombres

- `project_*.md` — estado / contexto de un proyecto, cliente, o sistema (ej. `project_hc_bot_live.md`, `project_f24_product_research_skill.md`).
- `feedback_*.md` — lecciones técnicas / bugs / quirks descubiertos (ej. `feedback_make_iml_no_and_or_functions.md`).
- `MEMORY.md` — index de toda la memoria con una línea por archivo (mantener ≤200 chars por línea).

## Reglas

- **NO commitear archivos personales.** `user_*.md`, `*_disconnection_plan.md`, archivos con info financiera personal van en `.gitignore`. Si necesitas info personal, vive solo en tu `~/.claude/projects/.../memory/` local.
- **NO pegar credenciales reales.** Está OK escribir "GR_SHOPIFY_TOKEN existe en `.env`" pero NUNCA `GR_SHOPIFY_TOKEN=shpat_abc123...`.
- **Index obligatorio en MEMORY.md.** Toda memoria nueva va al index con 1 línea descriptiva. Si pasa de 200 chars, el detalle se queda solo en el archivo individual.

## Sync con Claude Code

Cada miembro tiene una copia local en su `~/.claude/projects/.../memory/`. Para sync entre repo y Claude:

```bash
# Pull del repo a Claude local
rsync -a ~/dev/spekgen-os/memory/ ~/.claude/projects/-Users-*-CLIENTS-OFFICIAL/memory/ --exclude='.git'

# Push de Claude local al repo (cuidado con archivos personales)
rsync -a ~/.claude/projects/-Users-*-CLIENTS-OFFICIAL/memory/ ~/dev/spekgen-os/memory/ --exclude='user_*' --exclude='*_disconnection_plan*'
```

(Roadmap: script automatizado para esto, hook bidireccional.)

## Auditoría periódica

Cada par de semanas vale correr `consolidate-memory` (skill) para:
- Detectar duplicados (mismo conocimiento en 2 archivos).
- Identificar archivos stale (info ya no vigente).
- Mantener `MEMORY.md` index ordenado.
