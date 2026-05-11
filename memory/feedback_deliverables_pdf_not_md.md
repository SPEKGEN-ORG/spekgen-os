---
name: Entregables importantes en PDF visual, no en MD
description: Los documentos estratégicos/operativos importantes deben entregarse como PDFs visuales, no como archivos .md
type: feedback
---

Los archivos importantes (matrices estratégicas, planes, propuestas, reportes, documentos de alineación con el cliente o internos clave) deben entregarse como **PDFs visuales**, no como archivos markdown.

**Why:** Gibran quiere documentos que se vean profesionales y se puedan leer/compartir sin abrir un editor. Los .md son para memoria interna de Claude y notas de contexto, no para deliverables operativos que él necesita consultar o compartir.

**How to apply:**
- Planes estratégicos, matrices, roadmaps → PDF con formato visual (usar skill `/pdf` o generar con docx/pptx → exportar PDF)
- Documentos de un solo vistazo (tablas, matrices, KPIs) → PDF horizontal tipo dashboard
- Los .md siguen siendo válidos para: memoria interna, _CLIENT_CONTEXT, _KNOWLEDGE_BASE, CLAUDE.md, notas técnicas, SOPs que Claude lee
- Regla rápida: si es un entregable que Gibran va a mirar o mandar → PDF. Si es algo que Claude lee para operar → MD está bien.
- Cuando entregue un PDF, incluir comando `open` clickable
