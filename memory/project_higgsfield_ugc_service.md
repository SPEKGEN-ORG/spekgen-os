# Higgsfield Marketing Studio — UGC Video Service SPEKGEN

**Setup:** 2026-05-11
**Cuenta activa:** `spekgen.ai@gmail.com`, plan Starter $15/mo anual, 200 cr/mes
**Piloto:** 2 videos Fit Max (LF) generados — mode ugc_how_to, avatar Adriana, setting Kitchen

## Pricing de servicio (acordado con Gibran)

| Paquete | Precio MXN | Videos | Costo prod. (~$30/video) | Margen |
|---|---|---|---|---|
| Video individual | $480 | 1 | $30 | ~94% |
| Pack 10 | $3,000 | 10 | $300 | ~90% |
| Pack 15 | $4,000 | 15 | $450 | ~89% |
| Pack 20 | $5,000 | 20 | $600 | ~88% |

Costo: Ultra plan $70/mo anual ÷ 40 videos/mes = ~$1.75 USD/video (~$30 MXN a TC 17)

## Plan de upgrade

- Starter: 200 cr/mes = ~2 videos UGC (75 cr c/u) — solo para demos/pilotos
- Ultra Anual $70/mo: 3,000 cr/mes = 40 videos UGC/mes — para producción real
- Upgradeaar cuando cierre primer cliente (LF o GR)

## CLI: modelo marketing_studio_video

```bash
higgsfield generate create marketing_studio_video \
  --mode ugc_how_to \
  --avatars '[{"id":"AVATAR_ID","type":"preset"}]' \
  --medias '[{"type":"image","role":"image","data":{"id":"MEDIA_ID","type":"media_input"}}]' \
  --setting_id SETTING_ID \
  --generate_audio true \
  --aspect_ratio 9:16 \
  --duration 30 \
  --resolution 720 \
  --prompt "PROMPT"
```

## Limitación crítica: voz en español

`prompt_language` SIEMPRE sale `"en"` aunque el prompt esté en español. La voz del avatar es en inglés incluso con prompt en español. Workaround: Higgsfield Audio dubbing post-generation (no probado aún — requería créditos extra).

## Modos disponibles

ugc, ugc_how_to, ugc_unboxing, product_showcase (y más — ver `higgsfield marketing-studio settings`)

## Avatares disponibles (Starter)

Verificar con `higgsfield marketing-studio avatars` — hay varios preset disponibles (Adriana, etc.)

## Media upload

```bash
higgsfield media upload --file "path/to/image.webp"
# Devuelve media_id para usar en --medias
```

## Créditos por modelo

| Modelo | Créditos |
|---|---|
| marketing_studio_video | 75 |
| kling3_0 (cinematic) | 10 |
| wan2_7 / seedance_2_0 | 5 |

## Funnel recomendado por cliente

2 videos gratis (demo) → Pack 10 ($3K) → upsell Pack 20 + Audio dubbing español
