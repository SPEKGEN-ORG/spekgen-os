---
name: Prompts Gemini MG deben ser Liquid Glass v5.5 (cinematográfico conceptual), NO editorial tipográfico
description: Patrón de prompts para Gemini 2.5 Pro en batches MG (content orgánico B2B). Estilo canónico Liquid Glass v5.5 — mesh dark green + halos teal/amber/pink + metáforas visuales. Rechazado: editorial-typographic Kinfolk/poster.
type: feedback
originSessionId: 7c9dda25-0096-4ccb-b43a-0f27ae42bfd5
---
Cuando Gibran pide "estilo MG premium" para ads o content orgánico B2B, la aesthetic correcta es **Liquid Glass v5.5 cinematográfico-conceptual** (metáforas físicas + halos + glassmorphism cards), NO editorial-typographic magazine style.

**Why:** Batch MG-006→012 primera corrida tuvo dos fallas seguidas:
1. Primera corrida: prompts vagos → amber vials stock-looking y Canva cards con checkmarks verdes (anti-MG).
2. Rewrite v2 (mío): asumí que las referencias MG en carpeta FINAL (Kinfolk off-white editorial con tipografía gigante gradient green→purple) eran el target. Escribí prompts layout-first con canvas off-white + pills + chrome editorial. Gibran rechazó directo: **"nah broski, the styles are still ass"** y me mandó el legacy dashboard del día anterior como referencia correcta.

El estilo validado (legacy `_build_dashboard.py` en `SPK - 15. FACTORY/_archive/MG_SEMANA2_MG006-MG012_LEGACY_DEPRECATED_2026-04-22/`) es otra cosa completamente distinta.

**How to apply — sistema Liquid Glass v5.5 canónico para MG prompts:**

1. **Empezar con ROL + estilo explícito**: "ROL: Director de arte industrial premium. ESTILO: Liquid Glass v5.5 industrial. Mesh radial dark green #093D25 con halos teal #33BA9E y amber #F59B56. NUNCA azul corporativo monocromático (anti-GCAB)."

2. **Describir la ESCENA cinematográfica con metáfora física** (NO layout de póster):
   - Dropshipping / capital atorado → bloque de hielo translúcido con cajas congeladas, billetes de $500 MXN atrapados, grietas iluminadas, vapor frost.
   - Stock-out / urgencia → anaquel de farmacia con slots vacíos + tags «AGOTADO» + rim pink #D44A7A.
   - Autoridad / secretos → laboratorio oscurecido + documento glass con texto tachado pink simulando censura.
   - Solución operativa → glassmorphism card premium (backdrop-filter blur(20px) saturate(140%), border rgba(255,255,255,0.18), rounded-2xl) + halo teal dominante.

3. **Texto como overlay editorial FUERTE pero DENTRO de escena**: Inter Black 900 para headlines (50-68pt), white + un color de acento (amber para dolor, teal para solución, pink para tensión máxima). Usar ABSOLUTE TEXT RULE con comillas angulares «...».

4. **Continuidad visual estricta en carruseles via SEED**: slide 1 es el HERO, slides 2+ citan explícitamente `MG-XXX_SEED.png` como anchor ("CONTINUIDAD VISUAL ESTRICTA con MG-XXX_SEED.png — misma paleta, mismo estilo Liquid Glass, mismo watermark y posición").

5. **Chrome mínimo, NO editorial pills/caps**:
   - WATERMARK: "Logo MG en esquina inferior derecha, 80px, 70% opacidad."
   - SWIPE INDICATOR (si carrusel): «DESLIZA →» bottom-left, Inter SemiBold 600 14pt cream 50%.
   - Sin pills top-left editoriales. Sin "METAGREEN LABS" tracking +0.3em top-right. Esos son del sistema editorial que Gibran rechazó.

6. **Numerales ghosted como profundidad** (en slides de carrusel): Inter Black 900 420-520pt, 8-15% opacidad, color match palette, blur leve, bleed-style (recortado por bordes).

7. **Inversión visual para CTA final** (último slide de carrusel): el glass card translúcido se vuelve teal #33BA9E SÓLIDO como CTA plate gigante — ejemplo en legacy MG-012 slide 5.

8. **CANVAS cierre obligatorio**: "CANVAS: 1080×1350 px (4:5). Render nítido. Sin personas, sin texto adicional, sin emojis, sin azul monocromático."

**Referencia canónica del patrón:**
- Legacy prompts: `SPK - 15. FACTORY/_archive/MG_SEMANA2_MG006-MG012_LEGACY_DEPRECATED_2026-04-22/_build_dashboard.py` (líneas 75-600).
- Piloto validado v3: `/tmp/build_mg_batch.py` (2026-04-22, batch BATCH_MG_2026-04-22-v1).

**Cuándo NO aplicar este patrón:**
- HC (diferente sistema: foto realista + split-screen emocional).
- GR (PDP landing — más producto-forward).
- LF (ad-driven, performance first, no editorial).
- Gibran Ecom (foto real backgrounds — ver feedback_gibran_ecom_photo_backgrounds.md).
- MG ads de performance (no content orgánico) — puede necesitar variante más directa.
