---
name: Scheduled tasks are unreliable — need visible logs
description: Scheduled tasks fail silently, expire, or don't run when computer is off. Need visible execution logs.
type: feedback
---

Las scheduled tasks de Claude Code han sido poco confiables. Múltiples intentos de configuración, pero nunca parecen ejecutarse correctamente.

**Why:** Gibran ha intentado configurar tareas programadas varias veces (hc-morning-intelligence, hc-pipeline-watcher, etc.) pero: (1) fallan silenciosamente sin log visible, (2) no se ejecutan si la computadora está apagada, (3) expiran después de 7 días, (4) no hay archivo visible con los entries de ejecuciones pasadas.

**How to apply:**
1. Antes de crear una scheduled task, explicar sus limitaciones: solo funciona con Claude Code abierto, la computadora encendida, y expiran en 7 días
2. Si una tarea es crítica, considerar alternativas más robustas (Google Apps Script cron, GitHub Actions, n8n) en vez de scheduled tasks de Claude
3. Cuando se cree una scheduled task, crear también un archivo de log visible (markdown o txt) donde se registre cada ejecución exitosa con timestamp y resumen
4. No asumir que una scheduled task funciona solo porque se creó — verificar que realmente se ejecutó
5. Ser honesto sobre qué se puede y qué NO se puede automatizar con las herramientas actuales
