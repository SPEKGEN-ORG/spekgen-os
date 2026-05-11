---
name: yt-insights
description: Procesa un video de YouTube en un knowledge note + brief de contenido para @gibran.alonzo.ecom. Extrae transcript con yt-dlp, renderiza PDFs con CSS oscuro estilo SPEKGEN, append a MASTER_INDEX, crea nota Obsidian. Activate for "procesa este video", "extrae insights del video", "yt-insights URL", "analiza este YT", "/yt-insights", "saca contenido de este video", o cualquier solicitud de procesar contenido de YouTube para aprendizaje + producción de contenido en GAE.
---

# /yt-insights — YouTube → Knowledge + Content Brief

Procesa un video de YouTube en deliverables visuales (PDFs) que Gibran sí lee.

## Cuándo activar

- "procesa este video: <URL>"
- "yt-insights <URL>"
- "extrae los insights del video <URL>"
- "saca contenido de este YT"
- Pegando una URL de YouTube sin instrucciones explícitas → preguntar si quiere `/yt-insights`

## Restricciones

- **$0 de costos externos.** Solo herramientas locales (yt-dlp, ffmpeg, Playwright/chromium, Python).
- Transcript en cualquier idioma → output siempre en español.
- Si yt-dlp falla con auto-subs → pedir al usuario que pegue el transcript directo en el chat.

## Workflow (3 fases)

### Fase 1 — Extract (mecánica)

```bash
/usr/bin/python3 scripts/run.py extract <URL>
```

Esto hace:
- Slug canónico desde el título del video
- Crear carpeta `SPK - 18. YT VAULT/videos/{YYYY-MM-DD}_{slug}/`
- yt-dlp con `--write-auto-sub --write-info-json` — saca subs + chapters + metadata
- Limpiar VTT → `transcript.txt` (legible) + `transcript.srt` (con timestamps)
- Borra el VTT raw después de procesarlo
- Guardar `metadata.json` con chapters, duration, channel, etc.

**Idempotencia:** si la carpeta ya existe (mismo slug, mismo día), el script imprime `FOLDER_EXISTS: <path>` y sale con exit 3. Cuando esto pase, **preguntar a Gibran**: sobrescribir / crear `-v2` / cancelar. Re-correr según respuesta:

```bash
/usr/bin/python3 scripts/run.py extract <URL> --mode overwrite   # sobrescribe
/usr/bin/python3 scripts/run.py extract <URL> --mode version     # crea -v2, -v3, ...
```

**Sin auto-subs disponibles:** el script imprime `NEED_MANUAL_TRANSCRIPT` y exit 2. En ese caso, pedir a Gibran que pegue el transcript en el chat y guardarlo manualmente como `transcript.txt` en la carpeta del video (que sí se creó). Después continuar a Fase 2 normal.

### Fase 2 — Analyze (cognitiva, hace Claude)

Claude lee `transcript.srt` y genera dos archivos en la carpeta del video:

**`insights.md`** — knowledge note estructurado con:
- TL;DR (3-5 bullets)
- Tema central
- Lista completa de insights/tricks/conceptos numerados con timestamps
- Action items para SPEKGEN (mapeados a clientes/skills/workflows existentes)
- Aprendizajes clave (principios)
- Quotes citables con timestamp
- Backlinks Obsidian al final

**`content_briefs.md`** — brief de contenido para GAE con (REGLAS ESTRICTAS — ver memory `feedback_gae_content_voice.md`):
- ICP recordatorio (dueños $80K-500K MXN/mes que están empezando con la herramienta del video o quieren empezar)
- Ángulo dominante para el video
- **MÍNIMO 3 carruseles + 3 reels** — Gibran cura desde un menú, no aprueba/rechaza una sola opción
- Cada idea: hook desde dolor concreto + estructura + por qué encaja al ICP
- Tono "amigo compartiendo tips", NO guru
- **NUNCA** mencionar # de clientes, empleados, "agencia 99.99% AI", ni "lo estás haciendo mal"
- **NUNCA** framing de "mira cómo yo hago esto y tu no"

Claude usa los templates `templates/insights.md.j2` y `templates/content_briefs.md.j2` como referencia estructural — pero el contenido lo escribe desde el transcript, no se llena via Jinja.

### Fase 3 — Finalize (mecánica)

```bash
/usr/bin/python3 scripts/run.py finalize <slug>
```

Esto hace:
- Render `insights.md` → `insights.pdf` con Playwright + CSS oscuro SPEKGEN
- Render `content_briefs.md` → `content_briefs.pdf` mismo estilo
- Genera `_RECAP.pdf` (1 hoja real: TL;DR + títulos de las 6+ ideas con 1 línea de justificación)
- Append a `MASTER_INDEX.xlsx`
- Crea nota Obsidian en `_OBSIDIAN/04 - YT INSIGHTS/{slug}.md` con backlinks
- `open -R` del `_RECAP.pdf` en Finder

### Fase 4 — Handoff (conversacional)

Claude muestra en el chat:
- Lista compacta de los insights principales
- Las 6+ ideas de contenido (3 carruseles + 3 reels) en formato escaneable
- Pregunta cuáles aprobar para arrancar `/factory-batch --type content --client GIBRAN`

## Archivos

```
yt-insights/
├── SKILL.md                          # este archivo
├── scripts/
│   ├── run.py                        # orquestador (extract | finalize)
│   ├── _extract.py                   # yt-dlp + cleanup VTT/SRT/TXT
│   ├── _screenshots.py               # download video 480p + ffmpeg frames
│   ├── _render_pdf.py                # markdown → HTML → PDF (Playwright)
│   ├── _master_index.py              # openpyxl append
│   └── _obsidian.py                  # template Jinja → nota Obsidian
└── templates/
    ├── insights.md.j2                # estructura del knowledge note (referencia)
    ├── content_briefs.md.j2          # estructura del brief (referencia)
    ├── obsidian_note.md.j2           # nota Obsidian con backlinks
    ├── pdf_base.html.j2              # wrapper HTML para insights/briefs PDFs
    └── recap.html.j2                 # _RECAP.pdf 1-pager
```

## Reglas críticas

1. **NUNCA inventar timestamps**. Solo usar los que aparecen literal en el `transcript.srt`.
2. **Quotes citables**: copiar literal del transcript, no parafrasear.
3. **Action items para SPEKGEN**: mapear a infra existente (skills, clientes, workflows en CLAUDE.md). No proponer cosas que no existen.
4. **Top 3 ideas para GAE**: cada una con hook concreto + estructura slide-by-slide + por qué encaja al ICP. NO genéricas.
5. **CSS PDF**: oscuro estilo SPEKGEN. Background `#0F0F14`, accent purple `#8B5CF6`, mono code `#1A1A24`. Match al feed de @gibran.alonzo.ecom.
6. **Idempotencia**: si la carpeta ya existe (mismo slug), preguntar al usuario: sobrescribir / `-v2` / cancelar.
7. **Cleanup**: el video temporal en 480p se borra siempre al final, exitoso o no.

## Multi-source futuro (no ahora)

La arquitectura está pensada para extender a `--source pdf|audio|web` en v1.1. Por ahora solo YouTube.
