---
name: Always keep files updated — proactive close protocol
description: Claude must proactively update _CLIENT_CONTEXT.md, CLAUDE.md, and memory at end of every session. Never let files go stale.
type: feedback
---

Los archivos se quedan desactualizados constantemente. Claude construye cosas, crea archivos, cambia estados — pero no actualiza los archivos de referencia. Esto causa que la siguiente sesión arranque con info vieja.

**Why:** Gibran ha encontrado múltiples veces que datos en memorias, _CLIENT_CONTEXT.md, y otros archivos estaban incorrectos o desactualizados. Esto lleva a decisiones basadas en info falsa (ejemplo: montos de clientes eran $8K cuando en realidad eran $6K).

**How to apply:**
1. Al FINAL de cada sesión, sin esperar que Gibran lo pida, actualizar `_CLIENT_CONTEXT.md` con lo que se hizo
2. Si se creó un archivo nuevo importante, registrarlo en el CLAUDE.md correspondiente o en _CLIENT_CONTEXT.md
3. Si cambió un dato que está en memoria (precios, IDs, status), actualizar el archivo de memoria
4. Si no estás seguro de un dato, marcarlo como "POR CONFIRMAR" en vez de inventar o asumir
5. Leer ClickUp al inicio de sesión para tener el estado más reciente de tareas/roadmap
6. NUNCA confiar en datos de memoria sin verificar contra los archivos fuente
