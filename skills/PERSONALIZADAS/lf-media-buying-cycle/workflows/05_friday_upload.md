# Workflow 05 — Friday upload + activation (Viernes)

> Trigger: Viernes ~10 AM MX, post QA workflow 04 con `status: READY_FOR_UPLOAD` en todos los ads.
> Output: ads UPLOADED + ACTIVE en Meta + cascade activation + recap PDF + DECISIONS_LOG entry.

---

## Objetivo

Subir el batch a Meta Marketing API + activar en cascade (ads → adsets → campaigns) + actualizar todos los logs + generar recap PDF + handoff a monitoring.

## Pre-flight obligatorio

Cargar:
1. `_QUICK_REFERENCE.md`
2. `LOGS/LF/AUTONOMY_RULEBOOK.md` — autoridad confirmada
3. `LOGS/LF/CALIBRATION.md` — verificar budget cuenta no excedido
4. `LOGS/LF/DECISIONS_LOG.md` — historia
5. **Verificar que NO es sábado/domingo** (lockdown Brain). Si es lockdown weekend → POSTPONER al lunes.

## Procedimiento

### Paso 1 — Verificación final batch

```bash
python3 /path/to/factory-batch/scripts/validate_batch.py {batch_dir} --pricing-check --client LF --strict-v3
```

Esperar `✅ OK`. Si falla → STOP, regresar a workflow 04.

### Paso 2 — Upload via Meta Marketing API

Usar el script de upload (basado en `/spekgen-meta-ads-upload` skill rules). Por cada ad con `status: READY_FOR_UPLOAD`:

1. **Upload imagen** → `POST /act_{ad_account}/adimages` con `filename: FINAL/{ad_code}.png` → captura `image_hash`
2. **Crear creative** → `POST /act_{ad_account}/adcreatives` con `object_story_spec` que incluye `instagram_user_id` INSIDE (skill rule #1+2). NO usar `degrees_of_freedom_spec` (deprecated 2026-05). NO usar `instagram_actor_id` (rejected by system user tokens).
3. **Crear ad** → `POST /act_{ad_account}/ads` en `adset_id` correspondiente al `destination_adset` del entry. Status inicial: `PAUSED`.
4. Append `meta_ad_id`, `meta_creative_id`, `meta_image_hash` al entry en `batch.json`. Status: `UPLOADED_PAUSED`.

Si algún ad falla upload:
- Loggear error en `DECISIONS_LOG.md`
- Continuar con los demás (no bloquear todo el batch por 1 fail)
- Bandera para retry post-cascade

### Paso 3 — Verificación IG dropdown attached

Por cada creative recién creado, query:
```
GET /{creative_id}?fields=object_story_spec
```
Verificar `object_story_spec.instagram_user_id` existe. Si no → fix con `POST /{creative_id}` con `instagram_user_id` correcto. Skill rule #1.

### Paso 4 — Activation cascade (orden importante)

Orden:
1. **Ads (los nuevos) → ACTIVE**: cada ad creado via `POST /{ad_id}` con `status: ACTIVE`
2. **Adsets → ACTIVE**: solo los que reciben ads nuevos. Los que quedan vacíos (ej. D_WILDCARDS si no hay ads de wildcard) quedan PAUSED.
3. **Campaigns → ACTIVE**: si no estaban activas

Si Meta rechaza activación de adset por "Minimum Spend Limit Is Higher Than Campaign Budget" (error 1885648):
- Sumar `daily_min_spend_target` de todos los adsets del campaign
- Si suma > 80% del campaign daily_budget → bajar floor de los adsets a (campaign_budget × 0.6 ÷ N_adsets), o subir campaign budget
- Loggear como D-NNN calibración en CALIBRATION.md
- Reintentar activación

### Paso 5 — Update logs

```bash
# Regenerar BATCH_LOG con bloques A+B+C completos (ahora hay meta_ad_ids)
python3 /path/to/factory-batch/scripts/generate_batch_log.py {batch_dir} --block ABC

# Generar recap PDF whiteboard
python3 /path/to/factory-batch/scripts/build_recap_pdf.py {batch_dir} --format whiteboard
```

Append a `DECISIONS_LOG.md` D-NNN canónico:
- Cambio: upload + activation cascade del batch
- Justificación: (citar workflow 03 brief + workflow 04 QA OK)
- Hipótesis: (qué esperamos del batch — ROAS, CPA, % de bucket validation)
- Métrica de éxito: 72h Layer 1 + 7d Layer 2
- Riesgo: Learning Phase reset por N ads simultáneos. Mitigación.

### Paso 6 — Reveal recap + email handoff

```bash
open -R {batch_dir}/{batch_id}_recap.pdf  # reveal en Finder
```

Mensaje a Gibran: "Batch live + recap PDF generado. Próximo checkpoint: 72h pull jueves YYYY-MM-DD via workflow 06."

### Paso 7 — Lockdown weekend

NO touchear nada hasta lunes. Brain §4 hard rule.

## Edge cases

- **Meta API down/rate-limited**: backoff exponencial 3×. Si sigue fallando → POSTPONER upload al lunes (NO viernes EOD).
- **Ad rejected por policy** (ej. claim médico flagged): leer rejection reason → si fixable en copy, fix + re-upload. Si no, mover ad a status `BLOCKED_POLICY` y excluir.
- **Budget cuenta llegó a $333/d ceiling con campañas previas**: bandera URGENT a Gibran — escalar arriba del rulebook NO sin permiso.
- **IG dropdown vacío post-creative-create** (skill rule #1 fail): refetch creative, fix con `POST /{creative_id}` setear `instagram_user_id` directo.

## Output esperado

1. N ads UPLOADED + ACTIVE en Meta
2. `batch.json` actualizado con todos los meta_ad_ids
3. `BATCH_LOG.md` regenerado con bloques A+B+C
4. `{batch_id}_recap.pdf` generado + revealed en Finder
5. `DECISIONS_LOG.md` D-NNN appended
6. Mensaje handoff a Gibran
7. Trigger automático del workflow 06 a 72h (lunes/martes según día de upload)
