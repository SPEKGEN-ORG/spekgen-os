---
name: campaign-architecture-pdf
description: >
  Genera un PDF visual panoramico (A3 landscape) de la arquitectura de una campana publicitaria:
  campanas, ad sets, ads con thumbnails reales embebidos, placeholders para creativos pendientes,
  y landings. Para HC, LF, GR, MG y cualquier cliente nuevo.
  Activate for: "pdf arquitectura", "pdf de la estrategia", "armame un pdf visual",
  "plasma la estrategia en pdf", "dibuja la arquitectura", "arquitectura visual",
  "arquitectura de campana", "/campaign-architecture-pdf", "arquitectura meta ads",
  "pdf de campanas", "mapa visual de ads".
---

# Campaign Architecture PDF — v1.0

## Overview

Cada vez que defines o refinas la estrategia/estructura de una campana publicitaria,
Gibran necesita verla como PDF visual panoramico. Gibran es EXTREMADAMENTE visual —
se pierde con .md o Google Docs. Esta skill genera ese PDF de manera consistente:

- **Formato:** A3 landscape (420 x 297 mm)
- **Estructura:** Campana → Ad Set → Fase → Ads → Landing (columnas con arrow)
- **Thumbnails reales:** cada ad con sus slides embebidos como base64 (no URLs)
- **Placeholders:** cuando un creativo no existe todavia, bloque morado con "Pendiente"
- **Pages:** una pagina principal de arquitectura + paginas opcionales de detalle
  (config tecnica, budget viz, timeline, phase summary, quiz block)

**Regla de oro:** Esta skill corre SIEMPRE que definamos una estrategia o arquitectura
de campana para cualquier cliente — HC, LF, GR, MG, Gibran Ecom. Nunca entregar la
estrategia sin el PDF visual acompanandola.

---

## Paths

```
CLIENTS_BASE   = /Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL
SKILL_DIR      = SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/campaign-architecture-pdf
BUILD_SCRIPT   = {SKILL_DIR}/scripts/build_pdf.py
SCHEMA_DOC     = {SKILL_DIR}/templates/schema.md
EXAMPLE        = {SKILL_DIR}/examples/hc_meta_ads_mes1.json
```

---

## Cuando Activar

Activa esta skill cuando detectes CUALQUIERA de estos contextos:

1. **Gibran pide explicitamente un PDF visual** de una estrategia, campana, o arquitectura
2. **Acabas de escribir/actualizar una estrategia** (PLAN_CAMPAÑA.md, HC_ESTRATEGIA_*.md, etc.)
   y el PDF visual deberia acompanarla
3. **Gibran refina la estructura de ads** (agregar/quitar ads, cambiar fases, mover budget)
4. **Se aprueba/rechaza** un creativo y la arquitectura debe actualizarse
5. **Se arranca una campana nueva** para un cliente nuevo

Si Gibran dice "armame la estrategia pero sin PDF", respeta. Pero por default: estrategia = estrategia + PDF.

---

## Phase 0: PRE-FLIGHT (obligatorio)

Antes de generar el JSON de entrada, recopila TODA esta informacion:

### Data esencial (siempre)
- [ ] Cliente (HC, LF, GR, MG, Gibran Ecom, etc.)
- [ ] Nombre de la campana (ej. "Mes 1", "Lanzamiento Q2", "Scale")
- [ ] Budget total y ventana (ej. "$4,000 MXN / 25 dias")
- [ ] Audiencia (ej. "Broad MX 25-55")
- [ ] Objetivo de Meta Ads (Sales / Leads / Traffic / Awareness)
- [ ] Pixel ID + Ad Account ID (leer del `.env` del cliente)

### Lista de ads (para cada uno)
- [ ] ID corto (O1, V1, A1, Q1)
- [ ] Nombre Ads Manager (ej. HC-AD-DOLOR-SILENCIOSO-CAROUSEL)
- [ ] Hook (linea del primary text)
- [ ] Producto (y product_code para el color)
- [ ] Formato (carrusel/video/estatico, # slides, ratio)
- [ ] Origen (post ID + fecha, o "nuevo creative")
- [ ] Metrica label (WCI %, Tier, "Pendiente")
- [ ] Images folder (ruta absoluta o relativa) o placeholder=true
- [ ] Landing (tipo + URL + precio/detalle)

### Si el ad NO tiene creativos todavia
- `placeholder: true`
- `placeholder_icon: "▶"` (video) o `"📷"` (estatico)
- `placeholder_text: "Video pendiente\n45-60s"` o similar
- `metric_tier: "tbd"`, `metric_label: "Pendiente"`

---

## Phase 1: Escribir el JSON

1. **Ubicacion del JSON:** Guarda el input en
   `{CLIENT}/05. META ADS/{CAMPAÑA}/00. ESTRATEGIA/_arquitectura_build/input.json`
   (o el equivalente del cliente).
2. **Base template:** Copia `examples/hc_meta_ads_mes1.json` y reemplaza los campos.
3. **Schema:** Consulta `templates/schema.md` si tienes dudas sobre algun campo.
4. **images_root:** Ajusta al folder base donde viven los folders de imagenes por ad
   (normalmente `01. ESTATICOS/` dentro de la campana).
5. **output_pdf:** Ruta absoluta donde se guardara el PDF final (idealmente en `00. ESTRATEGIA/`).

### Reglas de naming
- `product_code`: usa `artridog`, `dogrelax`, `omegadog`, `gastrodog`, `marca` (HC).
  Para clientes nuevos, extiende el CSS en `scripts/build_pdf.py` con una nueva clase
  `.prod-<code>` y `.ad-card.<code>` (border-left-color). Alternativamente usa `default`.
- `metric_tier`: `high` (verde), `mid` (azul), `low` (gris), `tbd` (gris claro).
- Fases: minimo 1 fase. Si no hay sub-agrupacion, usa una sola fase con nombre generico
  (ej. "ADS ACTIVOS" o "CREATIVOS").

---

## Phase 2: Ejecutar el build

```bash
cd "{SKILL_DIR}/scripts"
python3 build_pdf.py "/ruta/al/input.json"
```

El script:
1. Lee el JSON
2. Carga todas las imagenes de los `images_folder` y las embebe como base64 (max 260px ancho, JPEG 82%)
3. Si una carpeta no existe o esta vacia, muestra placeholder automaticamente
4. Genera HTML intermedio
5. Llama a Playwright (chromium headless) para renderizar a PDF A3 landscape
6. Borra el HTML intermedio (usa `--keep-html` si lo quieres conservar para debug)

### Opciones
- `--output <path>` — sobreescribe `meta.output_pdf` del JSON
- `--html-only` — solo genera HTML (util para preview rapido)
- `--keep-html` — no borra el HTML intermedio

### Dependencias
- `pillow` (ya instalado via Python sistema)
- `playwright` + `chromium` (ya instalado, se usa en otras skills)

---

## Phase 3: Verificar el PDF

Despues de generar el PDF:

1. **Tamano sanity check:** debe pesar 500KB-2MB (si es <50KB probablemente faltan imagenes)
2. **Abrir con `open`:** `open "/ruta/al/pdf"` — verifica visualmente que:
   - [ ] Todas las fases se ven
   - [ ] Cada ad muestra sus thumbnails reales (no solo placeholder gris)
   - [ ] Los placeholders de videos/creativos pendientes estan visibles
   - [ ] Los colores de producto estan correctos
   - [ ] Las metricas pill (WCI, Tier, Pendiente) tienen el color correcto
   - [ ] El header tiene el titulo y metricas correctas
   - [ ] La pagina de detalle (si existe) tiene budget viz, timeline, kv grids correctos
3. **Si hay error visual:** ajusta el JSON y re-corre el build. NO editar el HTML/script
   directamente (a menos que sea un bug real del script — entonces arreglar `build_pdf.py`).

---

## Phase 4: Entrega

1. **Abrir el PDF para Gibran:** `open "/ruta/al/pdf"` (comando clickable al final de la entrega)
2. **Mencionar que tambien esta en _arquitectura_build:** el input.json + script permiten regenerar
   fast si algo cambia
3. **Actualizar `_CLIENT_CONTEXT.md`** del cliente en la seccion "Ultima Sesion" con el PDF generado

---

## Regla de oro: un PDF por cada definicion de estrategia

> Cada vez que se define, ajusta, o refina una arquitectura de campana para cualquier
> cliente (HC/LF/GR/MG/Gibran Ecom/nuevos), se genera o regenera este PDF.

Casos:
- Estrategia nueva → PDF v1
- Agregar creativos nuevos → PDF v2 (regenera con el JSON actualizado)
- Cambiar budget → PDF v3
- Cambiar fases → PDF v4
- Fin de mes, planear siguiente → PDF del siguiente mes

Siempre guardar el JSON en `_arquitectura_build/` de la campana para regenerar rapido.

---

## Estilo visual (fijo)

No tocar el CSS a menos que Gibran pida un rediseno global. El estilo actual es:
- Header azul marino con gradient a cyan, metricas a la derecha
- Campaign bar gradient oscuro con CBO bar verde (o morado para quiz)
- Ad cards con border-left color por producto, thumbnails embebidos, arrow, landing a la derecha
- Placeholder blocks en morado/lila con dashed border
- Legend bar negra al fondo con dots de color por producto
- Pagina de detalle con kv grids, budget viz horizontal, timeline 4 columnas

Si necesitas agregar un nuevo **producto** para un cliente nuevo:
1. Elige un color distinto a los existentes
2. Agrega en `build_pdf.py` seccion `CSS`:
   ```css
   .prod-<code> { background: <color>; }
   .ad-card.<code> { border-left-color: <color>; }
   ```
3. Usa `product_code: "<code>"` en el JSON

---

## Troubleshooting

| Problema | Causa | Solucion |
|---|---|---|
| PDF <50KB sin thumbnails | Imagenes no cargaron | Verifica `images_root` + `images_folder` paths |
| ImportError Pillow | Pillow no instalado | `pip install pillow` |
| Playwright error | Chromium no instalado | `playwright install chromium` |
| Texto con espacios raros | Usaste `u00a0` en vez de espacio | Cambiar a espacio normal |
| PDF pagina 2 se corta | Demasiado contenido en detail_grid | Reducir cantidad de kvs o quitar un bloque del right |
| Colors incorrectos | `product_code` no existe en CSS | Agregar clase nueva o usar `default` |

---

## Ejemplo completo de invocacion

Gibran dice: "Ya definimos el plan de campana Mes 2 de HC. Armame el PDF visual."

1. Leo `HC - HEALTHY CHUCHOS/HC - 05. META ADS/CAMPAÑA MES 2/00. ESTRATEGIA/PLAN_CAMPAÑA.md`
2. Extraigo: campanas, ad sets, ads, imagenes, budget, cronograma
3. Copio `examples/hc_meta_ads_mes1.json` a `CAMPAÑA MES 2/00. ESTRATEGIA/_arquitectura_build/input.json`
4. Edito el JSON con los datos Mes 2
5. Corro: `python3 "{SKILL_DIR}/scripts/build_pdf.py" "<path al input.json>"`
6. Verifico el PDF visualmente
7. `open "<path al pdf>"`

---

## Notas finales

- **Nunca usar Canva para esto.** El flujo es HTML/CSS → Playwright → PDF, siempre.
- **Nunca inventar imagenes.** Si no existe la carpeta, usa placeholder.
- **Siempre embed base64** — nunca URLs externas (el PDF debe ser self-contained).
- **El PDF es documento operativo** — no es material de cliente, es herramienta interna para
  que Gibran tenga visibilidad total de la arquitectura de una campana en una sola hoja.
