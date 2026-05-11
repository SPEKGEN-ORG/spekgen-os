# ads-factory-batch — WORKFLOW end-to-end

Guia paso a paso para producir un batch de ads desde cero.
Duracion tipica: **~3h** produccion Claude + **~2h** Gibran en Gemini
para un batch de 15 ads.

## Pre-requisitos

- [ ] Google One Pro activo (Gemini Advanced)
- [ ] `.env` de cada cliente con META_TOKEN + AD_ACCOUNT configurado
- [ ] Ultimo reporte `/cross-client-intel` leido (winners a replicar)
- [ ] `_ads_factory/STRATEGY/STRATEGY_{CLIENTE}.md` al dia
- [ ] Python 3.9+ disponible (stdlib solo, sin pip)

## Fase 1 — Brief (~15 min, Claude + Gibran)

### 1.1 Claude lee contexto
```
Read _ads_factory/STRATEGY/STRATEGY_GR.md
Read _ads_factory/STRATEGY/STRATEGY_LF.md
Read _ads_factory/STRATEGY/STRATEGY_HC.md
Read _ads_factory/STRATEGY/PROMPT_RECIPE_PRODUCT_INTEGRATION.md
Read _cross_client_intel/CROSS_CLIENT_INSIGHTS_{ultima fecha}.{html|md}
```

### 1.2 Claude propone mix
Output esperado:
```
Mix propuesto — BATCH_{fecha}-v1

GR (N ads):
  - GR-AD-XXX MULTIPRODUCT_STACK {linea}
  - GR-AD-XXX OFFER {linea}
  - GR-AD-XXX TESTIMONIO {linea}

LF (N ads):
  - LF-AD-XXX UGC_PERSONA_OFFER (consolida Lupita + OFFER)
  - ...

HC (N ads):
  - HC-AD-XXX UGC_PERSONA (synthetic UGC)
  - HC-AD-XXX UGC_AUTHORITY (MV)
```

### 1.3 Gibran aprueba o ajusta
**Quality gate:** no arrancar Fase 2 sin aprobacion explicita del mix.

## Fase 2 — Init (~1 min)

```bash
cd "SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/ads-factory-batch"
python3 scripts/init_batch.py --date 2026-05-01 --version 1
```

Crea `_ads_factory/BATCH_2026-05-01-v1/` con skeleton vacio.

## Fase 3 — JSON (~45 min Claude, 1 ad a la vez)

Claude escribe `ads_batch.json` con N entries, una por una, siguiendo
`templates/ad_entry.json`. Para cada ad:

1. Consultar schema `schemas/ads_batch.schema.json`
2. Construir `gemini_prompt` usando los 4 bloques (ver
   `reference/PROMPT_ANATOMY.md`)
3. Aplicar palette del cliente (ver `reference/PALETTES_BY_CLIENT.md`)
4. Listar attachments con paths relativos (`RESOURCES/{ad_code}/ATTACHMENTS/...`)
5. Escribir ad_copy completo (primary_text, headline, CTA, landing)

**Orden de escritura:** agrupar por cliente (GR primero, luego LF,
luego HC). Minimiza switch de paleta/estilo.

Al terminar:
```bash
python3 scripts/validate_batch.py _ads_factory/BATCH_2026-05-01-v1
```

Output esperado: `[validate] OK — batch BATCH_2026-05-01-v1 valido`.
Si hay errores, iterar.

## Fase 4 — Poblar RESOURCES (~30 min Claude)

Para cada ad del JSON:

```bash
cd _ads_factory/BATCH_2026-05-01-v1/RESOURCES
mkdir -p "{ad_code}/00. FINAL" "{ad_code}/ATTACHMENTS"
cp "{source_path_cliente}" "{ad_code}/ATTACHMENTS/"
```

Cada `RESOURCES/{ad_code}/` debe quedar con:
- `ATTACHMENTS/` con todos los archivos listados en el JSON (matcheando paths exactos)
- `00. FINAL/` vacia (lista para outputs limpios — el prefijo `00. ` la pone arriba en Finder)
- Opcional: `BORRADOR/` vacia (Gibran la crea on-the-fly)

Re-validar:
```bash
python3 scripts/validate_batch.py _ads_factory/BATCH_2026-05-01-v1
```

Ahora validate_batch debe pasar todos los checks de attachments.

## Fase 5 — Gemini loop (~2h Gibran, solo)

```bash
python3 scripts/serve_dashboard.py _ads_factory/BATCH_2026-05-01-v1
```

Abre `http://localhost:8766/ads_batch.html` automaticamente.

Loop por ad:
1. Click COPIAR en el dashboard (copia el gemini_prompt al clipboard)
2. Abre `gemini.google.com/app` → nuevo chat
3. Pega prompt + arrastra todos los attachments desde
   `RESOURCES/{ad_code}/ATTACHMENTS/`
4. Genera imagen
5. Si no convence: iterar con "make the shadow stronger" etc hasta
   que Gibran apruebe
6. Guarda version aprobada en `BORRADOR/01.png`
7. Quita marca de agua (Photopea / Claude / otro)
8. Guarda final limpio en `00. FINAL/{ad_code}_{aspect_ratio}.png`

**Paralelizable:** Gibran abre 3-4 tabs de Gemini y genera ads en
paralelo (uno por tab).

## Fase 6 — Upload a Meta (~30 min Gibran + Claude)

Una vez los 15 FINAL/ estan listos:

```
Usa /spekgen-meta-ads-upload en este batch.

Batch: _ads_factory/BATCH_2026-05-01-v1
Mode: DRY_RUN primero, luego LIVE tras confirmacion.
```

El skill de upload lee el JSON, valida, hace draft en Meta, reporta.
Gibran revisa preview en Ads Manager antes de activar.

**CPA pre-check obligatorio:** CPA_max = precio_producto - $150. Si
el breakeven del ad propuesto excede ese limite, no activar (ver
`feedback_cross_client_cpa_validation`).

## Fase 7 — Logging (~5 min Claude)

Al cerrar sesion:
1. `_ads_factory/BATCH_{fecha}-v{N}/README.md` — resumen (ads, winners
   base, ROAS esperado, costo produccion)
2. Update `_ads_factory/_BIG_PICTURE_ADS_FACTORY.md` seccion
   "Batches producidos"
3. Daily note Obsidian con `- [ ]` pendientes
4. Si hubo feedback nuevo, agregarlo a
   `_ads_factory/STRATEGY/STRATEGY_{CLIENTE}.md`

## Anti-patrones (NO hacer)

1. **No escribir prompts antes de validar mix con Gibran** — context
   waste si hay que reescribir
2. **No usar paths absolutos en attachments** — rompen cuando el
   batch se mueve
3. **No generar todo via API Gemini** — se rompe el "Gibran approva
   en Gemini web" que preserva taste + es gratis con One Pro
4. **No saltarse validate_batch** — JSON malformado causa silent fails
   en upload
5. **No mezclar ads de distintos clientes en misma session de Gemini**
   — paleta drift
6. **No subir a Meta sin DRY_RUN primero** — audit trail
7. **No mover el `00. FINAL/` folder a otra ubicacion** — upload skill
   asume paths relativos al batch

## Metricas del workflow (objetivo)

| Metrica | Target |
|---|---|
| Tiempo Claude total | < 3h para 15 ads |
| Tiempo Gibran Gemini | < 2h para 15 ads |
| Ads que requieren re-prompt | < 30% |
| Ads con product integration OK al 1er intento | > 60% |
| Ads que pasan validate_batch al 1er run | > 90% |
| Costo produccion (API + tokens) | $0 (Gemini web UI) |

## Cierre de batch

Un batch se considera "cerrado" cuando:
- [ ] JSON completo y valida OK
- [ ] RESOURCES completo (todos attachments en ATTACHMENTS/ + 00. FINAL/ poblado)
- [ ] Los N ads estan activos en Meta (o pausados con razon documentada)
- [ ] README.md del batch escrito
- [ ] Entry en `_BIG_PICTURE_ADS_FACTORY.md` agregado
- [ ] Daily note actualizada
