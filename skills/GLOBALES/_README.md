# _SKILLS_TEMPLATES

## Propósito
Lógica genérica de skills reutilizables. Cada subcarpeta contiene un `SKILL.md` con variables `{{PLACEHOLDER}}` que se resuelven leyendo el `client-config.json` del cliente.

## Tipos de archivo aceptados
- `SKILL.md` — Lógica de la skill con variables genéricas
- `config.template.json` — Template de configuración para clonar al cliente
- `scripts/` — Scripts Python/JS auxiliares de la skill
- Recursos de referencia (.md, .json)

## Convención de nombres
Cada skill tiene su propia subcarpeta con nombre en kebab-case: `meta-upload/`, `image-creator/`, etc.

## NO va aquí (redirigir a)
- `client-config.json` con valores reales → `[CLIENTE]/_SKILLS/[skill]/`
- Archivos `.skill` empaquetados → `[CLIENTE]/06. CLAUDE SKILLS/CURRENT VERSIONS/`
- Scripts compartidos entre skills → `../_SHARED_RESOURCES/`

## Notas
- Este es el SOURCE OF TRUTH de la lógica de cada skill.
- Nunca editar la lógica en la carpeta del cliente. Siempre editar aquí.
- Al actualizar un template, regenerar el `.skill` file correspondiente.

## Skills disponibles (v1.0+)

| Skill | Propósito | Inputs | Output |
|---|---|---|---|
| `campaign-architecture-pdf` | PDF visual A3 panorámico de arquitectura de campaña (campañas → ad sets → ads con thumbnails + landings). Placeholders automáticos para creativos pendientes. | JSON (schema en `templates/schema.md`) | PDF multi-page |
| `gemini-image-gen` | Genera imágenes social media con Gemini API usando mockups como refs. | Visual Rules + briefs | PNG 4:5 |
| `carousel-generator` | Genera carruseles HTML/CSS renderizados con Playwright | Briefs slides | PNG 1:1 |
| `content-planner`, `batch-producer`, `reel-scripter`, `single-post-generator` | Producción de contenido social | Brief + calendar | Posts listos |
