---
name: .gitignore global activo en ~/.gitignore_global
description: Configuración git global que ignora node_modules, __pycache__, .venv, .DS_Store, etc. en todos los repos
type: reference
originSessionId: 99bf4022-b3d3-4cd0-8c8a-7e3e9230f758
---
Configurado 2026-04-28 después de auditoría de disco. Path: `~/.gitignore_global`. Activado via `git config --global core.excludesfile ~/.gitignore_global`.

Cubre:
- **Node:** node_modules/, .next/, .nuxt/, .cache/, dist/, build/, out/, *.tsbuildinfo
- **Python:** __pycache__/, *.py[cod], .venv/, venv/, env/, .pytest_cache/, .mypy_cache/, .ruff_cache/, *.egg-info/
- **macOS:** .DS_Store, ._*, .Spotlight-V100, .Trashes
- **Editors:** .vscode/, .idea/, *.swp, .cursor/
- **Logs/temp:** *.log, npm-debug.log*, .npm/, .yarn/
- **Env locales:** .env.local, .env.*.local (NO .env — ese se queda local pero NO se commitea por convención)

**Cuándo me sirve:** cuando trabaje con cualquier repo git de Gibran no necesito proponer agregar gitignores básicos — ya están globales. Solo agregar al .gitignore del proyecto cosas específicas del proyecto (build outputs custom, secrets paths, etc.).

**Gotcha:** Drive Desktop NO respeta .gitignore (no tiene .driveignore). Para que estos archivos no se sincronicen a Drive hay que mover los proyectos fuera del path de Drive O esperar limpieza periódica. Por ahora opción 2 acordada con Gibran.
