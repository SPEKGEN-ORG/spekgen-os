---
name: Meta Ads API — IG dropdown y reglas críticas
description: Reglas inmutables para subir ads a Meta via API. instagram_user_id DENTRO de object_story_spec (no top-level) — y otras 6 reglas críticas.
type: feedback
---

**NUNCA subir ads a Meta con curl ad-hoc o scripts one-off.** Siempre usar `/spekgen-meta-ads-upload` (skill global en `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/spekgen-meta-ads-upload/`). Si lo haces ad-hoc, te vas a olvidar de `instagram_user_id` dentro de `object_story_spec` y los ads saldrán con el dropdown de IG vacío en Ads Manager.

**Why:** Sesión GREENRAY 08-09 abril 2026: subí 7 ads ad-hoc con curl porque el skill greenray-meta-upload tenía el script pendiente. Los 7 salieron con IG guardada top-level. Gibran detectó que el dropdown "Cuenta de Instagram" salía vacío. Tuve que debuggear durante horas probando: `instagram_actor_id` (rechazado por cross-BM system user), varias versiones del API (v19-v22, todas fallaron), scoped IDs, page-backed IG, token swaps — nada funcionó hasta que descubrí la regla: **`instagram_user_id` va DENTRO de `object_story_spec`, no top-level**. Reemplacé los 7 creatives y funcionó. Lección: las 7 reglas críticas documentadas en REFERENCE.md del skill son ley.

**How to apply:**
1. Cada vez que Gibran pida trabajo de Meta Ads API → invocar `/spekgen-meta-ads-upload`, NO improvisar con curl
2. El skill incluye `meta_diagnose.py` que valida prerequisites antes de cualquier upload (token, page, IG, pixel, scopes, sanity check del último creative)
3. El skill incluye `meta_upload.py verify-ad --ad-id X` que confirma que el creative está bien configurado (IG en OSS + UTMs)
4. El skill incluye `meta_upload.py fix-creative --ad-id X` que repara ads rotos reemplazando el creative
5. Las 7 reglas críticas están en SKILL.md — memorizarlas:
   - IG `instagram_user_id` DENTRO de object_story_spec (nunca top-level solamente)
   - NUNCA usar `instagram_actor_id` (cross-BM system user lo rechaza)
   - Pixel en `promoted_object` del ad set (no en `tracking_specs` del ad)
   - Advantage+ audience requiere `targeting_automation: {advantage_audience: 1}` y `age_min ≤ 25`
   - Dynamic Creative: 1 ad por ad set + `ad_formats: ["SINGLE_IMAGE"]`
   - Traffic attribution: solo `CLICK_THROUGH 1-day`
   - `url_tags` en el creative (inmutable — para editar hay que crear creative nuevo)
6. Si ves el error `"must be a valid Instagram account id"` → estás usando `instagram_actor_id` → cambiar a `instagram_user_id`
7. Si Gibran dice "el IG no aparece seleccionado en el dropdown" → correr `verify-ad`, luego `fix-creative`
