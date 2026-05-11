# Factory Workflow — Canonical (skill /factory-batch)

**LIVE:** 2026-04-21 tras generalizacion desde /ads-factory-batch (renombrado).
Piloto validado batch v4.1 (15 ads GR+LF+HC cross-client).

**Home unico:** `SPK - SPEKGEN AGENCY/SPK - 15. FACTORY/`
**Skill:** `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/factory-batch/`

## Cuando invocar

TODA iteracion de imagenes/contenido (ads, content organico, PDPs, prospects)
desde 2026-04-21 arranca con `/factory-batch`. No mas skills one-off.

Triggers: "batch de ads", "batch de content", "batch de pdps", "nuevo batch",
"produce ads", "produce content", "factory batch", "crea batch", "carrusel",
"post organico", "pdp images".

## Estructura factory (home)

```
SPK - 15. FACTORY/
├── ads/                          <- cross-client default (BATCH_CROSS_...)
├── content/                      <- per-client (BATCH_HC_..., BATCH_GIBRAN_...)
├── pdps/                         <- per-client-per-producto
├── prospects/                    <- agency-level
├── _intel/                       <- output /cross-client-intel
├── _strategy/                    <- STRATEGY_{CLIENTE}.md
├── _templates/                   <- dashboard base, ad_entry, schema, reference
├── _archive/                     <- batches viejos / deprecados
├── README.md                     <- mental model + comandos
└── _BIG_PICTURE_FACTORY.md
```

## Estructura skill

```
factory-batch/
  SKILL.md
  WORKFLOW.md
  scripts/
    init_batch.py       <- --type --client --product --name --date
    validate_batch.py   <- 13 campos + attachments + FINAL/ (ads schema)
    serve_dashboard.py  <- http.server 8765
```

Templates/schemas/reference **NO viven en el skill** — viven en
`SPK - 15. FACTORY/_templates/` para editarlos sin tocar skill code.

## Comando canonico

```bash
python3 scripts/init_batch.py --type ads --date 2026-05-01
python3 scripts/init_batch.py --type ads --client HC            # excepcion
python3 scripts/init_batch.py --type content --client HC
python3 scripts/init_batch.py --type pdp --client HC --product OMEGADOG
python3 scripts/init_batch.py --type prospect --name ENLACE
```

Crea `{tipo_dir}/BATCH_XXX_{fecha}-v{N}/` con `batch.json` + `dashboard.html` + `RESOURCES/`.

## Decisiones clave (todas vivas)

1. **Gemini web UI, NO API.** Gratis con Google One Pro + preserva taste gate + loop rapido.
2. **Python stdlib solo.** Sin pip installs.
3. **Cliente en nombre del batch, no en carpeta.** `BATCH_HC_...` vs `BATCH_CROSS_...`. Filtras con `ls BATCH_HC_*`.
4. **Un solo home.** `SPK - 15. FACTORY/` — NO per-client `_FACTORY/`. Simplificado despues de debate 2026-04-21.
5. **Un solo skill.** `/factory-batch` con `--type` cubre todo. Deprecados: spekgen-image-creator, pdp-image-creator, carousel-generator, single-post-generator, publish-post, spekgen-auto-image-gen, spekgen-post-producer.
6. **`/spekgen-meta-ads-upload` es fase 6 obligatoria para ads.** Nunca curl directo a Meta.
7. **Convencion stem:** `{CLIENT}-AD-{NNN}[_{VARIANT}]` sin tail concept. FINAL filename: `{stem}_{aspect}.png`.
8. **Schema ads:** 13 campos obligatorios. Un solo faltante = validator rechaza.

## Flujo 6 fases (agnostico al tipo)

1. **Brief** — Claude lee `_strategy/STRATEGY_{CLIENTE}.md` + `_intel/` si aplica. Propone mix. Gibran aprueba.
2. **Init** — `init_batch.py --type X --client Y`
3. **JSON** — Claude escribe `batch.json` con N entries. `validate_batch.py` pasa.
4. **RESOURCES** — Claude crea `RESOURCES/{stem}/` + copia attachments fisicos + `mkdir FINAL/`.
5. **Gemini loop** — Gibran: `serve_dashboard.py` → copia prompts → genera en gemini.google.com/app → quita marca de agua → guarda en `FINAL/`.
6. **Upload** — skill correspondiente: `/spekgen-meta-ads-upload` (ads), `upload_post_to_hub.py` (content HC), `/hc-pdp-builder` etc (PDPs), `/publish-prospect` (mockups).

## Debate estructura resuelto (2026-04-21)

Gibran pregunto si decentralizar (per-client `_FACTORY/` por cada cliente)
vs centralizar (todo en agency). Tras discusion:

- Pros per-client: locality, no dependency entre clientes
- Cons per-client: rompe el caso cross-client (v4.1 mixto), skill paths complicados,
  carpetas vacias esperando batches que quiza no llegan
- Decision final: **centralizado cross-client**. Razones: mismo operador
  (Gibran+Claude), misma cadencia (intel cross-client + days), mismo token Meta,
  cliente va en nombre del batch. Si eventualmente hace falta per-client se migra.

Modelo es analogo a Meta BM: un operador, multiples marcas, orchestracion unica.

## Learnings del piloto v4.1

- v1/v2/v3 deprecados a `_archive/` — micro-iso variations castigadas, copy buttons rotos, sin RESOURCES fisicos, attachment paths case-sensitive
- v4 introdujo PROMPT_RECIPE_PRODUCT_INTEGRATION + STRATEGY_{cliente}.md como context persistente
- v4.1 aprendizajes finales:
  - GR necesita multiproduct-only (0 ads activos, 60+ SKUs)
  - LF estrategia = "consolidar Lupita + ICONBAR + OFFER en un solo frame"
  - HC UGC_AUTHORITY necesita voz primera persona si MV es protagonista
  - Copy button roto = fixed con `data-attribute` + event delegation + `execCommand` fallback

## Winners referenciados

- LF-053-A LUPITA ICONBAR (ROAS 9.77x)
- LF-048 METAFIT 2PACK OFFER (ROAS 2.21x)
- LF-050 FITMAX TESTIMONIO (ROAS 3.14x)
- HC-AD-OFERTA-V2 (ROAS 9.29x)
- GR-AD-003 COLAGENO FITNESS (unico convertidor GR)

## Cost model

- Claude: ~$3-5 USD per batch (schema-driven, no deep research post-strategy MDs)
- Gemini: $0 (web UI, Google One Pro)
- Time Claude: < 3h para 15 ads
- Time Gibran: < 2h para 15 ads en Gemini
- Upload via skill: automatico

## Fase 7 — Recap PDF (OBLIGATORIO post-upload ads, 2026-04-22)

Script: `scripts/build_recap_pdf.py --batch-dir <BATCH_DIR>`.

Output: `{batch_name}_recap.pdf` en el propio batch folder. A4 landscape con:
- Matriz cobertura clientes x formatos agrupados (Oferta / Testimonial / Hero Product)
- Tabla formato x cliente: tiles con imagen FINAL + status Meta + Ad ID + link Ads Manager.
- Celdas sin ads → placeholder FALTANTE (dashed rojo) indicando qué producir en siguiente iteración.

Inputs opcionales en batch_dir:
- `_pending.json` → dict `{short_code: "razón"}` para ads `-P`.
- `_upload_log_YYYY-MM-DD_HHMM.json` → output de /spekgen-meta-ads-upload.

Deps: playwright + Pillow (ya instalados).

Por qué importa: snapshot pre-activar ads PAUSED. Ve en un ojo qué cobertura ya tenemos y qué clientes/formatos quedaron debiendo → input directo al brief del siguiente batch. Reemplaza los intentos previos de HTML local (CORS file:// + JSON.parse blobs embebidos — ambos fallaron).

Cuándo correr: después de cerrar el upload log. Claude debe ejecutar esto proactivamente sin pedir permiso. Gibran lo aprobó como parte estándar del workflow de ads.
