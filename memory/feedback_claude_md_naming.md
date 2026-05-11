---
name: Convention for referencing .claude folders
description: When Gibran says "CLAUDE.md global/root" he means the one at project root (01. CLIENTS OFFICIAL/.claude/). Per-client ones are referenced by client name.
type: feedback
---

Cuando Gibran dice "el CLAUDE.md global" o "el CLAUDE.md root" se refiere a `01. CLIENTS OFFICIAL/.claude/CLAUDE.md` (la configuracion principal del proyecto).

Cuando dice "el CLAUDE.md de [CLIENTE]" se refiere a `{CLIENTE} - SPEKGEN/.claude/CLAUDE.md`.

**Why:** Hay 5 carpetas .claude (1 root + 4 clientes) y Gibran necesita una forma clara de referirse a cada una sin ambiguedad.

**How to apply:** Siempre interpretar "global" o "root" como la carpeta .claude en la raiz del working directory. Nunca confundir con las de los clientes.
