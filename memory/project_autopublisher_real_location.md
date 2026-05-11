---
name: Autopublisher real location (GH Actions Python, NOT Edge Function)
description: Content Hub autopublisher real es script Python en GH Actions (g-bran/Spekgen-ops, content-hub-autopublisher.yml cron 7 * * * *). NO la Supabase Edge Function ni Make 4682719
type: project
originSessionId: d2c4c31d-c80a-48f2-9ee3-aedaaa8ffdcd
---
El autopublisher del Content Hub que **realmente corre cada hora** es un script Python en GitHub Actions, NO la Supabase Edge Function ni Make scenario 4682719.

**Realidad (verificada 2026-05-02 durante incidente MG-013):**
- Repo: `g-bran/Spekgen-ops`
- Workflow: `.github/workflows/content-hub-autopublisher.yml` con cron `7 * * * *` (cada hora a :07)
- Script: `scripts/content-hub-autopublisher/autopublisher.py`
- Secrets requeridos: `SHOPIFY_SHOP`, `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `META_TOKEN`, `MAKE_WEBHOOK_URL` (para email de resumen)
- Filter: `status=approved AND scheduled_datetime <= now_mx AND ig_post_url empty AND fb_post_url empty AND date_published empty` (post-fix 2026-05-02)
- Update path: status=published + date_published ISO + ig_post_url + fb_post_url. Si falla → status=publish_error (fallback para evitar re-publish loop).

**La Edge Function `auto-publish` en Supabase EXISTE** (`SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/edge-functions/auto-publish/index.ts`, project `wjlwpfaogjpeqgyxxnwa`) pero **NO está siendo invocada** por nada. Es código muerto / candidato a borrar. Memoria anterior decía que era el real autopublisher — incorrecto.

**Make 4682719 nunca existió** en team 354061.

**Why:** Incidente MG-013 (2026-05-02): MG-013 publicó 16 veces a IG+FB MetaGreen entre 5/1 17:10 y 5/2 17:02 MX. Investigación reveló que la GH Actions ejecutaba cada hora con `completed success` y publicaba el post — pero el `metaobjectUpdate` post-publish fallaba silenciosamente porque el script usaba keys equivocados (`ig_permalink`/`fb_post_id` cuando los reales son `ig_post_url`/`fb_post_url`). Status quedaba `approved` y al ciclo siguiente re-publicaba.

**How to apply:** Cualquier cambio al autopublisher orgánico (HC/GR/MG/Gibran) → editar `autopublisher.py` en repo Spekgen-ops, NO la Edge Function. Si necesitas pausar todo → `gh workflow disable content-hub-autopublisher.yml --repo g-bran/Spekgen-ops`. Para dry-run → `gh workflow run ... -f dry_run=true`. Fix del bug + dedup guards en commit 596d765.
