# Contributing — spekgen-os

## Workflow básico

1. `git pull` antes de empezar.
2. Branch para cambios grandes: `git checkout -b feat/nombre-corto`.
3. Commits con prefijo: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.
4. Push y PR si tocaste skills compartidas; merge directo a main solo para docs/memory.

## Convenciones de skills

### Estructura mínima

```
skills/CATEGORIA/nombre-skill/
├── SKILL.md              ← OBLIGATORIO. Frontmatter `name` + `description`.
├── scripts/              ← Python helpers
├── agent_prompts/        ← Si la skill spawneja sub-agentes
├── templates/            ← Si genera HTML/PDF/etc.
└── README.md             ← Opcional, contexto extra para humanos
```

### Frontmatter de SKILL.md

```yaml
---
name: nombre-skill
description: 1-2 oraciones explicando qué hace + frases que la activan ("Activate for X, Y, Z").
---
```

### Reglas duras para scripts

- **NUNCA hardcodear paths a `/Users/...` o `C:\Users\...`.** Usar `tools/spekgen_paths.py`:
  ```python
  import sys
  sys.path.insert(0, str(Path(__file__).parents[3] / "tools"))  # llega a spekgen-os/tools
  from spekgen_paths import drive_root, client_dir
  ```
- **NUNCA leer `.env` con rutas hardcodeadas.** Usar `python-dotenv` con `~/.env.spekgen` o aceptar `--env-file` como flag.
- **Cross-platform Python invocation:** dentro de docs y prompts, escribir `python3` (genérico). Cada OS lo resuelve diferente (Mac → `/usr/bin/python3` o `python3`; Windows → `python` o `py`).
- **Path separators:** usar `pathlib.Path`, NO `os.path.join` con `/`.

## Skills nuevas

Para crear una skill:

1. `mkdir skills/{CATEGORIA}/nueva-skill`
2. Escribir `SKILL.md` con frontmatter completo.
3. Si tiene scripts: usar `tools/spekgen_paths.py` para todo path.
4. Correr `bash scripts/sync-skills.sh` (Mac/Linux) o crear junction manual (Windows).
5. Probar invocándola en Claude Code.
6. Commit + push.

## Skills deprecadas

Si una skill se vuelve obsoleta:
1. Mover a `skills/_DEPRECATED/{categoria}/{nombre}/` (crear carpeta si no existe).
2. Agregar nota en `SKILL.md`: `## ⚠ DEPRECATED YYYY-MM-DD — reemplazada por /nueva-skill`.
3. Update CLAUDE.md root si la mencionaba.

NO borrar inmediatamente — el histórico vale.

## Commits convencionales

```
feat(skill-name): agregar feature X
fix(skill-name): arreglar bug Y
docs(README): actualizar Z
refactor(tools): renombrar A a B
chore: bump deps
```

Scope es el nombre de la skill o folder afectado. Si toca múltiples → omitir scope.

## Code review (cuando seamos 3+)

- PRs en `skills/PERSONALIZADAS/` o `tools/` requieren approval de Gibran.
- PRs en `skills/GLOBALES/` requieren approval de Gibran Y otro miembro senior.
- PRs en `docs/`, `memory/`, `clients/*/...` se pueden auto-mergear.

Por ahora (Gibran + Pedro): merge directo a main para skills personales del propio cliente, PR para cambios cross-client.
