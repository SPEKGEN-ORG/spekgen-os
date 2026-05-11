# Workflow 03 — Brief batch (Miércoles)

> Trigger: cada miércoles ~10 AM MX. Output: brief conceptual del batch siguiente + handoff a `/factory-batch`.

---

## Objetivo

Producir un brief de 6-8 ads para que `/factory-batch` arranque el jueves QA y viernes upload. **No genera imágenes**, solo conceptualiza: ad_code → producto → bucket → PDA → hipótesis testeable.

## Pre-flight

Cargar (orden estándar):
1. `_QUICK_REFERENCE.md`
2. `LOGS/LF/CALIBRATION.md`
3. `LOGS/LF/DECISIONS_LOG.md` últimas 2 semanas — qué se pausó/escaló/refresheó
4. `LOGS/LF/BATCH_LOG.md` — qué ads activos hay (no duplicar Entity ID)
5. `LOGS/LF/MONTH_PLAN_MAY26.md` — semana toca, gaps por bucket
6. `LOGS/LF/PROMPT_PATTERNS_LF.md` — patrones validados ≥3 ads / anti-patterns
7. `LOGS/LF/VOC_MINING.md` — PDAs `unused` del workflow 02
8. `LOGS/LF/AUDITS/audit_LATEST.md` — bandera de necesidades del workflow 01

## Procedimiento

### Paso 1 — Resolver el mix de la semana

Mirar MONTH_PLAN week activa:
- ¿Qué ad_codes están planeados? (ej. LF-066 a LF-072)
- ¿Algún cambio en la bandera del audit del lunes? (refresh creative, bucket bandera, kills)
- ¿Hay overrides justificados por data 7d? Loggear en `MONTH_PLAN.md` sección Overrides.

Mix final: lista 6-8 (ad_code, producto, bucket, adset destino).

### Paso 2 — Asignar PDAs del VoC mining

Para cada ad del mix, asignar 1 PDA `unused` (o `validated` si replicar winner). Si faltan PDAs disponibles → bandera de gap para workflow 02 próximo martes.

Ad sin PDA = no producir. Mejor 5 ads buenos que 8 con conceptos forzados.

### Paso 3 — Pricing pre-flight

```bash
python3 /path/to/factory-batch/scripts/validate_batch.py {batch_dir} --pricing-check --client LF
```

Ah — el batch aún no existe. Workaround: hacer el pricing check **mental** contra `LF_PRICING_REFERENCE.xlsx` (hoja SINGLES_WITH_PACKS). Para cada producto del mix:
- Confirmar precio single + Pack 2 + Pack 4 vigentes
- Confirmar stock=YES (sino → cambiar producto)
- Si menciona compare_at story → confirmar compare_at sigue activo en Shopify

### Paso 4 — Init batch via /factory-batch

```bash
python3 /path/to/factory-batch/scripts/init_batch.py --type ads --client LF --batch-id BATCH_LF_2026-05-XX-v1
```

Esto crea folder + skeleton. Claude (en chat) llena `batch.json` con 6-8 entries. Cada entry incluye:
- `ad_code` (siguiente número disponible LF-NNN)
- `client`, `format` (bucket exacto del `_buckets/LF.json`)
- `destination_adset`
- `product` (del catálogo, con precio si aplica)
- `concept_angle` (1-2 líneas — VoC literal del PDA)
- `entity_id_signature` (string compuesto que distingue de batches previos)
- `aspect_ratio: 4:5`
- `objective` (qué KPI esperamos)
- `hook_text_on_image` (literal — del VoC)
- `gemini_prompt` (SCALIST completo — 7 bloques)
- `extra_attachments` (paths a RESOURCES/{ad_code}/)
- `ad_copy` (primary_text, headline, description, cta_type, landing_url con UTMs)
- `expected_outcome` (hipótesis testeable: "ROAS ≥X / CPA ≤Y / Hook ≥Z%")
- `status: DRAFT`

### Paso 5 — Validate batch

```bash
python3 /path/to/factory-batch/scripts/validate_batch.py {batch_dir} --pricing-check --client LF
```

Si pasa: ✅ confirma que pricing cuadra + schema válido. Si falla: corregir antes de avanzar.

### Paso 6 — Generate dashboard

```bash
python3 /path/to/factory-batch/scripts/generate_dashboard.py {batch_dir}
```

(El init_batch v3 ya lo hace automático, pero re-correr si batch.json se modificó después.)

### Paso 7 — Handoff a workflow 04 (jueves)

Output del workflow 03:
- `batch_dir` con `batch.json` completo + dashboard.html generado + RESOURCES/ pre-poblada con attachments necesarios
- `/factory-batch` listo para Fase 4 (Web UI Gemini generation) por Gibran o team member el jueves

Mensaje a Gibran: "Brief listo para BATCH_LF_2026-05-XX-v1. {N} ads conceptualizados. Cuando puedas, abre el dashboard en :8766 y empieza generación."

## Edge cases

- **Layer 1 del lunes flagged un loser nato en bucket X**: NO incluir más ads del bucket X esta semana — bandera de override en MONTH_PLAN. Re-evaluar el bucket entero.
- **Cuenta hemorrágica en audit lunes** (ROAS 7d <breakeven): batch debe ser conservador — NO experimentar wildcards, doblar receta del top performer.
- **Stock de producto crítico (winner) cae a 0**: bandera URGENTE para Gibran — substituir o postponer el batch.

## Output esperado

1. `BATCH_LF_2026-05-XX-v1/batch.json` con 6-8 entries
2. `BATCH_LF_2026-05-XX-v1/dashboard.html` regenerado
3. Append a `MONTH_PLAN.md` Overrides si hubo
4. Mensaje breve a Gibran handoff
