# Workflow 04 — QA pre-upload (Jueves)

> Trigger: cuando todos los ads del batch tengan `final_image_path` poblado en `batch.json` (es decir, todas las imágenes Web UI generadas y guardadas en FINAL/).
> Output: batch validado para upload viernes, o lista de fixes pendientes.

---

## Objetivo

Última verificación antes del upload Meta. Brain §3 + EMQ audit. **Cualquier issue detectado aquí es 100× más barato que detectado post-launch.**

## Pre-flight

Cargar:
1. `_QUICK_REFERENCE.md` — section "Check antes de generar imagen Gemini"
2. `LOGS/LF/PROMPT_PATTERNS_LF.md` — anti-patterns documentados
3. `_brand_rules/LF.md` — reglas hard NEVER/ALWAYS

## Procedimiento

### Paso 1 — Validar shape del batch

```bash
python3 /path/to/factory-batch/scripts/validate_batch.py {batch_dir} --pricing-check --client LF --strict-v3
```

Esperar: `✅ OK — batch válido`. Si hay errores → fix antes de avanzar.

### Paso 2 — QA visual por imagen (Claude lee cada FINAL)

Para cada ad con `status: READY_FOR_UPLOAD`:

```bash
# Claude usa Read tool sobre {batch_dir}/FINAL/{ad_code}.png
```

Por cada imagen, evaluar checklist:

| Check | Pass / Fail |
|---|---|
| Identity Lock OK (cara persona = reference) | si aplica |
| Texto en imagen es ESPAÑOL (no English leaked) | obligatorio |
| Sin watermark Gemini visible | obligatorio |
| Sin símbolos decorativos no-pedidos (sparkles, diamonds) | obligatorio |
| Anatomía correcta (manos, pies, dedos, simetría facial) | obligatorio |
| Tipografía legible + sin typos en strings | obligatorio |
| Producto: label preserved 100% (sin redesign) | obligatorio si lleva producto |
| Hook on image cuadra con `hook_text_on_image` del batch.json | obligatorio |
| Score visual estimado (texture/lighting/anatomy/typography/cohesion = X/10, promedio ≥8) | obligatorio |
| Ratio del producto/persona ocupa ≥ 30% del frame | recomendado |
| 4:5 aspect ratio respetado | obligatorio |

Si algún ad falla cualquier check **obligatorio** → bandera para regenerar.

### Paso 3 — EMQ audit (Estimated Match Quality)

Para cada ad activo, EMQ del adset destino debe ser ≥7.0 (Brain). Si <7.0:
- Pixel firing OK? Verificar test event en Meta Events Manager
- Audience match rate suficiente?
- Ajustar ad set si EMQ bajo (no bloqueante para upload, pero anota en DECISIONS_LOG)

### Paso 4 — COFEPRIS / brand voice check

Para cada `ad_copy.primary_text`:
- ¿Verbos OK? (apoya / contribuye / favorece / ayuda a)
- ¿Verbos prohibidos? (cura / elimina / garantiza / trata) — si sí → REGENERAR
- ¿Disclaimer obligatorio presente? ("Suplemento alimenticio. No sustituye una alimentación balanceada." o "No sustituye diagnóstico médico ni tratamiento.")
- ¿Tildes y ñ correctas? (Ctrl+F: año, también, más, después, calorías, energía, recuperación, articulación, inflamación)

### Paso 5 — UTMs check

Para cada `ad_copy.landing_url`:
- ¿Tiene `utm_source=meta&utm_medium=paid&utm_campaign=X&utm_content=LF-NNN`?
- ¿`utm_content` matchea `ad_code`?

### Paso 6 — Decisión

Si **todos los ads pasan**:
- Update `batch.json` `status: "READY_FOR_UPLOAD"` (si no estaba)
- Mensaje a Gibran: "Batch QA OK, listo para upload viernes"
- Handoff a workflow 05

Si **alguno falla**:
- Lista issues con fix concreto por ad
- Si fix es Gemini-side (regenerar): mensaje a Gibran "LF-XXX falló QA — necesita regenerar (razón: ...)"
- Si fix es batch.json-side (typo, copy ajuste): Claude lo arregla directo
- NO upload viernes hasta que todos pasen

## Edge cases

- **Imagen perfecta pero copy flojo**: REGENERAR copy (más barato que regenerar imagen). Update batch.json + re-validar.
- **Imagen mediocre 7.5/10 pero concepto único valioso**: decisión de Gibran. Subir si valida la hipótesis del bucket; bandera para iterar en próxima semana.
- **Discrepancia precio image vs catálogo live**: BLOQUEANTE. Re-pull catálogo, re-correr `validate_batch --pricing-check`.

## Output esperado

1. `batch.json` con status actualizado a `READY_FOR_UPLOAD` (si pasa)
2. `LOGS/LF/QA/qa_BATCH_NNN_YYYY-MM-DD.md` con checklist completado por ad
3. Mensaje handoff a Gibran (o lista de fixes)
