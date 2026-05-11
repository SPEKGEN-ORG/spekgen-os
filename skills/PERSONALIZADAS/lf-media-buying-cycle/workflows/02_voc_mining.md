# Workflow 02 — VoC Mining (Martes)

> Trigger: cada martes ~10 AM MX. Output: 2-3 ángulos PDA nuevos appended a `LOGS/LF/VOC_MINING.md`.

---

## Objetivo

Extraer Voice-of-Customer (VoC) fresco para alimentar el brief del miércoles. **Sin VoC fresca, los prompts del miércoles repiten ángulos saturados.** Brain §3 dice creatividad ES segmentación — y la creatividad sale del lenguaje exacto del cliente.

## Pre-flight

Cargar (orden estándar):
1. `_QUICK_REFERENCE.md`
2. `LOGS/LF/CALIBRATION.md`
3. `LOGS/LF/VOC_MINING.md` — qué VoC ya tenemos (no duplicar)
4. `LOGS/LF/MONTH_PLAN_MAY26.md` — qué buckets toca alimentar esta semana

## Fuentes de VoC priorizadas (en orden)

1. **GHL conversations LO FITNESS** (últimos 7d) — DMs/WhatsApp/Email frescos. Más rico VoC porque es 1:1.
2. **Comentarios en ads activos** (últimos 7d Meta API) — reacciones públicas, "this is me" moments.
3. **Reviews Shopify** (productos top de la semana) — post-purchase voice.
4. **Reels orgánicos comments** (top engagement últimos 14d) — discovery-stage VoC.
5. **Webinar Q&A transcripts** (si hubo webinar reciente) — objections + decision triggers.

## Procedimiento

### Paso 1 — Pull GHL conversations
Usar GHL MCP `mcp__ghl__search_conversations` con `location='LF'`, ventana últimos 7d. Filtrar por mensajes inbound (cliente → marca, no auto-replies).

Para cada conversación significativa, extraer literal (en lenguaje del cliente):
- **Pain**: ¿qué problema describe? (con palabras exactas)
- **Desire**: ¿qué solución busca? (con palabras exactas)
- **Objection**: ¿qué freno o duda menciona? (precio, sabor, dosis, autoridad, etc.)
- **Trigger**: ¿qué momento de vida lo trajo? (post-pandemia, edad, recomendación de amiga, etc.)

### Paso 2 — Pull comments Meta
Usar Meta API `/{ad_id}/comments` para top 5 ads por engagement últimos 7d. Extraer comentarios sustantivos (>5 palabras, no emoji-only). Mismo formato P/D/O/T.

### Paso 3 — Sintetizar 2-3 PDA nuevos

PDA = Persona × Deseo × Awareness level (Schwartz). Format:

```
PDA #N (YYYY-MM-DD)
- Persona: mujer 38-50 que entrena pero no baja peso, post-perimenopausia
- Pain literal: "no es falta de disciplina, es biología" (de comment LF-063 o de DM #G45)
- Desire literal: "quiero un reset que NO sea otra dieta más"
- Awareness: 2 (Problem-Aware) — sabe el problema pero no la solución
- Bucket sugerido: PROBLEM-SOLUTION o LUPITA+AUTHORITY
- Producto sugerido: MetaFIT
- Hook gold (literal): "Después de los 35 tu cuerpo no falla — se adapta"
- Source: GHL convo #M2891 (2026-05-04) + comment LF-063 (2026-05-08)
```

### Paso 4 — Append a `VOC_MINING.md`

Append-only. Tagear cada PDA con:
- **Status**: `unused` (nuevo, no usado en ningún ad) | `in_use` (ad N activo) | `validated` (ROAS ≥breakeven) | `failed` (ROAS <0.5×)
- **Used in**: `LF-NNN` (cuando se use en ad)

### Paso 5 — Bandera para brief del miércoles

Cierre del workflow: lista de PDAs `unused` listos para ser baseados en el brief del workflow 03.

```
PDAs disponibles para brief Wed 2026-05-XX:
- PDA #14 (PSS, MetaFIT, ya validado parcial en LF-063)
- PDA #15 (PSS, FitMax, NUEVO — gap a llenar en LF-070)
- PDA #16 (LUPITA+AUTH, Magnesio, NUEVO — para LF-068)
```

## Edge cases

- **Pocas conversaciones GHL** (<5 inbound): bajar el bar — usar incluso convos cortas. Suplementar con comments Meta.
- **VoC repetitiva**: bandera para investigar — quizás el ICP necesita ampliarse (cohorte nueva).
- **Lenguaje del cliente NO se parece al brand voice**: NO forzar — el brand voice se ajusta al cliente, no al revés. Loggear divergence en `CALIBRATION.md`.

## Output esperado

1. Append a `LOGS/LF/VOC_MINING.md` con 2-3 PDAs nuevos formato fijo
2. Bandera de PDAs disponibles para workflow 03 del miércoles

## Próxima ejecución scheduled

Cada martes 10 AM MX (cron `lf-tuesday-voc.yml` futuro). Por ahora manual.
