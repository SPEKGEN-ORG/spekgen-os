---
name: HC Content Whiteboard PDF mensual
description: Patron de planning visual mensual para feed organico HC. PDF A3 landscape con cover stats + N estilos × 6 posts. Reusable cross-client.
type: project
originSessionId: be1e8cc7-81f5-4115-9c11-52f93c5d4ac9
---
**Qué es:** PDF whiteboard A3 landscape que mapea el feed orgánico de un mes completo, agrupado por estilo visual. Cover con stats globales (producidos / target / mix) + página por estilo con grid 3×2 de tiles + meta strip (pilar/objetivo/mix/producidos).

**Why:** entregable visual para alinear con el equipo cliente sin tener que armar deck nuevo cada mes. Vibe sketch/post-it (cinta adhesiva, papel grid sutil, sombras hand-drawn) hace que se sienta planning vivo, no doc corporativo. HC mayo 2026 fue el primer mes que lo usó — 4 estilos: MEME LIKE / TIPS / VERDAD O MITO / SABÍAS QUE.

**How to apply:**
- Path master: `SPK - 15. FACTORY/content/BATCH_{CLIENTE}_{fecha}-v{N}/_planning/build_whiteboard.py` (idempotente, lee dict STYLES con files+post_ids+hooks por estilo).
- Path share filtrado: `_planning/build_memelike_share.py` (o equivalente por estilo) — cover narrativo "X listas, Y en producción, Z total" + 1 página del estilo en review. Útil para mandar previews al equipo cliente conforme cada estilo va saliendo.
- Output PDFs en raíz del batch: `{CLIENTE}_CONTENT_MAP_{MES}_{YYYY}.pdf` + `_MEMELIKE.pdf` (o el estilo del share).
- Stack: HTML + Playwright PDF (mismo stack de `/cross-client-intel` y `/publish-monthly-report`).
- Tipografía: Anton (mega numerals/títulos), Nunito 600-900 (body), JetBrains Mono 700 (etiquetas/slot numbers).
- Paleta: cream `#FFFCEF` + teal `#1A9B8C` + naranja `#E8852E` + dark `#0F2A2C` (HC v7 colors). Para otros clientes: ajustar a su paleta.
- Tiles con object-fit:contain (no cover) + bg `#F2EBD3` para letterbox tipo polaroid — preserva imágenes 4:5 sin crop agresivo.
- Grid auto-rows 88mm para que 6 tiles caben en 2 filas de página A3 sin overflow.

**Cuando regenerar:** cada vez que llegue un nuevo lote de imágenes (ej. estilo 02 termina), actualizar dict STYLES (`files`, `post_ids`, `hooks`) y re-correr. PDF se sobrescribe.

**Replicable a:** GR, LF, MG (cualquier cliente con feed orgánico mensual planeado por estilos). Solo cambiar paleta + textos del cover. Estructura del script es agnóstica.
