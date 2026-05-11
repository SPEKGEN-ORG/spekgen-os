---
name: @gibran.alonzo.ecom content production state
description: Estado de producción de contenido para la marca personal de Gibran. Posts producidos, pipeline, infraestructura creada.
type: project
---

## Estado (2026-04-08)

**Posts publicados (11 total):**
- GA-001 (Mi Historia) — Mar 13
- GA-004 (Imagen $0 vendio $12K) — Mar 20
- GA-005 (CLAUDE.md) — Abr 3 — IG: https://www.instagram.com/p/DWrvPf6lBUz/
- GA-006 (Inventario Sheets) — Abr 3 — IG: https://www.instagram.com/p/DWrvZoylKT4/
- GA-007 (Plugins Ep.1) — Abr 3
- GA-008 (Plugins EP.2 / Skills) — Abr 3 — IG: https://www.instagram.com/p/DWrwwD2FJpr/
- GA-009 (Meta App EP.1 — Publicar sin IG) — Abr 3 — IG: https://www.instagram.com/p/DWrxC6flDe0/
- GA-010 (Meta App EP.2 — Media Buying) — Abr 3 — IG: https://www.instagram.com/p/DWrxVNODsQk/
- GA-011 (TASKER) — Abr 3 — IG: https://www.instagram.com/p/DWrxkevlCTt/
- GA-012 (Forms HTML+Make) — Abr 3 — IG: https://www.instagram.com/p/DWrxybMlGpL/
- GA-027 (Deja de pagar apps — Content Hub portal) — Abr 8 — IG: https://www.instagram.com/p/DW4QG_rmSRQ/

**Pipeline (ideas sin producir):** GA-013 en adelante (ver GIBRAN_CONTENT_IDEAS.xlsx)

**Secuencia publicada 2026-04-03:**
```
GA-005 → GA-006 → GA-007(ya pub) → GA-008(Plugins EP.2) → GA-009(Meta EP.1) → GA-010(Meta EP.2) → GA-011(TASKER) → GA-012(Forms)
```
7 posts publicados en batch el 3 de abril. Scheduling via Meta API no funciona (whitelist error) — publicacion inmediata si funciona.

**Renumeracion 2026-04-03:** Doble pase. Primero: GA-018→010, GA-019→011, GA-020→012. Segundo: reordenado por contenido — GA-012(Skills)→008, GA-010(Meta1)→009, GA-011(Meta2)→010, GA-008(TASKER)→011, GA-009(Forms)→012.

## Meta API — Scheduling Limitation

La app SPEKGENAUTOADS NO tiene permiso para scheduled posts (`published=false` + `scheduled_publish_time`). Error: "User must be on whitelist". Publicacion inmediata SI funciona. Para scheduling futuro: usar Make scenario o cron alternativo.

## GA-008 TASKER — Producido 2026-04-03

- 8 slides Contrast Morado (estilo GA-007)
- Screenshots REALES del TASKER de Gibran (sunset theme, desktop real, vision board)
- Nombres de tareas censurados en todas las capturas
- Desktop screenshot con gaussian blur en panel TASKER
- Lead magnet: HTML template del TASKER
- CTA: DM "TASKER"
- Stats reales: 44 tocadas, 6 ciclos, CICLO 7, 29%, 5 pendientes

## Infraestructura creada

- `GIBRAN IG POSTS/_STRATEGY.md` — Estrategia con 2 ICPs (El Dueño + El Builder), pilares, funnel
- `GIBRAN IG POSTS/GA_SOCIAL_MEDIA_CALENDAR.xlsx` — Calendario operativo 5 sheets
- `GIBRAN IG POSTS/GIBRAN_CONTENT_IDEAS.xlsx` — Ideas raw de sesiones
- `GE-001/LEAD_MAGNET_CLAUDE_TEMPLATE.pdf` — PDF lead magnet para DM
- Playwright instalado para pipeline HTML→PNG de slides
- `/publish-post` skill — Publicacion directa IG+FB via Meta API (sin Content Hub)

## Producción visual

- **Estilo ganador v1:** "Contrast Morado" (GA-007/GA-008) — #120836 bg, #EDD9B4 cream, #A78BFA lavender, DM Serif Display + Inter, corner brackets, inverted blocks
- **Estilo ganador v2:** "Light Tech" (GA-027) — #FAFAF8 bg, dot grid, gradient morado-rosa (#7C3AED→#EC4899), orbs, gradient borders, browser frames para screenshots, Space Grotesk 700 + Inter + DM Serif Display
- **Covers:** Typography-first con CSS avanzado (no AI-generated — se ven fake)
- **Aspect ratio:** 4:5 (1080x1350). Playwright no soporta --device-scale-factor, usar viewport nativo 1080x1350
- **Nomenclatura:** Todos los posts son GA-XXX (no GE). GA-002 y GA-003 nunca existieron
- **Workflow:** HTML/CSS slides + Playwright render + `?render=N` mode para captura individual

## 2 ICPs definidos

1. **El Dueño:** Business owner $80K-500K MXN/mes → servicio done-for-you $8K-20K/mes (prioridad Q2)
2. **El Builder:** Agency owner/freelancer → cursos, Skool community (construir Q2, monetizar Q3)

**Why:** La marca personal es el canal principal para cerrar clientes nuevos y cubrir el gap de $64K MXN/mes.

**How to apply:** Todo contenido debe servir a ambos ICPs. El copy/CTA diferencia: ICP 1 → "DM para servicio", ICP 2 → "Comenta X y te mando la guía"

## Publicacion Flow (para /publish-post skill)

1. Pull .env.local de Vercel (Content Hub)
2. Subir imagenes de `00. IMAGENES FINALES/` o `00. WINNERS/` a Supabase Storage bucket `previews`
3. URLs publicas: `https://wjlwpfaogjpeqgyxxnwa.supabase.co/storage/v1/object/public/previews/gibran/GA-XXX/{file}`
4. Crear child containers en IG → carousel container → publish
5. FB Page post con primera imagen
6. Actualizar xlsx → Status "Publicado"
7. Eliminar .env.local
