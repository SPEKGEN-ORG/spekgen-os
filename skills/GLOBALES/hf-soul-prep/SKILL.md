---
name: hf-soul-prep
description: Pipeline para entrenar un Soul ID en Higgsfield (producto o persona). Genera 8 mockups premium en Gemini Nano Banana Pro como inputs de training, sube a Higgsfield CLI, entrena Soul 2.0, registra en _SOUL_REGISTRY. Reusable para 15+ Souls cross-client (HC/GR/LF/MG productos + marcas personales). Workflow team-friendly con dashboard HTML local. Activar cuando Gibran diga "entrena un soul de X", "soul de [producto]", "vamos a hacer un soul", "prepara soul training", "soul prep para [cliente]", "/hf-soul-prep".
---

# /hf-soul-prep — Soul Training Pipeline para Higgsfield

Pipeline end-to-end para entrenar Soul IDs (producto o persona) en Higgsfield. Una vez entrenado, un Soul permite generar contenido infinito con el sujeto idéntico y consistente (imagen + Soul Cast video a 0.12c por gen).

**Diseñado para que cualquier miembro del equipo lo ejecute sin training previo.** Dashboard HTML local con copy buttons, attachments pre-organizados por prompt, status tracking automático.

## Cuándo invocar

- "entrena un soul de [producto/persona]"
- "soul de ArtriDog/DogRelax/Gibran/etc"
- "vamos a hacer un soul de X"
- "prepara soul training"
- "soul prep para [cliente]"

## Pre-requisitos

- Higgsfield CLI instalado y autenticado (`higgsfield auth token` debe responder OK)
- Créditos Higgsfield suficientes (Soul 2.0 training: costo a verificar pre-flight)
- Cuenta Google One Pro activa (Gemini Nano Banana Pro web UI = gratis)
- Reference image(s) del sujeto: mockup 3D del producto, foto frontal de la etiqueta, o fotos limpias de persona
- Python 3 + Pillow opcional para validación (`pip3 install Pillow`)

## Estructura de la skill

```
~/.claude/skills/hf-soul-prep/
├── SKILL.md                    ← este archivo
├── _SOUL_REGISTRY.md           ← catálogo cross-batch de Souls entrenados
├── templates/
│   ├── PROMPT_PACK_PRODUCT.json   ← 8 SCALIST prompts producto + placeholders
│   └── PROMPT_PACK_PERSON.json    ← 8 SCALIST prompts persona + placeholders
└── scripts/
    ├── init_batch.py           ← crea batch dir + batch.json + carpetas
    ├── generate_dashboard.py   ← sync attachments + render dashboard.html
    ├── serve_dashboard.py      ← server local :8767 con auto-regen
    ├── validate_batch.py       ← valida outputs antes de training
    └── train_soul.py           ← upload + soul-id create + registry update
```

## Workflow (5 fases)

### Fase A — Init batch (Claude ejecuta)

1. Decidir ubicación del batch:
   - **Producto:** `{CLIENTE}/.../{PRODUCTO}/04. MOCK UPS/SOUL_TRAINING_BATCH/`
   - **Persona:** `SPK - 12. SOCIAL MEDIA/{PERSONA}/SOUL_TRAINING_BATCH/`
2. Construir `specs.json` temporal con `subject_name`, `client`, `soul_model`, y todos los placeholders del template (PRODUCT_NAME, BRAND_NAME, COLOR_PALETTE, etc. — el template indica los `placeholders_required`).
3. Ejecutar:
   ```bash
   python3 ~/.claude/skills/hf-soul-prep/scripts/init_batch.py \
     "{batch_dir}" --type product --specs /tmp/specs.json
   ```
4. Crea estructura:
   ```
   SOUL_TRAINING_BATCH/
   ├── batch.json              ← source of truth
   ├── _SOUL_INFO.md           ← human readable metadata
   ├── PROMPTS.md              ← backup legible de los 8 prompts ya substituidos
   ├── REFERENCE/              ← (vacío — copiar refs aquí)
   ├── ATTACHMENTS/            ← (vacío — se puebla en Fase B)
   │   ├── 01_hero_3_4/
   │   ├── 02_frontal/
   │   ├── 03_macro_label/
   │   └── ...
   └── OUTPUTS/                ← (vacío — PNGs de Gemini van aquí)
   ```
5. Copiar reference image(s) del sujeto a `REFERENCE/` (mockup 3D + label PDF para producto, o 3-5 fotos para persona).

### Fase B — Generar 8 mockups (equipo ejecuta via dashboard)

1. Claude levanta el dashboard:
   ```bash
   python3 ~/.claude/skills/hf-soul-prep/scripts/serve_dashboard.py "{batch_dir}"
   ```
   Abre browser en `http://127.0.0.1:8767/`. Cada GET regenera el dashboard sincronizando `REFERENCE/` → `ATTACHMENTS/0N_*/` y detectando outputs descargados.

2. **Equipo ve dashboard con onboarding embebido** y 8 cards:
   - Status badge (PENDIENTE / COMPLETADO / DROPPED)
   - Thumbnails de attachments del prompt
   - Botón **📋 COPIAR** del prompt SCALIST
   - Output filename esperado (ej. `01_hero_3_4.png`)
   - Score input (1-10)
   - Preview del PNG cuando se descarga

3. **Por cada card:**
   - Click **COPIAR** → paste en `gemini.google.com` (modelo Gemini 3 Pro Image / Nano Banana Pro)
   - Drag&drop la carpeta `ATTACHMENTS/0N_slug/` entera al input de Gemini
   - Generar, iterar hasta score ≥8/10
   - Quitar watermark de Gemini (Photoshop / Canva / Photopea)
   - Guardar PNG con el filename exacto en `OUTPUTS/`
   - Ingresar score en el campo de la card → recargar browser → status flip a ✓ COMPLETADO

4. **Mínimo aceptable:** 5/8 con score ≥8. Ideal: 8/8.

### Fase C — Validate + Upload + Train (Claude ejecuta)

1. Validar batch:
   ```bash
   python3 ~/.claude/skills/hf-soul-prep/scripts/validate_batch.py "{batch_dir}"
   ```
   Checks: ≥5 outputs, PNGs legibles, aspect ratio 1:1, score promedio ≥8.

2. Si validation pasa → ejecutar training:
   ```bash
   python3 ~/.claude/skills/hf-soul-prep/scripts/train_soul.py "{batch_dir}"
   ```
   Ejecuta:
   - Upload de cada PNG a Higgsfield (captura `upload_id`)
   - `higgsfield soul-id create --name {SUBJECT} --soul-2 --image <ids...>`
   - Polling `higgsfield soul-id wait <soul_id>` (5-15 min)
   - Update `batch.json` con `soul_id`, `cost_credits`, `elapsed_seconds`
   - Append fila a `_SOUL_REGISTRY.md` (skill home)

### Fase D — Test gen (Claude ejecuta)

Generar 2-3 imágenes test con el Soul para validar fidelidad:

```bash
higgsfield generate create text2image_soul_v2 \
  --prompt "{SUBJECT} on a marble surface, golden hour, cinematic" \
  --soul-id <soul_id>
```

Si fidelidad <80% (cara/etiqueta deformada):
- Re-train con más imágenes (hasta 20)
- Re-train con imágenes de mayor calidad
- Cambiar entre `--soul-2` (preserva geometría) y `--soul-cinematic` (drift estético)

### Fase E — Cierre (Claude ejecuta)

Update fila en `_SOUL_REGISTRY.md` con `fidelity_score` observado en test. Update memoria del proyecto si hubo lecciones.

## Decisiones documentadas

- **Gemini para mockups, Higgsfield solo para Soul:** Gemini Nano Banana Pro web UI es gratis con Google One Pro y rinde calidad equivalente a FLUX/Cinematic Studio. Reservamos créditos Higgsfield para training.
- **Soul 2.0 default para productos:** preserva geometría/etiqueta. Soul Cinematic introduce drift estético — bueno para retratos, malo para packshot.
- **Aspect ratio 1:1 obligatorio:** evita que Soul aprenda distorsiones. Después generamos 4:5/9:16/16:9 con Soul ya entrenado.
- **8 mockups como número óptimo:** rango Higgsfield es 5-20, 8 es punto dulce calidad/tiempo.
- **Dashboard local en :8767:** no choca con `/factory-batch` :8766. Auto-regen on GET para que el equipo vea status flip sin restart.
- **Attachments per-prompt copiados, no symlinkeados:** ~8MB extra por batch pero portable + visible en Finder.

## Anti-patterns (no hacer)

- ❌ Entrenar con menos de 5 imágenes (quality severamente comprometida)
- ❌ Entrenar con outputs de baja calidad (Soul aprende los defectos)
- ❌ Mezclar productos/personas distintos en un mismo Soul
- ❌ Saltarse Identity Lock prefix en los prompts (sale producto/cara distinta)
- ❌ Usar Higgsfield para generar los mockups iniciales (quema créditos — Gemini lo hace gratis)
- ❌ Editar `batch.json` a mano (usar dashboard inputs + scripts)
- ❌ Subir PNGs con watermark de Gemini (Soul los aprende para siempre)

## Lecciones acumuladas (append por batch)

- (vacío — primer run real será ArtriDog HC, 2026-05-07)

## Referencias

- Higgsfield CLI: `higgsfield --help`
- Gemini Nano Banana Pro: https://gemini.google.com (selector arriba del prompt)
- SCALIST framework: `SPK - SPEKGEN AGENCY/SPK - MEDIA BUYING OPS/DIGESTS/05_GEMINI_REALISM_DIGEST.md`
- Templates legacy (.md): `_archive_md_templates/` (deprecados 2026-05-07, reemplazados por JSON estructurado)
