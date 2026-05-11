# Gemini 3 Pro Image — Prompt Structure (Anti-Leak Pattern)

**Fecha:** 2026-04-22 (MG batch BATCH_MG_2026-04-22-v1, 30 imgs)
**Aplica a:** cross-client (HC, LF, GR, MG, GIBRAN) cuando se renderea via `gemini-3-pro-image-preview` API.

## Problema

En prompts monolíticos (specs + copy + scene inline), el modelo renderiza como texto visible:
- Specs tipográficas: "Inter SemiBold 600, 14pt, uppercase, tracking +0.25em"
- Opacidades: "50%", "70%", "30%"
- Coordenadas de layout: "80px wide", "bottom-right"
- Caracteres meta: `« »` angle quotes alrededor de strings que solo marcaban "render este texto"
- Logos inventados si no se adjunta el logo real como imagen

## Fix canónico (4-block prompt + system_instruction + logo-first)

### 1. Prompt con 4 bloques separados

```
=== TEXT CONTENT (render EXACTLY these strings, nothing more, nothing less) ===
- STRING 1
- STRING 2

=== VISUAL SCENE ===
<descripción visual del setup, iluminación, composición>

=== STYLE GUIDE (internal — DO NOT render as text) ===
<typography specs, color codes, opacity values, layout coordinates>

=== DO NOT ===
- Do NOT render typography specifications as visible text
- Do NOT render percentage numbers like "50%", "70%", "30%"
- Do NOT render the angle quotes « » around any text
- Do NOT invent a logo; copy exactly the attached logo

=== CANVAS ===
1080x1350 px (4:5 IG portrait). No people, no emojis, no additional text.
```

### 2. `system_instruction` en `GenerateContentConfig`

```python
SYSTEM_INSTRUCTION = """You are a senior art director producing premium images.
STRICT RULES (non-negotiable):
1. ONLY render text that appears inside the === TEXT CONTENT === block.
2. NEVER render as visible text: typography specifications, color codes, layout coordinates, meta-labels.
3. LOGO: the first attached image is the OFFICIAL logo — copy it EXACTLY. Do NOT invent.
4. Follow the brand palette.
5. If user prompt uses « » around text, render WITHOUT those characters."""

config = types.GenerateContentConfig(
    response_modalities=["IMAGE"],
    system_instruction=SYSTEM_INSTRUCTION,
)
```

### 3. Logo como PRIMERA imagen attached

```python
parts = [load_image_part(LOGO)]  # ← logo FIRST
for ref in attachments:
    parts.append(load_image_part(ref))
parts.append(types.Part.from_text(text=prompt_text))
```

Sin logo attached, el modelo alucina el isotipo + typos de wordmark. Con logo attached + rule explícita en system_instruction + DO NOT forbidding invention, lo copia 1:1.

## Resultado validado

- 14 imgs MG-006/007/008 regeneradas: leaks eliminados.
- 16 imgs MG-009/010/011/012 generadas clean desde inicio.
- 30/30 OK, ~$1.20 USD cost.
- Único micro-leak residual: 1 backtick `` ` `` (MG-011 S3 v1) — edge case cosmético.

## Reference scripts

- `/tmp/mg_gen/rerun_clean.py` (MG-006/007/008)
- `/tmp/mg_gen/rerun_clean_009_012.py` (MG-009/010/011/012) — incluye fix `"50%" / "70%" / "30%"` explícito en DO NOT.

## Cuándo aplicar

**Siempre** que se use Gemini API para generar imágenes con texto overlay. Si es web UI (default per memoria `feedback_gemini_workflow_semi_auto.md`), el patrón también ayuda pero es menos crítico porque Gibran puede iterar manualmente.

## Folder structure estándar (factory)

```
RESOURCES/{POST_ID}/FINAL/v1/{naming}.png
RESOURCES/{POST_ID}/FINAL/v2/{naming}.png
RESOURCES/{POST_ID}/FINAL/_legacy/  (runs anteriores con leaks)
```

Antes era flat `{naming}_v{n}_clean.png`. v1/v2 folders dejan espacio para v3/v4 si hay que iterar.
