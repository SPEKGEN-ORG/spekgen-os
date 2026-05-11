---
name: Reveal deliverables in Finder
description: Cada vez que entregue un archivo o carpeta como deliverable (PDF, xlsx, docx, png, mp4, carpeta nueva, etc.), correr `open -R <path>` después de generarlo para que Finder se abra con el archivo seleccionado.
type: feedback
originSessionId: 2bb73e9c-7673-4f72-8be5-09ef84768144
---
Cuando entregue cualquier archivo final (deliverable) o una carpeta nueva al usuario, además del markdown link en la respuesta, ejecutar:

```bash
open -R "<path absoluto del archivo o carpeta>"
```

Esto hace que Finder se abra con el archivo/carpeta seleccionado e iluminado — equivalente visual a un botón "Show in Finder".

**Why:** El UI de Claude Code no renderiza botones de "Show in Finder" para archivos no editables (PDFs, imágenes, etc.). Gibran quiere ver el archivo en Finder al instante sin tener que copiar paths a mano. Solicitado explícitamente 2026-05-04.

**How to apply:**
- Aplica para deliverables FINALES — PDFs, xlsx, docx, presentaciones, imágenes generadas, reportes, carpetas nuevas con contenido.
- NO aplica para archivos intermedios (código fuente que voy editando, .md de drafts, scripts internos). Sólo para outputs que el usuario va a usar/abrir/compartir.
- Si genero múltiples archivos en una entrega (ej. PDF + HTML + assets), revelar el archivo "principal" en Finder, no todos uno por uno.
- Si la entrega es una carpeta completa, usar `open` (sin `-R`) para abrir la carpeta directamente.
- Combinar con `open <archivo>` cuando además quiera que se abra inmediatamente en Preview/aplicación default (caso típico: PDF entregado).

**Comando útil:**
- `open -R <path>` → Finder se abre con archivo seleccionado
- `open <path>` → abre el archivo en su app default (Preview para PDF, etc.)
- Para PDFs deliverables suele convenir hacer ambos: `open <path>` para que el cliente lo vea + `open -R <path>` para que Finder esté listo si quiere mover/compartir el archivo.
