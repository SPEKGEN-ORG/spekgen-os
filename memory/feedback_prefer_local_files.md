---
name: Prefer local files over Vercel/Supabase
description: Gibran prefers xlsx/docx/sheets over web dashboards. Only use Vercel/Supabase if absolutely necessary AND with SOPs.
type: feedback
---

Preferir archivos locales (xlsx, docx, Google Sheets) sobre dashboards web (Vercel, Supabase, Next.js apps).

**Why:** El Content Hub en Vercel ha sido una fuente de frustración. Claude construye mucho ahí, hace muchos cambios, pero Gibran ve el dashboard peor e incompleto cada vez. Gibran no sabe usar, manejar, ver o editar Vercel ni Supabase. Se pierde mucho tiempo construyendo cosas que no sirven ni son accesibles para él.

**How to apply:**
1. Para datos operativos (ad logs, product logs, métricas) → usar xlsx o Google Sheets como fuente de verdad
2. Para documentos → usar docx o markdown
3. Solo usar Vercel/Supabase si es estrictamente necesario (por ejemplo, un portal de cliente que necesita ser web)
4. Si se usa infra web, crear "views" ligeros que reflejen un archivo base (el xlsx es la fuente, el view solo muestra)
5. Si se DEBE usar Vercel/Supabase → OBLIGATORIO crear SOPs con instrucciones paso a paso para que Gibran pueda ver, editar y manejar
6. Nunca construir features en el dashboard sin que Gibran pueda verificar que funcionan
7. Antes de tocar el Content Hub, preguntar: "¿Esto se puede resolver con un archivo local?"
