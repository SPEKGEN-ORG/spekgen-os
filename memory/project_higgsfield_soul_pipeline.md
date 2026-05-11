# Higgsfield Soul Pipeline — SPEKGEN

**Onboarded:** 2026-05-07
**Cuenta:** Higgsfield CLI autenticado a Gibran personal, workspace Private, plan free, 5 créditos al onboarding

## Skills disponibles

**Oficiales (instaladas via `npx skills add higgsfield-ai/skills`):**
- `higgsfield-generate` — wrapper general T2I/I2I/I2V/T2V + Marketing Studio
- `higgsfield-soul-id` — train Soul Character (low-level, focused en personas)
- `higgsfield-product-photoshoot` — imágenes brand-quality producto vía GPT Image 2 (no entrena Soul)
- `higgsfield-marketplace-cards` — cards estilo Amazon

**SPEKGEN custom:**
- `/hf-soul-prep` — pipeline end-to-end Soul training (productos + personas). Path: `SPK - 02. SKILLS/GLOBALES/hf-soul-prep/`

## Pricing crítico verificado

| Modelo | Costo | Nota |
|---|---|---|
| Soul V2 / Cinematic / Cast | **0.12c** | Killer: ~40 gens/credit. Soul Cast = video |
| FLUX.2 | 1c | |
| Nano Banana Pro / Cinematic Studio / Marketing Studio | 2c | |
| Veo 3.1 / Kling 3.0 | 22c | Out of free tier |

## Decisión arquitectural: Gemini para mockups, Higgsfield para Soul

Para entrenar un Soul se necesitan 5-20 imágenes de input. Generarlas en Gemini Nano Banana Pro web UI (gratis con Google One Pro) en lugar de Higgsfield ahorra ~16 créditos por Soul. Higgsfield créditos se reservan SOLO para Soul training (lo único que Gemini no hace).

Pipeline 5 fases (skill `/hf-soul-prep`):
A. Init batch folder + PROMPTS.md
B. Generar 8 mockups en Gemini Nano Banana Pro (gratis)
C. Upload Higgsfield + train Soul 2.0
D. Test gen
E. Registro en `_SOUL_REGISTRY.md`

## Souls planeados

- **HC productos:** ArtriDog (piloto), DogRelax, GastroDog, OmegaDog, VistaChu
- **GR productos:** ARTRIX, otros
- **LF productos:** MetaFit, otros
- **MG productos:** TBD
- **Personas:** Gibran (marca personal @gibran.alonzo.ecom — Japan-proof content)

## Reglas

- Soul 2.0 (`--soul-2`) para productos (preserva geometría/etiqueta)
- Soul Cinematic (`--soul-cinematic`) para personas
- Aspect ratio 1:1 obligatorio en training inputs
- Identity Lock prefix + SCALIST framework en prompts Gemini (research `Gemini Image Generation Realism Research.txt`)
- Score mínimo 8/10 (rubric Gemini Realism Research) por imagen antes de subir a training
