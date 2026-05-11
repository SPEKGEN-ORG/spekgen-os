---
name: Python glob.glob needs recursive=True
description: glob.glob() con patrones ** devuelve 0 hits silenciosamente si no pasas recursive=True. Bug común, falla silenciosa, no errorea.
type: feedback
originSessionId: 3585f9e9-12e1-4bbc-8e9d-05fb0539a4fb
---
`glob.glob(pattern)` **NO** soporta el wildcard `**` por defecto — requiere `recursive=True` explícito.

**Why:** Descubierto 2026-04-23 en `build_evidence_report.py` del Delivery Hub. Patrones como `HC - HEALTHY CHUCHOS/**/HC-024/**/*.png` silenciosamente devolvían 0 matches aunque los archivos existían (verificado con shell glob que tiene `globstar` activado). El dashboard mostraba "sin img" en ~10 posts. Falla silenciosa — no excepción, no warning, solo `[]`.

**How to apply:**
- Cualquier script Python que use `glob.glob()` con `**` en el path, **siempre** pasar `recursive=True`.
- Mejor aún: usar `pathlib.Path().rglob(pattern)` que es recursivo por default y más legible.
- Al debuggear "archivo no encontrado" en scripts que usan glob, primero verificar el flag antes de buscar el archivo en otro path.
- Sanity check rápido: comparar `len(glob.glob(p))` vs `len(glob.glob(p, recursive=True))` — si el primero es 0 y el segundo tiene hits, ese es el bug.
