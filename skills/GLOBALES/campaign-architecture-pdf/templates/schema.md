# Schema JSON — campaign-architecture-pdf

Este documento describe la forma del JSON que consume `scripts/build_pdf.py` para
generar un PDF panoramico visual de una arquitectura de campana.

## Estructura top-level

```json
{
  "meta": { ... },
  "header_metrics": [ ... ],
  "pages": [ ... ]
}
```

---

## meta (obligatorio)

```json
{
  "meta": {
    "client": "HEALTHY CHUCHOS",
    "client_code": "HC",
    "title": "HEALTHY CHUCHOS - Arquitectura Meta Ads Mes 1",
    "subtitle": "Lanzamiento Abril 2026 - 25 dias - Broad MX 25-55",
    "tagline": "Estrategia Organic-First - Winners Organicos a Paid Ads",
    "date_generated": "2026-04-09",
    "images_root": "/abs/path/ o relativo/al/json",
    "output_pdf": "HC_ARQUITECTURA_META_ADS_MES1.pdf"
  }
}
```

- `images_root` (opcional): base path para resolver `images_folder` relativos de cada ad.
  Si se omite, se usa el directorio del JSON de entrada.
- `output_pdf` (opcional): puede ser absoluto o relativo al directorio del JSON. Si se
  omite, se usa `<input_stem>.pdf`. Puede sobreescribirse con `--output`.

---

## header_metrics (opcional)

Metricas chicas que aparecen en el header de la pagina 1 (lado derecho).

```json
"header_metrics": [
  {"label": "Budget", "value": "$4,000"},
  {"label": "Campanas", "value": "2"},
  {"label": "Ads Org.", "value": "6"},
  {"label": "Videos", "value": "+6"}
]
```

Opcional: `"value_size": "14px"` para ajustar el tamano de fuente del valor.

---

## pages (obligatorio)

Lista de paginas. Cada pagina tiene un `type`:
- `"architecture"` - pagina panoramica con campanas, ad sets, fases, ads
- `"detail"` - pagina de detalle con phase-summary, campaign blocks, kv grids, budget viz, timeline

### Pagina tipo `architecture`

```json
{
  "type": "architecture",
  "campaigns": [ { ... } ],
  "legend_items": [ ... ],
  "legend_meta": "Generado 2026-04-09 - HC SPEKGEN - Pagina 1 de 2",
  "page_foot": "Healthy Chuchos - Arquitectura Meta Ads Mes 1 - Visual",
  "page_num": "1 / 2"
}
```

### Pagina tipo `detail`

```json
{
  "type": "detail",
  "header": {
    "title": "HC - Campana 2 Quiz - Config",
    "subtitle": "Detalle operativo - Budget - Kill criteria",
    "tagline": "Todo lo que hay que saber antes de darle Publish",
    "metrics": [
      {"label": "Pixel", "value": "SPEKHC-23MARZO", "value_size": "10px"}
    ]
  },
  "phase_summary": [
    {
      "pn": "Fase 1 - Activo dia 1",
      "title": "Organic Winners",
      "desc": "Posts organicos WCI Tier 1-2...",
      "count": "6",
      "count_label": "ads carrusel"
    }
  ],
  "campaigns": [ { ... } ],
  "quiz_block": {
    "flow_title": "Quiz Funnel - Flujo",
    "flow_desc": "El usuario responde 5 preguntas...",
    "funnel": ["Meta Ad", "Quiz Page", "GHL CRM", "PDP recomendada"],
    "landing_title": "Landing - Quiz GHL",
    "landing_desc": "Tipo: Quiz dinamico (GHL)..."
  },
  "detail_grid": {
    "left": { ... detail-card },
    "right": [
      { "type": "card", ... },
      { "type": "budget_viz", ... },
      { "type": "timeline", ... }
    ]
  },
  "legend_items": [ ... ],
  "legend_meta": "...",
  "page_foot": "...",
  "page_num": "2 / 2"
}
```

---

## campaign

```json
{
  "name": "HC-VENTAS-MES1",
  "style": "background:linear-gradient(90deg, #4c1d95 0%, #7c3aed 100%);",
  "tag_style": "background:#c4b5fd;color:#4c1d95",
  "details": [
    {"k": "Objective", "v": "Sales"},
    {"k": "Optimization", "v": "Purchase"},
    {"k": "Budget", "v": "$3,000 MXN - CBO $120/dia"}
  ],
  "ad_sets": [ { ... } ]
}
```

- `style` y `tag_style` son opcionales (para campanas secundarias con color distinto, ej. quiz en morado).

---

## ad_set

```json
{
  "name": "HC-BROAD-MX-PURCHASE",
  "style": "background:#5b21b6;",
  "details": [
    {"k": "Audience", "v": "Broad MX 25-55"},
    {"k": "Placements", "v": "Advantage+"},
    {"k": "Pixel", "v": "1813096612719811"}
  ],
  "phases": [ { ... } ]
}
```

---

## phase

Un agrupador de ads dentro de un ad set (ej. "Fase 1: Organic Winners", "Fase 2: Videos Monse").

```json
{
  "name": "FASE 1 - ORGANIC WINNERS (ACTIVO DIA 1)",
  "info": "6 carruseles ya publicados con WCI validado",
  "color": "#2563eb",
  "ads": [ { ... } ]
}
```

Si no tiene sentido agrupar en fases, usa una sola fase con `name` generico.

---

## ad

```json
{
  "id": "O1",
  "name": "HC-AD-DOLOR-SILENCIOSO-CAROUSEL",
  "hook": "Lo que no puedes ver es lo que mas le duele",
  "product": "ArtriDog",
  "product_code": "artridog",
  "format": "Carrusel - 3 slides - 1:1",
  "origin": "Origen: HC-004 - 2026-04-01",
  "metric_label": "WCI 9.81%",
  "metric_tier": "high",
  "images_folder": "O1_HC-004_ARTRIDOG_DOLOR_SILENCIOSO",
  "placeholder": false,
  "is_video": false,
  "landing": {
    "type": "PDP NATIVA",
    "url": "/products/artridog",
    "detail": "$397 MXN"
  }
}
```

### Campos clave:

- **`id`**: badge corto (O1, V1, Q1, A1, etc.)
- **`product_code`**: afecta el color del border-left del card y el color de la product pill.
  Valores soportados: `artridog`, `dogrelax`, `omegadog`, `gastrodog`, `marca`, `brand`, `default`.
  Para clientes nuevos, extender `CSS` en `build_pdf.py` con clases `.prod-<code>` y `.ad-card.<code>`.
- **`metric_tier`**: `high` (verde), `mid` (azul), `low` (gris), `tbd` (gris claro, para pending).
- **`metric_label`**: texto del pill de metrica (ej. "WCI 9.81%", "Top", "Pendiente", "0 data").
- **`images_folder`**: ruta absoluta o relativa a `meta.images_root`. Si existe, carga todas las
  imagenes PNG/JPG/JPEG/WEBP ordenadas alfabeticamente como thumbnails. Si no existe o esta vacio,
  cae a placeholder automaticamente.
- **`placeholder`**: si es `true`, fuerza bloque placeholder (aunque haya carpeta).
- **`placeholder_icon`**: (opcional) caracter o emoji para el placeholder (default: "▶").
- **`placeholder_text`**: texto del placeholder, admite `\n` (default: "Pendiente").
- **`is_video`**: si es `true`, el badge se pinta morado y el card tiene fondo lila.

### Placeholder ejemplo

```json
{
  "id": "V1",
  "name": "HC-BRAND-SOYVETERINARIA-VIDEO",
  "hook": "Soy veterinaria. Y formule estos suplementos...",
  "product": "Marca",
  "product_code": "marca",
  "format": "Video - 45-60s - 9:16 + 1:1",
  "origin": "UGC Monse - Pendiente grabacion",
  "metric_label": "Pendiente",
  "metric_tier": "tbd",
  "placeholder": true,
  "placeholder_icon": "▶",
  "placeholder_text": "Video pendiente\n45-60s",
  "is_video": true,
  "landing": {
    "type": "HOME / COLECCION",
    "url": "healthychuchos.com",
    "detail": "Todo el catalogo"
  }
}
```

---

## legend_items (pie de pagina)

Legend bar negra al fondo de cada pagina.

```json
[
  {"kind": "dot", "color": "#f59e0b", "label": "ArtriDog $397"},
  {"kind": "dot", "color": "#8b5cf6", "label": "DogRelax $381"},
  {"kind": "text", "label": "<b style='color:#7dd3fc'>PDP NATIVA</b> - Shopify"},
  {"kind": "dash"}
]
```

---

## detail_grid (solo pagina tipo detail)

### left - una detail-card grande

```json
"left": {
  "dnum": "CAMPANA 1 - CONFIG TECNICA",
  "dtitle": "HC-VENTAS-MES1",
  "ddesc": "Escalar los winners organicos a paid...",
  "head_style": "",
  "dnum_style": "",
  "sections": [
    {
      "heading": "Ad Set - HC-BROAD-MX-PURCHASE",
      "kvs": [
        {"k": "Objective", "v": "Sales"},
        {"k": "Budget", "v": "<b>$3,000 MXN</b> - CBO $120/dia"}
      ]
    },
    {
      "heading": "Kill Criteria",
      "kvs": [
        {"k": "CTR link click", "v": "&ge; 1.0%"}
      ]
    }
  ]
}
```

### right - lista de bloques

Cada bloque tiene `type`:

#### type: "card" - otra detail-card

Misma estructura que `left`.

#### type: "budget_viz"

```json
{
  "type": "budget_viz",
  "title": "Distribucion de Budget - $4,000 MXN",
  "segments": [
    {"flex": 3, "color": "#2563eb", "label": "VENTAS - $3,000 (75%)"},
    {"flex": 1, "color": "#8b5cf6", "label": "QUIZ - $1,000 (25%)"}
  ],
  "legend": [
    {"color": "#2563eb", "label": "HC-VENTAS-MES1 - CBO $120/dia x 25d"},
    {"color": "#8b5cf6", "label": "HC-QUIZ-LEADS - Reserva Semana 2"}
  ]
}
```

#### type: "timeline"

```json
{
  "type": "timeline",
  "title": "Cronograma 25 dias",
  "weeks": [
    {"name": "SEM 1 - Lanzamiento", "task": "6 organic winners live..."},
    {"name": "SEM 2 - Videos + Quiz", "task": "..."},
    {"name": "SEM 3 - Optimizacion", "task": "..."},
    {"name": "SEM 4 - Escala", "task": "..."}
  ]
}
```

---

## Ejemplo completo

Ver `examples/hc_meta_ads_mes1.json`.
