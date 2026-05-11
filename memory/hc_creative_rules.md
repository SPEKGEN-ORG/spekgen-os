---
name: HC Creative Rules (Dynamic)
description: Dynamic creative rules for Healthy Chuchos — organized by type (copy, visual, targeting, hooks). Updated automatically by Creative Learner agent. NOT fixed per product.
type: feedback
---

## Reglas Permanentes (Non-negotiable)

1. **COFEPRIS:** NUNCA mencionar en material público. Alternativas: "Nutracéutico Veterinario", "Hecho en México", "Formulación con Evidencia", "Sin Rellenos Inertes"
2. **SENASICA:** Usar lenguaje de "apoya", "contribuye", "soporte nutricional". NUNCA "cura", "antibiótico", "medicamento"
3. **VistaChu:** Excluido de Fase 1. No sale a la venta
4. **Copy aprobado es INTOCABLE:** NUNCA cambiar copy aprobado sin consultar a Gibran. Es la regla más importante
5. **No asumir conceptos:** Proponer opciones y esperar aprobación antes de generar

## Reglas Validadas (Data-backed)

### Copy & Hooks
- **Hook de curiosidad gana:** "¿Sabías que...?" baja la guardia del scroll. Formato educativo conversacional > cifras directas
- **DOLOR = situación del dueño:** El hook más potente para ads de dolor NO es "perro sufriendo" sino "dueño desesperado en situación reconocible" (ej: 3AM googleando)
- **Precio como arma:** $799 tachado → $381-$397 (52% ahorro). Pero en TOFU, autoridad primero — el precio lo ve en la PDP
- **Arco PROBLEMA→CIENCIA→SOLUCIÓN:** Formato ganador para multi-slide ads
- **Mini-carrusel (2-3 slides):** Estándar consolidado. No hacer single-image cuando se puede contar historia

### Visual / Imagen
- **Hyperrealism block ESENCIAL** para renders de perros — sin él, Gemini produce cartoon/anatomía incorrecta
- **3 variaciones (A/B/C)** por imagen con diferentes ángulos — mejor ratio de winners
- **V1 tiende a ganar:** Invertir más tiempo en el prompt que en variaciones. La primera ejecución suele ser la más fiel al concepto
- **Perros con ACTITUD > perros genéricos posando.** La expresión del perro ES el scroll-stop
- **Perros MADUROS (5-8 años, canas)** para dolor articular. Razas grandes: Bernese, Golden, Saint Bernard
- **Ads siempre AD-READY con texto integrado:** El copy va dentro del prompt como ABSOLUTE TEXT RULE. No generar text-free
- **Referencia como primer attachment = estilo dominante.** El orden de refs importa
- **Color dominance:** Cada producto tiene universo cromático de etiqueta. Un solo color domina el frame

### Gemini API — Receta Correcta (2026-04-07)
- **Modelo:** `gemini-3.1-flash-image-preview` SIEMPRE. No usar gemini-3-pro ni gemini-2.5-flash
- **Prompt en INGLÉS**, textos de la imagen en español. Si todo va en español, calidad baja
- **10 bloques estructurados:** FORMAT OPENER, VISUAL IDENTITY, COMPOSITION, TEXT CONTENT, PRODUCT IDENTITY, CHARACTER DESCRIPTION, ABSOLUTE TEXT RULE, DISCLAIMER, COHERENCE, NEGATIVE INSTRUCTIONS
- **Orden de refs (CRITICO):** 1. Mockup producto → 2. Winner aprobado (quality ref) → 3. Fotos reales perros (2-3) → 4. Ref de template → 5. Prompt
- **Negativos exhaustivos:** "NO cartoon dogs, NO illustrated dogs, NO plush toy looking dogs, NO generic bottles, NO amber capsules, NO colored powders"
- **Fotos reales de perros** de `14. REFERENCIAS/` adjuntas SIEMPRE. Sin ellas = ojos muertos y pelaje plástico
- **Winner como quality ref:** Adjuntar un ad/post APROBADO le dice a Gemini "la barra de calidad es esta". Gemini copia calidad sin copiar colores
- **Consistencia de perro:** Generar 1 foto de referencia del perro y adjuntarla en CADA slide del carrusel
- **HC_VISUAL_RULES.md** en `06. SOCIAL MEDIA/` — LEER OBLIGATORIO antes de cada generación
- **Skill `gemini-image-gen`** en `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/`

### Productos HC — Especificaciones Visuales
- ArtriDog/DogRelax/GastroDog = FRASCOS CORTOS Y ANCHOS BLANCOS con POLVO
- OmegaDog = BOTELLA ALTA BLANCA con CÁPSULAS ROJO RUBÍ OSCURO / BURGUNDY
- NUNCA polvos de colores fantasía esparcidos
- NUNCA productos genéricos de vidrio oscuro
- Mockups en `02. PRODUCTOS/03. MOCK UPS/`

### Formatos Específicos
- **Mantesso style:** Fondo off-white #F7F5F2 PURO (nunca gradiente), foto hyperrealista, doodle tinta negra. Raza: Schnauzer negro
- **Split DOLOR/CALMA:** 8% header / 42% top / 2% divider / 40% bottom / 8% branding
- **Slide de reveal:** Perro feliz + producto + cierre narrativo. NUNCA solo producto con checkmarks
- **Paper Tear:** Papel rasgado revelando anatomía — formato potente para "ciencia visual"

### Naming & Proceso
- Winners se nombran con CONCEPTO (TECLADO3AM, BILLBOARD) — no con número de ronda
- **3 rondas estándar:** R1 dirección, R2 refina, R3 entregable final
- Convención: HC_AD_[PRODUCTO]_S[#]_CONCEPTO_1x1.png
- Reutilizar slides entre ads si encajan — slides de "solución" son módulos reutilizables

## Hipótesis a Probar (sin data aún)

- ¿Los ads de DogRelax responden igual al framework DOLOR que GastroDog/ArtriDog?
- ¿OmegaDog (omega-3, skin/coat) necesita un approach visual diferente? (menos "dolor", más "brillo/vitalidad")
- ¿El formato "¿Sabías que?" funciona igual en retargeting que en TOFU?
- ¿Carruseles orgánicos de 6+ slides tienen mejor engagement que 3-slide ads?

**Why:** Rules dinámicas permiten que el sistema aprenda y mejore. Las "validadas" son data-backed de 3 batches de ads (GastroDog, ArtriDog, DogRelax). Las "hipótesis" se moverán a validadas o se descartarán conforme el Creative Learner (A12) analice performance.
**How to apply:** Cada agente que genera copy/imágenes/contenido DEBE leer este archivo primero. El Creative Learner actualiza este archivo automáticamente.
