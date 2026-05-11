---
name: F24 Product Research Skill
description: Skill /f24-product-research validado 2026-05-11. Cosecha imágenes+PDFs+specs+copy de productos Marvelsa. 4 sub-agentes paralelos + 1 COPY secuencial. Path portable Pedro-ready.
type: project
originSessionId: 7606906f-b773-4700-a985-c52ea1d36de0
---
Skill `/f24-product-research` construida y validada con piloto HP5.5N (Hidrolavadora Parazzini HP5.5) el 2026-05-11. Cobertura del checklist: **8.3% → 81.2%** en una corrida.

## Arquitectura

- **4 sub-agentes en paralelo** (single message, 4 Agent tool uses, general-purpose, no worktree isolation):
  - MEDIA → hero + secundarias 3+ + lifestyle + video URLs
  - DOCS → ficha técnica PDF + manual + exploded view
  - SPECS → marca/modelo + motor + operativas + físicas + garantía + NOM + país origen + embarque
  - COMERCIAL → taxonomía Shopify + tags + SEO + pain points + ángulos venta
- **1 COPY agent secuencial** después de reconciliación: copy.md con 9 secciones fijas
- **Consolidador Python** que lee 4 JSONs → upsert 2 hojas xlsx (Research Log granular + Asset Index de archivos) + actualiza Checklist Recursos dashboard

## Path

`SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/PERSONALIZADAS/f24-product-research/`

Estructura: SKILL.md + agent_prompts/ (5 archivos con placeholders) + scripts/ (consolidate_to_xlsx.py + _add_research_sheets.py)

## Fuentes doradas para ferretería MX (replicables en 49 SKUs restantes)

- **Imágenes secundarias:** Ferrepat CDN patrón directo `cms.grupoferrepat.net/assets/img/productos/{SKU}.webp + _1..7.webp` — galería completa en una llamada, sin watermark
- **Ficha técnica PDF:** Jardepot → botón "Descargar Ficha Técnica" → Google Drive público (canonical) + AgroCoyote API `api5.agrocoyote.com.mx/api/ficha/{SKU}` (backup)
- **Specs estructurados:** Ferrepat tiene tabla completa con peso embarque + país + garantía
- **Hero alta-res:** Marvelsa cambiar `image_512` → `image_2048`
- **Manualslib:** auth-walled — NO scrapear, solo registrar URL

## Trampas a evitar

- **Marvelsa requiere LOGIN** (303 → /web/login). Inútil sin credenciales — usar fuentes secundarias.
- **Marvelsa sirve solo UNA imagen.** Endpoints `image_extra_N`, `image_zoom` devuelven placeholder 6KB/256px.
- **Mercado Libre y Amazon MX bloquean WebFetch frecuente** (403/JS-only).
- **COMERCIAL puede hipotetizar marca incorrecta** desde specs "similares" (ej. asumió HP5.5N = Surtek HG755 cuando era Parazzini HP5.5 con presión diferente). SPECS gana en reconciliación.
- **`file` macOS reporta `Pages: 0` falso** para PDFs dompdf (AgroCoyote). Validar con `pypdf` o `pdfinfo`.

## Patrones de identificación de marca

- **Leer logo en hero_001.jpg con Read tool** después de descarga — 3 agentes lo lograron independientemente en piloto.
- **Buscar SKU literal en Google** — frecuentemente aparece como URL slug en agrocoyote.com.mx / portal.agrobolder.com confirmando marca+modelo upstream.

## Convención de columnas del xlsx (CRÍTICO)

`00_50_PRIORITARIOS_MARVELSA.xlsx` hoja `50 SKUs Prioritarios`:
- **Col E "Precio dist Marvelsa" = costo F24** (lo que Sergio cobra a F24). USA ESTA.
- **Col F "Precio neto Sergio" = costo interno Sergio** (irrelevante para research/copy).

## Specs que casi siempre faltan en ferretería MX (flag automático)

cilindrada cc del motor, capacidad tanque combustible litros, longitud manguera metros, color exacto, NOM (zona oscura total — requiere contacto fabricante MX), manual de usuario PDF público, exploded view aislado. Esperar 80-85% como techo natural sin override manual.

## Reglas operativas

- **Garantía:** default OEM 12m (manual fabricante), retailers anuncian 36m como marketing. Default a 12m + nota al equipo.
- **Flete motorizado con combustible:** flag "NO paquetería aérea" (DHL/FedEx Express rechazan). Usar Estafeta/Castores/Tres Guerras. Despachar vacío.
- **Precio retail final lo decide F24.** SPEKGEN solo hace research; NO analiza pricing del proveedor, NO recomienda renegociaciones. Si COMERCIAL sugiere `precio_venta_sugerido_mxn`, es informativo nada más.

## Path resolution portable

Scripts usan walk-up desde `Path(__file__).resolve()` hasta encontrar anchor `01. CLIENTS OFFICIAL` (común en Drive de Gibran y Pedro). Env var `F24_PRODUCTS_DIR` como escape hatch. NO hardcoded `/Users/gibranalonzo/...`.

## Cross-machine ready

`INSTALL_PEDRO.txt` en raíz del skill: prompt copy-paste de 7 pasos para Pedro. Verifica setup + test de portabilidad sin correr SKU nuevo.

## Roadmap v2

- `category_memory/{categoria}.json` para reutilizar taxonomía + tags + pain points cuando llega segundo SKU de la misma familia (ej. segunda hidrolavadora). NO implementado todavía — para primeros SKUs cada uno corre workflow completo. Si patrón se confirma viable, agregar.
- Modos batch automatizados (`--batch`, `--field`, `--dry-run`) son roadmap. Por ahora Claude orquesta siguiendo SKILL.md.

## Estado del piloto

- HP5.5N (Hidrolavadora a gasolina 5.5hp): 81.2% completo, marca Parazzini HP5.5 reconciliada, copy.md limpio en español MX, todos los archivos en `F24 - 02. PRODUCTOS/Hidrolavadora a gasolina 5.5hp/`.
- 49 SKUs prioritarios restantes pendientes. Siguiente: CA-25PH Compresor de aire Power Hunt 25L.
- Retro completa en `F24 - 02. PRODUCTOS/_RESEARCH_WORKFLOW.md`.
