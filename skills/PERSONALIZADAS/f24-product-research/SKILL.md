---
name: f24-product-research
description: Investiga recursos completos para un producto del catálogo F24 (Ferre24) — imágenes, PDFs, specs, taxonomía, copy de venta. Lee el SKU del xlsx maestro `00_50_PRIORITARIOS_MARVELSA.xlsx`, spawnea 4 agentes research en paralelo (MEDIA, DOCS, SPECS, COMERCIAL), reconcilia discrepancias, spawnea agente COPY secuencial, y actualiza Research Log + Asset Index + Checklist Recursos. Empaca todos los recursos en la carpeta del producto con estructura 01-05. Activate for "investiga el producto F24 X", "recursos del HP5.5N", "siguiente producto F24", "f24 product research", "research del SKU XXX", "/f24-product-research".
---

# `/f24-product-research` — F24 Product Research Skill

Skill SPEKGEN para Ferre24 (F24). Cosecha recursos completos para un producto Marvelsa siguiendo el workflow validado en el piloto **HP5.5N (Hidrolavadora 5.5hp)** que llevó la cobertura de checklist de **8.3% → 81.2%**.

## Cuándo usarse

- "Investiga el producto F24 HP5.5N"
- "Recursos del SKU CA-25PH"
- "Siguiente producto F24" (toma el de menor `% Completo`)
- "f24-product-research --batch 5"
- "Investiga 5 más"

## Inputs

- **SKU obligatorio** — debe existir en `F24- FERRE24/F24 - 02. PRODUCTOS/00_50_PRIORITARIOS_MARVELSA.xlsx` hoja `50 SKUs Prioritarios`.
- **Carpeta destino** — `F24- FERRE24/F24 - 02. PRODUCTOS/{descripcion}/`. Si no existe se crea con estructura 01-05.

## Outputs

```
F24 - 02. PRODUCTOS/{descripcion}/
├── _research_log.md         ← bitácora narrativa por agente
├── 01. MEDIA/
│   ├── _findings.json
│   ├── hero/hero_001.jpg
│   ├── secundarias/sec_001..N.jpg
│   ├── lifestyle/life_001.jpg
│   └── video/video_urls.md
├── 02. DOCS/
│   ├── _findings.json
│   ├── ficha_tecnica.pdf
│   ├── manual.pdf            (si está disponible)
│   └── exploded.pdf          (si está disponible)
├── 03. SPECS/specs.json
├── 04. COMERCIAL/comercial.json
└── 05. COPY/copy.md
```

Y al xlsx maestro:
- Hoja **`Research Log`** — fila por (SKU, campo) con valor + fuente + confidence + agente + fecha
- Hoja **`Asset Index`** — fila por archivo físico con tipo + ruta + size + source URL
- Hoja **`Checklist Recursos`** — actualiza ✓/⚠/✗ + `% Completo` para el SKU

## Workflow (5 fases)

### Fase 0 — Setup (Claude orquestador, no agente)
1. Leer `00_50_PRIORITARIOS_MARVELSA.xlsx` hoja `50 SKUs Prioritarios`, encontrar fila del SKU.
2. Capturar contexto base: `sku, descripcion, url_marvelsa, url_imagen, precio_costo_f24 (col E), bodega, categoria_master`.
   - **Col E "Precio dist Marvelsa" = precio Sergio→F24** (es lo que el cliente nos pasa, no se cuestiona).
   - Col F existe en el xlsx pero **NO es relevante para el research** — el alcance de SPEKGEN es solo cosechar info del producto, no analizar pricing de proveedor.
3. Crear estructura de carpetas si no existe.
4. Verificar que las hojas `Research Log` y `Asset Index` existan (sino → `scripts/_add_research_sheets.py`).

### Alcance del skill (qué SÍ y qué NO hace)

**SÍ:**
- Cosechar imágenes, PDFs, specs, taxonomía, tags, pain points, ángulos de venta, copy de PDP.
- Documentar fuentes y discrepancias técnicas (specs entre retailers).
- Marcar viabilidad comercial como dato informativo si la encuentra, NO como gate.

**NO:**
- Analizar pricing de proveedor ni recomendar renegociaciones.
- Comparar costo F24 vs mercado para "validar" si el SKU debe venderse — esa es decisión de F24/Sergio, no de SPEKGEN.
- Bloquear generación de copy por márgenes — el copy se genera siempre; el precio retail final lo decide el cliente.

### Fase 1 — Spawn 4 agentes research EN PARALELO

**SINGLE message con 4 Agent tool uses** (subagent_type=`general-purpose`, isolation=`worktree` NO — los agentes escriben a la misma carpeta).

Prompts en `agent_prompts/`:
- `media.md` → cubre hero, secundarias 3+, lifestyle, video
- `docs.md` → cubre ficha técnica, manual, exploded
- `specs.md` → cubre marca/modelo + motor + operativas + físicas + garantía + NOM + país origen + embarque + frágil
- `comercial.md` → cubre taxonomía Shopify + tags + SEO keywords + precio competencia + pain points + ángulos venta

**Todos escriben a `_findings.json` en su subfolder. NUNCA al xlsx.**

### Fase 2 — Reconciliación (Claude orquestador)

Validar consistencia entre agentes ANTES de spawn COPY:

1. **Brand/modelo discrepancy** — si COMERCIAL y SPECS difieren, **SPECS gana** (regla validada en piloto: COMERCIAL hipotetizó Surtek HG755, SPECS confirmó Parazzini con manual + 4 retailers).
2. **Specs numéricos** — prioridad **Marvelsa > manual fabricante > Ferrepat > Manualslib > Mercado Libre > Amazon**. Discrepancias se documentan en `specs.json` campo `discrepancias`.
3. **Coverage gate** — si <50% de campos del checklist quedaron sin valor, NO pasar a COPY. Re-spawn los agentes con prompt refinado o flag manual review.

### Fase 3 — Spawn COPY agent (SECUENCIAL, no paralelo)

Prompt en `agent_prompts/copy.md`. Recibe outputs reconciliados de fase 1 + flags de reconciliación de fase 2. NO investiga, solo sintetiza.

Output: `05. COPY/copy.md` con 9 secciones fijas:
- Meta producto
- Descripción corta (≤160 chars)
- Descripción larga (250-400 palabras)
- Bullets venta (6-8)
- SEO (title, description, slug, keywords)
- H1 sugerido para PDP
- Hook de ad (Meta/IG, 1 versión)
- Notas para equipo (discrepancias, `[VERIFICAR]`)

### Fase 4 — Consolidar xlsx

```bash
python3 scripts/consolidate_to_xlsx.py <SKU> "<descripcion>"
```

El script:
- Lee los 4 JSONs + scan disco
- Reconcilia marca/modelo (SPECS gana sobre COMERCIAL)
- Upsert filas en `Research Log` (granular) y `Asset Index` (archivos)
- Actualiza fila del SKU en `Checklist Recursos` con ✓/⚠/✗ por columna + `% Completo`

## Modos de invocación

Frases que activan el skill en Claude Code (NO son comandos shell — son intenciones que Claude interpreta y ejecuta como el workflow descrito arriba):

| Lo que le dices a Claude | Lo que Claude hace |
|---|---|
| "Investiga el SKU HP5.5N" | Corre el workflow 5 fases para 1 SKU end-to-end |
| "Siguiente producto F24" | Lee xlsx, toma el de menor `% Completo`, corre el workflow |
| "Investiga 5 más" | Repite el workflow secuencialmente sobre los siguientes 5 SKUs incompletos |
| "Re-corre solo el agente DOCS para HP5.5N" | Spawneja solo ese agente, re-consolida xlsx |

**Modos batch automatizados (`--batch`, `--field`, `--dry-run`)** son roadmap futuro — requieren un script orquestador que aún no existe. Por ahora Claude orquesta el flujo siguiendo las instrucciones de este SKILL.md.

## Reglas duras

1. **NUNCA inventar specs.** Si una fuente no lo dice, queda `null` o `[VERIFICAR]`.
2. **NUNCA inventar marca/modelo.** Si no se puede identificar con confianza alta, COPY agent NO escribe descripción larga — sale `[VERIFICAR marca antes de publicar]`.
3. **Garantía default = OEM (manual fabricante).** Retailers anuncian más para marketing — usar OEM y dejar nota al equipo.
4. **Productos motorizados con combustible** → flag automático "no paquetería aérea" + despachar vacío.
5. **Marvelsa requiere login** — el skill no intenta scrapear. Para fichas técnicas reales, Sergio debe drop manualmente en `02. DOCS/` (modo override), o usar fuentes secundarias (Jardepot, AgroCoyote, Ferrepat).
6. **Reconciliación obligatoria** entre fase 1 y fase 3. Sin esto el COPY puede heredar errores (caso piloto: Surtek vs Parazzini).

## Fuentes doradas (heurística aprendida en piloto)

| Recurso | Fuente #1 | Fuente #2 |
|---|---|---|
| Imágenes secundarias | Ferrepat CDN `cms.grupoferrepat.net/assets/img/productos/{SKU}.webp` + `_1..7.webp` | Bombas y Maquinaria |
| Ficha técnica PDF | Jardepot → Google Drive | AgroCoyote API `api5.agrocoyote.com.mx/api/ficha/{SKU}` |
| Specs estructurados | Ferrepat | Manualslib (auth-walled, no scrape, solo URL) |
| Hero alta-res | Marvelsa `image_2048` | Fabricante |
| Video | Canal YouTube del distribuidor | Búsqueda `"marca modelo" review` |
| Brand match | Reverse-image (logo en hero) + buscar SKU literal en Google | Cross-spec compare |

## Específicos que casi siempre faltan (flag automático)

- Cilindrada cc del motor
- Capacidad tanque combustible litros
- Longitud manguera metros
- Color exacto
- NOM (zona oscura — requiere contacto fabricante MX)
- Manual de usuario PDF público
- Exploded view aislado

## Reutilizable a nivel categoría (roadmap v2)

Cuando llegue el segundo SKU de una categoría (ej. segunda hidrolavadora), valdría la pena cachear y reutilizar:
- Taxonomía Shopify (estable por familia)
- Tags base
- Pain points base
- Ángulos venta base

Esto reduciría el research per-SKU a solo lo específico (HP, PSI, GPM, brand match). **No está implementado todavía** — para los primeros SKUs cada uno corre el workflow completo. Si el patrón se confirma viable, agregar `category_memory/{categoria}.json` en una v2.

## Verificación end-to-end

Criterios para considerar el SKU "completo":
1. `% Completo` ≥80% (puede ser menos si NOM no aplica)
2. Archivos en `Asset Index` existen en disco con `size_kb ≥ umbral` (img≥80KB, PDF≥50KB)
3. Cada fila de `Research Log` con `fuente_url` no-vacío
4. `copy.md` ≥1KB con las 9 secciones presentes
5. Marca + modelo reconciliados (sin discrepancia entre SPECS y COMERCIAL)

## Archivos del skill

```
f24-product-research/
├── SKILL.md                          ← este archivo
├── agent_prompts/
│   ├── media.md                      ← prompt template para agente MEDIA
│   ├── docs.md                       ← prompt template para agente DOCS
│   ├── specs.md                      ← prompt template para agente SPECS
│   ├── comercial.md                  ← prompt template para agente COMERCIAL
│   └── copy.md                       ← prompt template para agente COPY
└── scripts/
    ├── consolidate_to_xlsx.py        ← fase 4 — consolida JSONs → xlsx
    └── _add_research_sheets.py       ← idempotente, asegura hojas Research Log + Asset Index
```

Los agent prompts tienen placeholders tipo `{{SKU}}`, `{{DESCRIPCION}}`, `{{URL_MARVELSA}}`, etc. Claude (orquestador) los rellena al spawnear cada agente, leyéndolos del xlsx en Fase 0.

## Setup (primera vez en una máquina nueva)

1. **Acceso al Shared Drive** — debes tener "01. CLIENTS OFFICIAL" sincronizado vía Google Drive Desktop. Si es máquina ajena al admin de SPEKGEN: Gibran te comparte la carpeta desde Google Drive Web (click derecho → Compartir → tu email como Editor), tú activas "Unidades compartidas" en Drive Desktop → Preferencias.
2. **Python 3** con `openpyxl` y `pypdf` instalados.
   - **Mac/Linux:** `python3 -m pip install openpyxl pypdf`
   - **Windows:** `python -m pip install openpyxl pypdf` (Python desde winget se registra como `python` y `py`, normalmente NO como `python3`)
3. **(Opcional) Override de ruta** — si la búsqueda automática falla, define `F24_PRODUCTS_DIR` con la ruta absoluta a `F24- FERRE24/F24 - 02. PRODUCTOS/`.
   - Mac/Linux: `export F24_PRODUCTS_DIR="/ruta/absoluta"`
   - Windows PowerShell: `$env:F24_PRODUCTS_DIR = "G:\ruta\absoluta"`
4. **Symlink al directorio de skills de Claude:**
   - **Mac/Linux:** el hook `SessionStart` lo hace automático (`.claude/hooks/sync-skills.sh` — bash). Skill aparece en `~/.claude/skills/f24-product-research`.
   - **Windows:** el hook bash NO corre en cmd/PowerShell nativo. Opciones:
     - Junction (recomendado, no requiere admin): `mklink /J "%USERPROFILE%\.claude\skills\f24-product-research" "G:\My Drive\01. CLIENTS OFFICIAL\SPK - SPEKGEN AGENCY\SPK - 02. SKILLS\PERSONALIZADAS\f24-product-research"` (ajusta la letra del drive).
     - Copia directa: `xcopy /E /I` de la carpeta del skill a `%USERPROFILE%\.claude\skills\` (hay que re-copiar cuando se actualice).
     - Usar Git Bash / WSL y correr `sync-skills.sh` desde ahí.

## Notas cross-platform

- En todas las invocaciones de Python dentro del skill y agent prompts, "`python3`" significa "el intérprete de Python 3 disponible en tu sistema". Mac/Linux: `python3`. Windows: `python` o `py`.
- Path separators: los scripts usan `pathlib.Path` así que funcionan idéntico en Mac y Windows.
- Anchor del path resolution: el skill busca la carpeta `01. CLIENTS OFFICIAL` caminando hacia arriba desde `__file__`. Funciona en `/Users/...` (Mac) y `G:\My Drive\...` (Windows) siempre que la estructura del Drive esté sincronizada.

## Lecciones validadas en el piloto

Ver `F24- FERRE24/F24 - 02. PRODUCTOS/_RESEARCH_WORKFLOW.md` para retro completa.

Resumen ejecutivo:
- **Brand discovery cross-agent funciona** — 3 de 4 agentes identificaron Parazzini leyendo el logo en hero image.
- **Marvelsa login wall es bloqueante** — sin credenciales, hay que reemplazar con fuentes secundarias.
- **Ferrepat + Jardepot son las dos fuentes doradas para ferretería MX.**
- **COMERCIAL puede hipotetizar marca incorrecta** — orquestador DEBE reconciliar antes de COPY.
- **5 campos casi siempre quedan en falta**: cc, tanque, manguera, color, NOM. Esperar 80-85% como techo natural sin override manual.
