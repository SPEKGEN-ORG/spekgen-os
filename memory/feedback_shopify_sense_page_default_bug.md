# feedback: Shopify theme Sense default page.json renders no body_html

**Contexto:** GR theme "Sense" (id 131785490521). Cuando se crea una page via Admin API con body_html custom y template_suffix vacío, el theme NO renderiza el content — solo aparece en meta description (invisible).

**Root cause (confirmado 2026-04-21):**
`templates/page.json` default del theme tiene:
```json
{
  "sections": {
    "main": {
      "type": "main-page",
      "disabled": true,  // ← AQUÍ
      "settings": {...}
    },
    "multirow_PnzwfC": { "type":"multirow", ... "heading":"Descubre las Aplicaciones..." },
    "multicolumn_89y3xw": { "type":"multicolumn", ... 8 columnas de "Enfermedades..." }
  },
  "order": ["main", "multirow_PnzwfC", "multicolumn_89y3xw"]
}
```

La section `main-page` (que renderiza `{{ page.content }}`) está disabled. Las 2 secciones hardcoded se muestran en su lugar. Por eso todas las pages del store con template default muestran el mismo hero y multicolumn, independiente de su body_html.

**Por qué las pages EcomPoser sí funcionan:** todas usan template_suffix `ecom-*` que apunta a templates custom creados por la app, bypaseando el default.

## Fix estándar para pages API nuevas en GR

1. Crear asset custom via PUT `/admin/api/2024-10/themes/{THEME_ID}/assets.json`:
   ```json
   {"asset":{"key":"templates/page.{handle}.liquid","value":"<div class=\"page-width\" style=\"padding:24px 0;\">\n  {{ page.content }}\n</div>"}}
   ```
2. PUT page con `template_suffix={handle}`
3. Verificar render con curl: buscar `<form action="/cart/add"` o el H1 real en el HTML público

## Fix definitivo pendiente (afecta todo el store)

Cambiar `main-page` a `"disabled": false` en `templates/page.json` O eliminar las 2 secciones hardcoded. Afecta pages futuras sin template_suffix y podría afectar pages legacy si alguien depende del hero compartido.

## Aplica a

- GR (confirmado 2026-04-21)
- Validar antes de asumir misma cosa en LF, HC, Gibran Ecom stores — cada theme puede tener config diferente.

## Descubierto durante

Creación del bundle HORMO FX Pack 40+ y su landing `/pages/pack-40-hormonal`. Costo: ~15 min debugging + 1 round-trip screenshot de Gibran.
