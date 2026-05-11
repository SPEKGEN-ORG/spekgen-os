---
name: campaign-architecture-pdf skill
description: Skill para generar PDF visual panorámico A3 de arquitectura de campañas publicitarias (cualquier cliente)
type: project
---

Skill global `campaign-architecture-pdf` creada 2026-04-09 en `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/campaign-architecture-pdf/`.

**Qué hace:** Toma un JSON describiendo una arquitectura de campaña (campañas → ad sets → fases → ads → landings) y genera un PDF visual panorámico A3 landscape (420×297mm) con thumbnails reales embebidos (base64) y placeholders automáticos para creativos pendientes.

**Stack:** Python single-file (`scripts/build_pdf.py`) + PIL (resize/base64) + Playwright chromium (HTML→PDF). No depende de Canva ni herramientas externas.

**Cuándo usarla:** SIEMPRE que se defina o refine una estrategia/arquitectura de campaña para cualquier cliente (HC, LF, GR, MG, Gibran Ecom, nuevos). Gibran es extremadamente visual y se pierde con .md/Google Docs — el PDF visual es obligatorio acompañando cada estrategia.

**Files clave:**
- `SKILL.md` — activación + flujo completo (pre-flight, build, verify, entrega)
- `scripts/build_pdf.py` — builder self-contained (CSS embebido + renderers + CLI)
- `templates/schema.md` — docu del formato JSON de entrada
- `examples/hc_meta_ads_mes1.json` — input completo de referencia (HC Mes 1, 2 páginas)

**Validada:** 2026-04-09 regenerando el PDF de HC end-to-end (839.8KB, visualmente idéntico al original). El PDF original vive en `HC/05. META ADS/CAMPAÑA MES 1/00. ESTRATEGIA/HC_ARQUITECTURA_META_ADS_MES1.pdf`.

**Why:** Gibran pidió que SIEMPRE que definamos estrategias/estructuras de campañas se arme un PDF visual así, con placeholders cuando los creativos no existan todavía, para HC y todos los clientes. El flujo anterior (hacer el build ad-hoc cada vez) no escala.

**How to apply:**
1. Cada vez que termines de escribir/refinar una estrategia de campaña, generar el PDF como parte del deliverable.
2. Guardar el input.json en `{CLIENT}/05. META ADS/{CAMPAÑA}/00. ESTRATEGIA/_arquitectura_build/input.json` para regenerar rápido si algo cambia.
3. Para clientes nuevos con productos distintos, agregar clase CSS `.prod-<code>` y `.ad-card.<code>` en `build_pdf.py` (dentro de la constante `CSS`).
4. Invocación: `python3 "{SKILL_DIR}/scripts/build_pdf.py" "{path/al/input.json}"` (respeta `meta.output_pdf` del JSON o usa `--output`).
