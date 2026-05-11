---
name: HC Operational State
description: Real-time operational state of Healthy Chuchos — ad pipeline, social media organic, infrastructure, blockers, tracking, and pending actions.
type: project
originSessionId: 943ba8df-f54f-424a-9d98-94db50bd4e21
---
## Contacto HC
- **WhatsApp:** `3326402219` (México) — `https://wa.me/523326402219`
- Widget flotante instalado en todo el sitio (live 2026-04-14), `snippets/hc-whatsapp-widget.liquid`

## Clarity Metrics — Último A1 Run (2026-04-16, 24h + 3 días)

### 24h (Abr 15-16) por Device
| Métrica | Mobile | PC |
|---------|--------|----|
| Sesiones reales | 0 (3 totales = 3 bots) | 2 |
| Sesiones bot | 3 | 0 |
| Scroll depth promedio | 38.57% (bots) | 17.67% |
| Engagement activo | 104s (bots) | 27s |
| Dead clicks | 0% | 50% (1/2 ses.) |
| Rage clicks | 0% | 0% |
| QuickBack clicks | 0% | 0% |
| Script errors | 33% / 1 evento (bot ses.) | 0% |

NOTA (Abr 16): Tráfico real bajísimo — solo 2 sesiones PC reales. Mobile = solo bots. Sin señal orgánica meaningful. Ads activos confirmados via UTMs en 3d.

### Top URLs por sesiones (3 días Abr 14-16)
| URL | Ses. | Notas |
|-----|------|-------|
| Homepage (/) | 12 | — |
| /products/artridog (orgánico) | 10 | Principal PDP orgánico |
| /products/artridog (UTMs paid) | >15 (múltiples variantes) | hc-ventas-mes1 + NUEVO hc-artridog-mes1 |
| /products/dogrelax | 4 orgánico + 3 paid UTMs | hc-ventas-mes1 activo |
| /pages/tienda | 3 | 33% dead clicks |
| /pages/distribucion | 2 | — |
| /collections/all | 2 | — |
| /products/gastrodog | 1 + 1 paid UTM | hc-ventas-mes1 activo |
| /cart | 1 | Intención de compra presente |
| /products/omegadog | 1 | — |

⚠️ NUEVO DETECTADO (Abr 16): UTM `hc-artridog-mes1` con ad_id `6913720802034` (hc-ad-oferta-v2) — campaña/ad diferente a los 6 organic winners de hc-ventas-mes1. Posible nuevo ad lanzado manualmente. Verificar en Meta.

⚠️ ArtriDog paid landing (ad_id 6911066326834): 100% dead clicks en 1 sesión UTM — CTA no funciona.

CRO findings actualizados (Abr 16):
- ArtriDog domina tráfico (10 ses. orgánicas + >15 paid en 3d)
- Dead clicks en landing paid de ArtriDog (100% en sesión UTM) — CRO crítico
- /pages/tienda: 33% dead clicks (recurrente)
- Script errors: mobile 33% (1 evento en bot session)

A3 comment ClickUp: 90170198854491 (task 86e0c4m07)

## Social Media Orgánico — Semanas 1-4 (actualizado 2026-03-31 sesión 3)

**Estrategia:** Organic-first. Mes 1 = 28 posts orgánicos. Mes 2 = winners a Meta Ads ($4,000 MXN).

**Calendario ajustado 2026-03-31:**
- S14 (Mar 30 - Abr 5): 4 posts → Lun/Mie/Vie/Dom (NO martes/jueves/sábado)
- S15+ (Abr 6 en adelante): diario (7/semana)
- Último post: HC-028 → Lun 27 abril

**Posts publicados:**

| Post | Fecha | Producto | Status |
|------|-------|----------|--------|
| HC-009 | Mar 24 | GastroDog | Publicado |
| HC-002 | Mar 26 | DogRelax | Publicado |
| HC-003 | Mar 30 | DogRelax (Mantesso 6 slides) | Publicado |

**HC-004 — URGENTE (publicar Abr 1 a las 10am):**
- Supabase: status=Programado, date_planned=2026-04-01, best_posting_time=10:00
- Imágenes: 2 previews en Supabase Storage (TEAR + MECANISMO)
- Copy: corregido con tildes/ñ
- ig_post/fb_post: limpiados (Gibran borró posts anteriores)
- BLOCKER: necesita Make.com scenario para disparar POST /api/publish a las 10am

**Próximos posts (esta semana):**

| Post | Fecha | Día | Producto | Imagen | Status |
|------|-------|-----|----------|--------|--------|
| HC-004 | Abr 1 | Mie | ArtriDog (TEAR+MECANISMO, 2 slides) | LISTAS | Programado — pendiente Make |
| HC-005 | Abr 3 | Vie | OmegaDog (krill vs pescado, 6 slides) | PENDIENTE | Brief listo |
| HC-006 | Abr 5 | Dom | GastroDog (3 fases, 6 slides) | PENDIENTE | Brief listo |

## Auto-Publishing System (OPERATIVO — actualizado 2026-04-08)

**Endpoint:** `GET/POST /api/auto-publish` (spekgen-hub.vercel.app)
- Auth: `Authorization: Bearer {CRON_SECRET}`
- GET handler agregado 2026-04-08 para compatibilidad Vercel Cron (commit 89aab74)
- Busca posts status=`approved` (date_planned=hoy, time_planned<=ahora) + status=`scheduled` (publicar ahora, sin filtro de tiempo)
- Publica IG carousel + FB multi-photo (independientes)
- Usa Page Access Token derivado de META_TOKEN_{SLUG}
- Retries con backoff para errores transitorios
- **"Publicar ahora":** approve endpoint dispara auto-publish en background automaticamente (fix 2026-04-07)

**Notificaciones email (2026-04-07):** `notifyGibranClientActivity()` envia email a Gibran cuando cliente toma accion en portal (approve, reject, copy edit, image revision, proposal accept/reject).

**Automatizacion doble capa (2026-04-08):**
- **Make.com Scenario NUEVO:** ID 4682719, "SPEKGEN Auto-Publisher (All Clients)", cada 60 min, ACTIVO, carpeta SPEKGEN—Agency. Cubre TODOS los clientes.
- **Vercel Cron (backup):** vercel.json con 2 crons (11 AM + 5 PM MX). Auto-auth via CRON_SECRET env var.
- **Make.com Scenario ANTERIOR:** ID 4657645, cada 3h — posiblemente redundante, considerar desactivar.
- **Scheduled task local:** `hc-daily-autopublisher` desactivada (ya no se necesita).

**Vercel Env:** CRON_SECRET + META_TOKEN_HC
**Publicados via API:** HC-006 (FB only, IG caida), HC-009 (IG+FB 2026-04-07), HC-010 (IG+FB 2026-04-08)

## Content Hub (Portal de Cliente)

- **Portal cliente:** https://spekgen-hub.vercel.app/portal/3b22f35e-975e-4e50-b913-85ea5baa3925
- **Dashboard admin:** https://spekgen-hub.vercel.app/dashboard/hc
- **Portal features (2026-04-07):** Caption edit, AI Image Revision (slide selector + before/after proposals), star rating (1-5 obligatorio), hora de publicacion visible, "Publicar ahora", email notifications a Gibran
- **WhatsApp notifications:** Descartadas.
- **PDF guia funcionalidades:** Creada, entregada a Gibran, movida a `01. BRAND MEDIA/CONTENT HUB UPDATES PDF/`

## Ad Pipeline por Producto (actualizado 2026-04-09)

**Plan v1 (ad batch original) DEPRECADO.** Reemplazado por Plan v2.0 (organic winners).

### Plan v2.0 — Mes 1 (HC-VENTAS-MES1) — 6 organic winners PAUSED

| # | Ad Name | Ad ID | Producto | WCI | Slides |
|---|---|---|---|---|---|
| O1 | HC-AD-DOLOR-SILENCIOSO-CAROUSEL | 6911066326834 | ArtriDog | 9.81% | 3 |
| O2 | HC-AD-CURCUMINA-CAROUSEL | 6911066345034 | ArtriDog | 7.64% | 3 |
| O3 | HC-DR-OFF-CAROUSEL | 6911066358834 | DogRelax | 7.57% | 6 |
| O4 | HC-OD-OMEGA-EQUIVOCADO-CAROUSEL | 6911066375434 | OmegaDog | 7.18% | 6 |
| O5 | HC-DR-ESTRES-CAROUSEL | 6911066404634 | DogRelax | 6.41% | 6 |
| O6 | HC-GD-REGENERACION-CAROUSEL | 6911066427234 | GastroDog | 4.40% | 6 |

Status: **PAUSED/IN_PROCESS review**. Budget $120 MXN/día. Campaña PAUSED hasta GO manual.

Legacy v1 ads pausados: HC-DR-001, HC-GD-001, HC-AD-001 (los CIENCIA/AUTORIDAD del batch original nunca se usaron).

**Bloqueos pre-GO:** código CHUCHO10 + 4 email flows Shopify + test purchase end-to-end. Ver `project_hc_meta_ads_mes1_setup.md`.

## Infraestructura Meta

| Componente | Status | ID |
|-----------|--------|-----|
| BM | OK | HealthyChu (880354658373862) |
| Ad Account | OK | act_1626923298353925 |
| Page ID | OK | 102627388012544 |
| IG Account | OK | 17841430824981516 |
| Pixel | OK | 1813096612719811 |
| CAPI | OK | Vía Shopify (Maximum) |
| System User | OK | SPEKGENAUTOADS |
| Token | OK | Válido (smoke test 2026-03-31). Publish inmediato funciona, scheduling NO. |

## Tracking Stack

| Herramienta | Status | ID |
|------------|--------|-----|
| GA4 | OK | G-V2FL067WSM |
| Clarity | OK | vy5jjgw9yi |
| Meta Pixel | OK | 1813096612719811 |
| CAPI | OK | Vía Shopify |
| Search Console | BLOCKED | Dueña HC |

## Cola de Acciones Pendientes

1. **CRITICO: Regenerar token Meta HC con permisos IG** (86e0p34k6 + 86e0q1tg8) — DÍA 19+. Bloquea publicación IG automatizada. NOTA: 86e0r1fgr RESUELTO (2026-04-08) — token de monitoreo/ads ya funciona. Task 86e0qxn1b (0 ads activos) — verificar si ads volvieron con token resuelto.
2. **CRITICO: S15 inicio HOY (Abr 6-12) con 0% producido** — HC-008 a HC-014 (7 posts). S14 cerró con HC-005/006/007 saltados.
3. **URGENTE: Producir OmegaDog Batch 01 para ads** — DÍA 19+ sin producción (86e0gcgpt "to do")
5. **Generar imágenes HC-006 a HC-010** — briefs listos
6. **Configurar GHL workflow para keyword ARTRI** — Gibran lo hace manualmente
7. **Resolver auto-publishing a largo plazo** — Make.com scenario reutilizable (necesita fix permisos MCP o endpoint sin auth)
8. **Fix MCP Make permisos** — reconectar con scopes de activate/update/run
9. Producir Semana 2+ contenido (HC-011 a HC-028)
10. Configurar ManyChat a 500+ followers

## Ultimo Check A1 Morning Intelligence
- 2026-04-16 09:00 CST — Brief posteado ClickUp comment 90170202043813. Clarity OK: 24h — 0 ses. mobile reales (3 bots), 2 ses. PC reales. Tráfico real bajísimo. Dead clicks PC 50% (1/2 ses.). Script errors: mobile 33% (1 evento en bot). 3d: Homepage 12 ses., ArtriDog 10 ses. orgánicas + >15 paid (hc-ventas-mes1). NUEVO: campaña hc-artridog-mes1 / ad_id 6913720802034 (hc-ad-oferta-v2) detectada — diferente a los 6 organic winners. ArtriDog paid landing 100% dead clicks (1 sesión UTM) — CRO crítico. /cart 1 sesión. ClickUp MCP disponible. Blockers sin cambio: Token IG DÍA 31 (86e0p34k6+86e0q1tg8), OmegaDog DÍA 31 (86e0gcgpt), script errors VENCIDA 9d (86e0t9yab), 0 ads blocker (86e0qxn1b — posible cambio si ad 6913720802034 está activo). S16 DÍA 4/7 con 0/7.
- 2026-04-15 09:00 CST — Brief compilado. ClickUp MCP NO disponible. Clarity OK: 24h — 2 ses. mobile reales (-91% vs 22 Apr 12), scroll 50% (↑↑), engagement 66s (↑↑) — calidad alta, volumen muy bajo. Script errors: 2 eventos, 50% ses. mobile. 3d: ArtriDog 7 ses. reales (top), DogRelax múltiples paid UTMs (hc-ventas-mes1 activo), GastroDog 1 ses. Script errors: GastroDog 100% (4 err), DogRelax 100% (4 err), ArtriDog 14% (2 err). Ads posiblemente activos post token-fix Apr 8 (UTMs presentes). Blockers sin cambio: Token IG DÍA 29+ (86e0p34k6+86e0q1tg8), OmegaDog DÍA 30+ (86e0gcgpt), script errors VENCIDA 8d (86e0t9yab), 0 ads DÍA 13+ (86e0qxn1b). S16 DÍA 3/7 con 0/7. Brief NO posteado ClickUp (MCP no disponible). A2 ya posteó alerta comment 90170201488703.
- 2026-04-14 09:00 CST — Brief compilado. ClickUp MCP disponible. Clarity DOWN (429 daily limit — ambas queries 24h + 3d fallaron). Sin datos frescos de tráfico hoy. Último dato: Apr 12 — 22 ses. mobile RECORD, scroll 6.11%, bounce masivo. Blockers sin cambio (todos "to do" confirmados via get_task): Token IG DÍA 27+ (86e0p34k6+86e0q1tg8), OmegaDog DÍA 28+ (86e0gcgpt), script errors VENCIDA 5d (86e0t9yab), 0 ads DÍA 11+ (86e0qxn1b). S16 DÍA 2 con 0/7. Comment posteado: 90170201262733. No se crearon tareas urgentes nuevas (todas existen).
- 2026-04-12 09:00 CST — Brief compilado. ClickUp MCP no disponible (error recurrente). Clarity 24h: 22 ses. mobile reales (RECORD ↑↑ +214% vs 7 ayer). Scroll 6.11% (↓↓↓), 14s activo (↓↓) — bounce masivo. Script errors 4% mobile (↓ mejora vs 66.67% PC ayer). PC: 0 ses. reales. 3d URLs: DogRelax 100% script errors, /collections/all 100%. /cart 3 ses. (compra real). UTMs paid HC-VENTAS-MES1 confirmados múltiples productos. ALERTA: spike + bounce = ads posiblemente activos pero audiencia/landing no convierte. Blockers sin cambio: Token IG DÍA 25+ (86e0p34k6+86e0q1tg8), OmegaDog DÍA 26+ (86e0gcgpt), script errors VENCIDA 3d (86e0t9yab), 0 ads verificar DÍA 8+ (86e0qxn1b). S15 CIERRA HOY Abr 12 con 0/7 posts. S16 inicia mañana Lun Abr 13 sin prep. No se crearon tareas urgentes (todas existen).
- 2026-04-11 09:00 CST — Brief diario posteado ClickUp comment 90170200603379. Clarity: 7 ses. mobile (↑↑ +133%) + 3 PC reales. Mobile: scroll 20.89% (↓), 140s activo (↑↑), dead clicks 14.29% (↓), script errors 0 (mejora). PC: NUEVA ESPIGA script errors 4 eventos / 66.67% sesiones (ayer: 0 en PC) — inversión de patrón. UTMs paid HC-VENTAS-MES1 en Clarity 3d (ArtriDog/OmegaDog/DogRelax/GastroDog) → posible ads activos post token-fix Apr 8. /cart 3 sesiones (intención de compra). OmegaDog dead clicks 50%. Blockers: Token IG DÍA 24+ (86e0p34k6+86e0q1tg8), OmegaDog DÍA 25+ (86e0gcgpt), script errors VENCIDA 2d (86e0t9yab), 0 ads/verificar DÍA 8+ (86e0qxn1b). S15 DÍA 6/7 con 0/7 posts. No se crearon tareas urgentes nuevas.
- 2026-04-10 09:00 CST — Brief diario posteado ClickUp comment 90170200360634. Clarity: 3 ses. mobile + 2 PC reales (5 total, igual ayer). Mobile: scroll 36% (↑), 60s activo. Dead clicks REGRESAN (5 eventos, 33% ses.) — confirma que los 2 días limpios eran artefacto de tráfico bajo. Script error regresa en mobile (1, 33%). PC: 55% scroll, 7s activo (bots). 4 tareas OVERDUE: 86e0p34k6 (9d), 86e0p5ake (8d), 86e0n2g98 (4d), 86e0t9yab (1d). S15 deadline HOY 0/7 posts. No se crearon tareas urgentes nuevas (todas existen).
- 2026-04-09 09:00 CST — Brief diario posteado ClickUp comment 90170200007060. Clarity: 5 ses. mobile (+400% vs ayer 1), 0 PC reales (17 bots). Mobile: scroll 24%, 82s activo. Script errors: 0 en 24h (2do día). NUEVO en 3d: /collections/all 100% script error (página no estaba antes). Homepage QuickBack 20% (CRO). ArtriDog scroll 8% (crítico). DogRelax 115s activo (top). Token Meta DÍA 20+ (86e0p34k6 + 86e0q1tg8). 0 ads activos. S15 DÍA 4 en cero. OmegaDog DÍA 23+. task 86e0t9yab VENCIDA HOY (DÍA 10). No se crearon tareas urgentes nuevas (todas existen).
- 2026-04-08 09:00 CST — Brief diario posteado ClickUp comment 90170199633656. Clarity: 1 ses. mobile (-91% vs ayer), 3 PC reales (8 bots). Mobile: scroll 83% (RECORD), 62s activo. Script errors: 0 en 24h (primera vez — posible fix o tráfico bajo, pendiente confirmar). Top URLs (3d): Homepage 9 ses., /afiliados 4 ses. Token Meta DÍA 18+ (86e0p34k6 + 86e0q1tg8 + 86e0r1fgr). 0 ads activos. S15 DÍA 2 en cero. OmegaDog DÍA 22+. No se crearon tareas urgentes nuevas (todas existen).
- 2026-04-07 09:00 CST — Brief diario posteado ClickUp comment 90170199244039. Clarity: 11 ses. mobile (+175% vs ayer), 0 PC reales. Mobile: scroll 47.62% (↑↑ gran mejora), 28s activo, script errors 9.09%. Top URL: Homepage 16 ses. (3d), /tienda 68% scroll. Script errors DÍA 8 (5 URLs sin fix). Token Meta DÍA 17 (86e0p34k6 + 86e0q1tg8 + 86e0r1fgr). 0 ads activos. S15 inicia HOY. OmegaDog DÍA 21. NUEVA tarea urgente creada: 86e0t9yab (script errors 8d — fix PDPs).
- 2026-04-06 09:00 CST — Brief diario posteado ClickUp comment 90170198848579. Clarity: 4 ses. reales (2 mobile + 2 PC), -60% vs ayer. Mobile: scroll 27%, 200s activo, script errors 50%. PC: scroll 6.75%, 32s activo, script errors 100%. Script errors DÍA 7 (5 URLs: ArtriDog 100%, GastroDog 100%, DogRelax 50%, OmegaDog 50%, Homepage 6.7%). Token Meta DÍA 15+ (86e0p34k6 + 86e0q1tg8 + 86e0r1fgr, todos "to do"). 0 ads activos. HC-005/006/007 saltados. S15 empieza HOY Abr 7 con 0% producido. OmegaDog DÍA 19 sin producción. No se crearon tareas urgentes nuevas (ya existen todas).
- 2026-04-05 09:00 CST — Brief diario posteado ClickUp comment 90170198633038. Clarity: 10 ses. PC (+100% vs ayer), 0 mobile. Scroll 15.18% (mejora). Script errors DÍA 6 (OmegaDog NUEVO 33%). Token Meta DÍA 14+. 0 ads activos en Meta (task 86e0qxn1b — NUEVO CRÍTICO). HC-006 deadline HOY Dom Abr 5 sin imágenes confirmadas. S15 empieza mañana Lun Abr 6 con 0% imágenes listas. No se crearon tareas urgentes nuevas (ya existen 86e0q1tg8 + 86e0p34k6 + 86e0qxn1b + 86e0r1fgr).
- 2026-04-04 09:00 CST — Brief diario posteado ClickUp comment 90170198611230. Clarity: 5 ses. PC (24h), 0 mobile. Script errors DÍA 5 sin fix (ArtriDog 100%, GastroDog 100%, DogRelax 50%, Homepage 7%). HC-006 CRITICO <24h (post Dom Abr 5, 0%). Token Meta DÍA 13 sin resolver. OmegaDog ~16d sin producción. No se crearon tareas urgentes nuevas (ya existen 86e0q1tg8 + 86e0p34k6).
- 2026-04-03 09:00 CST — Brief diario posteado ClickUp comment 90170198463311. Clarity: 2 ses. totales (muy bajo, esperado organic-only). Script errors día 4 sin fix (4 URLs). HC-005 deadline HOY sin imágenes. Token Meta día 10 sin resolver. No se crearon tareas urgentes nuevas (ya existen 86e0q1tg8 + 86e0p34k6).
- 2026-04-02 09:00 CST — Brief diario posteado ClickUp comment 90170198145820. Tarea urgente creada: 86e0q1tg8 (Token Meta 9 días sin resolver). HC-004 ventana perdida confirmada. HC-005 deadline mañana sin imágenes.

## Ultimo Check Pipeline Watcher (A2)
- 2026-04-16 21:00 CST — Health: ROJO (20%) — Sin cambios vs 19:00. ClickUp MCP disponible. 5 blockers verificados: todos "to do", date_updated sin cambio en los 5 (86e0p34k6: 1775024771228, 86e0q1tg8: 1775147515077, 86e0gcgpt: 1774367021374, 86e0t9yab: 1775577735207, 86e0qxn1b: 1775342499304). Token IG DÍA 31 (86e0p34k6+86e0q1tg8), OmegaDog DÍA 31 (86e0gcgpt), script errors VENCIDA 9d (86e0t9yab), 0 ads DÍA 14 (86e0qxn1b). S16 DÍA 4/7 con 0/7. No se posteó alerta. Alerta vigente: comment 90170202053421.
- 2026-04-16 19:00 CST — Health: ROJO (20%) — Sin cambios vs 14:00. ClickUp MCP disponible. 5 blockers verificados: todos "to do", date_updated sin cambio en los 5. Token IG DÍA 31 (86e0p34k6+86e0q1tg8), OmegaDog DÍA 31 (86e0gcgpt), script errors VENCIDA 9d (86e0t9yab), 0 ads DÍA 14 (86e0qxn1b). S16 DÍA 4/7 con 0/7. No se posteó alerta. Alerta vigente: comment 90170202053421.
- 2026-04-16 14:00 CST — Health: ROJO (20%) — Primer A2 del día. ClickUp MCP disponible. 5 blockers verificados: todos "to do", date_updated sin cambio. NUEVO (A1 hoy): ad hc-artridog-mes1 / ad_id 6913720802034 detectado en UTMs 3d — fuera del pipeline conocido. ArtriDog paid landing 100% dead clicks (CRO crítico). Alerta posteada comment 90170202053421. Token IG DÍA 31 (86e0p34k6+86e0q1tg8), OmegaDog DÍA 31 (86e0gcgpt — HITO: 31 días = un mes completo sin producción), script errors VENCIDA 9d (86e0t9yab), 0 ads DÍA 14 (86e0qxn1b). S16 DÍA 4/7 con 0/7.
- 2026-04-15 19:00 CST — Health: ROJO (20%) — Sin cambios vs 14:00. ClickUp MCP disponible (4 de 5 blockers verificados — 86e0p34k6 error conector, asumido "to do"). date_updated sin cambio en todos los verificados. Token IG DÍA 29 (86e0p34k6+86e0q1tg8), OmegaDog DÍA 30 (86e0gcgpt), script errors VENCIDA 8d (86e0t9yab — due Apr 9 vencida), 0 ads DÍA 13 (86e0qxn1b). S16 DÍA 3/7 con 0/7. No se posteó alerta. Alerta vigente: comment 90170201488703.
- 2026-04-15 14:00 CST — Health: ROJO (20%) — Sin cambios vs 09:27. ClickUp MCP disponible. Verificado: todos blockers "to do", date_updated sin cambio en los 5. Token IG DÍA 29 (86e0p34k6+86e0q1tg8), OmegaDog DÍA 30 (86e0gcgpt), script errors VENCIDA 7d (86e0t9yab), 0 ads DÍA 13 (86e0qxn1b). S16 DÍA 3/7 con 0/7. No se posteó alerta. Alerta vigente: comment 90170201488703.
- 2026-04-15 09:27 CST — Health: ROJO (20%) — Sin cambios vs 09:00. ClickUp MCP no disponible. No se posteó alerta. Alerta vigente: comment 90170201488703. Blockers sin cambio: Token IG DÍA 29 (86e0p34k6+86e0q1tg8), OmegaDog DÍA 30 (86e0gcgpt), script errors VENCIDA 7d (86e0t9yab), 0 ads DÍA 13 (86e0qxn1b). S16 DÍA 3/7 con 0/7.
- 2026-04-15 09:00 CST — Health: ROJO (20%) — Nuevo día. Alerta posteada comment 90170201488703. ClickUp verificado: todos blockers "to do" sin cambios. HITO: OmegaDog llega a DÍA 30 (un mes sin producción). Blockers: 86e0p34k6+86e0q1tg8 (Token IG DÍA 29, "to do"), 86e0gcgpt (OmegaDog DÍA 30, "to do"), 86e0t9yab (script errors VENCIDA 7d, "to do"), 86e0qxn1b (0 ads DÍA 13, "to do"). S16 DÍA 3/7 con 0/7.
- 2026-04-14 19:00 CST — Health: ROJO (20%) — Sin cambios vs 14:00. No se posteó alerta. ClickUp verificado: todos blockers "to do" sin updates. Blockers: 86e0p34k6+86e0q1tg8 (Token IG DÍA 28+, "to do"), 86e0gcgpt (OmegaDog DÍA 29+, "to do"), 86e0t9yab (script errors VENCIDA 6d, "to do"), 86e0qxn1b (0 ads DÍA 12+, "to do"). S16 DÍA 2 con 0/7. Alerta vigente: comment 90170201133390.
- 2026-04-14 14:00 CST — Health: ROJO (20%) — Sin cambios vs 09:00. No se posteó alerta. ClickUp verificado: todos blockers "to do" sin updates. Blockers: 86e0p34k6+86e0q1tg8 (Token IG DÍA 28+, "to do"), 86e0gcgpt (OmegaDog DÍA 29+, "to do"), 86e0t9yab (script errors VENCIDA 6d, "to do"), 86e0qxn1b (0 ads DÍA 12+, "to do"). S16 DÍA 2 con 0/7. Alerta vigente: comment 90170201133390.
- 2026-04-14 09:00 CST — Health: ROJO (20%) — S15 CERRÓ Abr 12 con 0/7 posts (DEFINITIVO). S16 inició Abr 13 — DÍA 2 con 0/7 sin prep. ClickUp MCP disponible (recuperado después de 2 días ausente Abr 12-13). Alerta posteada comment 90170201133390. Verificado en ClickUp: todos los blockers siguen "to do" sin actualizaciones. Blockers: 86e0p34k6+86e0q1tg8 (Token IG DÍA 27+, "to do" sin cambio), 86e0gcgpt (OmegaDog DÍA 28+, "to do" sin cambio), 86e0t9yab (script errors VENCIDA 5d, "to do" sin cambio), 86e0qxn1b (0 ads DÍA 11+, "to do" sin cambio).
- 2026-04-12 09:00 CST — Health: ROJO (20%) — S15 CIERRA HOY Abr 12 con 0/7 posts (DEFINITIVO — semana completamente fallida). S16 INICIA MAÑANA Lun Abr 13 con 0 prep. ClickUp MCP no disponible (4to día consecutivo — no se pudo postear alerta). Blockers: 86e0p34k6+86e0q1tg8 (Token IG DÍA 25+), 86e0gcgpt (OmegaDog DÍA 26+), 86e0t9yab (script errors VENCIDA 3d), 86e0qxn1b (0 ads DÍA 9+). NUEVO A1: spike tráfico +214% mobile con bounce masivo (6.11% scroll, 14s activo) — posibles ads activos sin conversión.
- 2026-04-11 19:00 CST — Health: ROJO (20%) — Sin cambios vs 14:00. No se posteó alerta. ClickUp MCP no disponible esta sesión. Todos blockers "to do": 86e0p34k6+86e0q1tg8 (Token IG DÍA 24+), 86e0gcgpt (OmegaDog DÍA 25+), 86e0t9yab (script errors VENCIDA 2d), 86e0qxn1b (0 ads DÍA 8+). S15 CIERRA MAÑANA Abr 12 con 0/7 — semana completamente fallida. S16 inicia Lun Abr 13 sin prep.
- 2026-04-11 14:00 CST — Health: ROJO (20%) — Sin cambios vs 09:00. No se posteó alerta. Todos blockers "to do" sin actualización: 86e0p34k6+86e0q1tg8 (Token IG DÍA 24+), 86e0gcgpt (OmegaDog DÍA 25+), 86e0t9yab (script errors VENCIDA 2d), 86e0qxn1b (0 ads DÍA 8+). S15 DÍA 6/7 con 0/7 posts — CIERRA MAÑANA Abr 12. S16 inicia Lun Abr 13 sin prep.
- 2026-04-11 09:00 CST — Health: ROJO (20%) — Alerta posteada ClickUp comment 90170200603357. Sin cambios de status en ClickUp vs ayer. Todos blockers "to do": 86e0p34k6+86e0q1tg8 (Token IG DÍA 24+), 86e0gcgpt (OmegaDog DÍA 25+), 86e0t9yab (script errors VENCIDA 2d), 86e0qxn1b (0 ads DÍA 8+). S15 DÍA 6/7 con 0/7 posts — CIERRA MAÑANA Abr 12. S16 inicia Lun Abr 13 sin prep.
- 2026-04-10 19:00 CST — Health: ROJO (20%) — Sin cambios vs 14:00. No se posteó alerta. Todos blockers "to do" sin actualización: 86e0p34k6+86e0q1tg8 (Token IG DÍA 23+), 86e0gcgpt (OmegaDog DÍA 24+), 86e0t9yab (script errors VENCIDA 1d), 86e0qxn1b (0 ads DÍA 7+). S15 DÍA 5/7 con 0/7 — recuperación imposible (2 días restantes).
- 2026-04-10 14:00 CST — Health: ROJO (20%) — Sin cambios vs 09:00. No se posteó alerta. Todos blockers "to do" sin actualización: 86e0p34k6+86e0q1tg8 (Token IG DÍA 23+), 86e0gcgpt (OmegaDog DÍA 24+), 86e0t9yab (script errors VENCIDA 1d), 86e0qxn1b (0 ads DÍA 7+). S15 DÍA 5/7 con 0/7 posts.
- 2026-04-10 09:00 CST — Health: ROJO (20%) — Alerta posteada ClickUp comment 90170200369107. NUEVO URGENTE: 86e0qxn1b (0 ads activos) cruza umbral 7 días hoy. 86e0p34k6+86e0q1tg8 (Token IG DÍA 23+ "to do"), 86e0gcgpt (OmegaDog DÍA 24+ "to do", último update Mar 27), 86e0t9yab (script errors VENCIDA 1d — dead clicks regresan en mobile confirmado A1 hoy). S15 DÍA 5/7 con 0/7 posts — 2 días para cerrar semana, recuperación imposible.
- 2026-04-09 19:00 CST — Health: ROJO (25%) — Sin cambios vs 14:00. No se posteó alerta. Verificado en ClickUp: todos los blockers confirmados "to do" sin actualización. 86e0p34k6+86e0q1tg8 (Token IG DÍA 22+), 86e0gcgpt (OmegaDog DÍA 23+), 86e0t9yab (script errors VENCIDA — 0 acciones), 86e0qxn1b (0 ads DÍA 6+). S15 DÍA 4 con 0/7 posts.
- 2026-04-09 14:00 CST — Health: ROJO (25%) — Sin cambios vs 09:00. No se posteó alerta. Todos blockers siguen "to do": 86e0p34k6+86e0q1tg8 (Token IG DÍA 21+), 86e0gcgpt (OmegaDog DÍA 23+), 86e0t9yab (script errors VENCIDA — sin resolver), 86e0qxn1b (0 ads sin verificar). S15 DÍA 4 con 0/7 posts.
- 2026-04-09 09:00 CST — Health: ROJO (25%) — Alerta posteada ClickUp comment 90170200015468. Sin cambios de status en ClickUp vs ayer. 86e0t9yab VENCIDA OFICIALMENTE HOY (deadline Apr 9). NUEVA URL script error: /collections/all 100% (expansión). Token IG DÍA 21+ (86e0p34k6+86e0q1tg8 "to do"). OmegaDog DÍA 23+ (86e0gcgpt "to do"). 0 ads sin verificar DÍA 6+ (86e0qxn1b "to do"). S15 DÍA 4 con 0/7 posts.
- 2026-04-08 19:00 CST — Health: ROJO (25%) — Sin cambios vs 14:00. No se posteó alerta. Todos blockers siguen "to do": 86e0p34k6+86e0q1tg8 (Token IG DÍA 20+), 86e0gcgpt (OmegaDog DÍA 22+), 86e0t9yab (script errors DÍA 10+ — VENCE MAÑANA Apr 9), 86e0qxn1b (0 ads sin verificar post-token). S15 DÍA 3 con 0/7 posts.
- 2026-04-08 14:00 CST — Health: ROJO (25%) — Alerta posteada ClickUp comment 90170199782091. CAMBIO: 86e0r1fgr marcado COMPLETE (Token Meta GR+HC descifrado — resuelto). Blockers activos: 86e0p34k6+86e0q1tg8 (Token IG permissions DÍA 19+), 86e0gcgpt (OmegaDog DÍA 22+), 86e0t9yab (script errors DÍA 10+ VENCE HOY Apr 9), 86e0qxn1b (0 ads DÍA 4+ — verificar con token resuelto). S15 DÍA 3 con 0/7 posts.
- 2026-04-08 09:00 CST — Health: ROJO (20%) — Alerta posteada ClickUp comment 90170199643862. Sin cambios vs ayer 19:00. Todos blockers "to do": 86e0p34k6, 86e0q1tg8 (Token Meta DÍA 19+), 86e0r1fgr (Token expirado HC+GR DÍA 3+), 86e0qxn1b (0 ads DÍA 4+), 86e0gcgpt (OmegaDog DÍA 22+), 86e0t9yab (script errors DÍA 9+ — VENCE MAÑANA Apr 9). S15 DÍA 2 con 0/7 posts. Primera vez que un blocker toca su deadline (86e0t9yab).
- 2026-04-07 19:00 CST — Health: ROJO (20%) — Sin cambios vs 14:00. No se posteó alerta. Todos blockers "to do": 86e0p34k6, 86e0q1tg8, 86e0r1fgr (Token Meta DÍA 17+), 86e0qxn1b (0 ads), 86e0t9yab (script errors DÍA 8+). 86e0gcgpt → error API (asumido sin cambio). S15 Abr 7-13 con 0% producido. Última alerta: 09:00 comment 90170199258549.
- 2026-04-07 09:00 CST — Health: ROJO (20%) — Alerta posteada ClickUp comment 90170199258549. S15 INICIA HOY (Abr 7-13) con 0% producido (HC-008 a HC-014). Token Meta DÍA 17 (86e0p34k6 + 86e0q1tg8 + 86e0r1fgr, todos "to do", confirmados en ClickUp). 0 ads activos (86e0qxn1b). OmegaDog DÍA 21+ sin producción (86e0gcgpt "to do"). Script errors DÍA 8+ (86e0t9yab nueva, "to do"). Sin cambios de status en ningún blocker.
- 2026-04-06 19:00 CST — Health: ROJO (20%) — Sin cambios vs 14:00. No se posteó alerta. Todos blockers "to do": 86e0p34k6, 86e0q1tg8, 86e0r1fgr (error API al consultar — asumido "to do", Token Meta DÍA 16+), 86e0qxn1b (0 ads), 86e0gcgpt (OmegaDog DÍA 20+), 86e0n2ga6 (S15 Abr 7-13 — start_date MAÑANA, 0% producido). Alerta ya posteada en 09:00. Score mantenido 20% ROJO.
- 2026-04-06 14:00 CST — Health: ROJO (20%) — Sin cambios vs 09:00. No se posteó alerta. Todos blockers siguen "to do": 86e0p34k6, 86e0q1tg8, 86e0r1fgr (Token Meta DÍA 16+), 86e0qxn1b (0 ads), 86e0gcgpt (OmegaDog DÍA 20+), 86e0n2ga6 (S15 Abr 7-13, 0% producido). Score mantenido 20% ROJO.
- 2026-04-06 09:00 CST — Health: ROJO (20%) — Alerta posteada ClickUp comment 90170198863766. S15 INICIO HOY (Abr 6-12) con 0% producido (HC-008 a HC-014). Token Meta DÍA 15+ (86e0p34k6 + 86e0q1tg8 + 86e0r1fgr, todos "to do"). 0 ads activos (86e0qxn1b). OmegaDog DÍA 19+ sin producción (86e0gcgpt "to do"). 6 ads en cola bloqueados. Script errors DÍA 7+ (5 URLs). Prior: 2026-04-05 19:00 → Sin cambios, no posteó.
- 2026-04-05 19:00 CST — Health: ROJO (25%) — Sin cambios vs 14:00. No se posteó alerta. Todos blockers siguen "to do". S15 empieza MAÑANA Abr 6 (T-12h) con 0% producido. Token Meta DÍA 14+ sin resolver.
- 2026-04-05 14:00 CST — Health: ROJO (25%) — Alerta posteada ClickUp comment 90170198635574. NUEVO: 86e0r1fgr Token Meta "could not be decrypted" (HC + GR). 0 ads activos en Meta confirmado (86e0qxn1b "to do"). HC-005 SALTADO, HC-006 SALTADO (deadline HOY), HC-007 SALTADO (deadline HOY). S15 empieza MAÑANA Abr 6 con 0% imágenes (HC-008/009B/010 sin producir). OmegaDog DÍA 16 sin producción. Script errors DÍA 6 (5 URLs, OmegaDog NUEVO 33%). Token Meta DÍA 14+.
- 2026-04-04 14:00 CST — Health: ROJO (31%) — Alerta posteada ClickUp comment 90170198617407. HC-006 + HC-007 ambos deadline Dom Abr 5 (MAÑANA <20h, 0% producidos — confirmado 86e0n4qnu). Token Meta DÍA 13 (86e0p34k6 + 86e0q1tg8 "to do"). OmegaDog DÍA 14+ sin producción (86e0gcgpt "to do" desde Mar 21). S15 empieza Lun Abr 6 con 0% imágenes. Script errors DÍA 5 sin fix. Sin cambios de status en ClickUp vs 9am.
- 2026-04-04 09:00 CST — Health: ROJO (30%) — Alerta posteada ClickUp comment 90170197616615
- 2026-04-01 14:00 CST — Health: ROJO (33%) — Alerta posteada ClickUp comment 90170197743081. Nuevos flags: HC-004 ventana probablemente perdida (10am ya pasó sin confirmar activación Make.com), HC-005 <2 días para deadline.
- 2026-04-02 09:00 CST — Health: ROJO (31%) — Alerta posteada ClickUp comment 90170198145702. Confirmado en ClickUp: HC-004 task 86e0n4qka sigue "in progress" (debía publicarse Mar 31, 2 días vencida). Token Meta (86e0p34k6) sigue "to do" — 9 días. OmegaDog ads 9 días sin producción. HC-005 deadline MAÑANA sin imágenes.
- 2026-04-02 14:00 CST — Health: ROJO (30%) — Alerta posteada ClickUp comment 90170198286909. CRITICO: HC-005 deadline mañana (Abr 3), 0% producido, 86e0n4qnu "to do". HC-004 overdue 2+ días. Token Meta (86e0q1tg8) 10 días sin resolver. OmegaDog (86e0gcgpt) 10 días sin producción.
- 2026-04-02 19:00 CST — Health: ROJO (37%) — Alerta posteada ClickUp comment 90170198337230. Sin cambios vs 14:00: HC-005 deadline mañana ~15h restantes 0% producido, HC-004 overdue 2+d, Token Meta 10d, OmegaDog 13d sin producción. Script errors website empeorando (4 URLs afectadas).
- 2026-04-03 09:00 CST — Health: ROJO (33%) — Alerta posteada ClickUp comment 90170198463206. HC-005 deadline HOY 0% producido (post va a saltar). HC-004 overdue 3d. Token Meta 11d. OmegaDog 10d sin update. HC-006 nuevo riesgo (Abr 5, 2d restantes sin imágenes).
- 2026-04-03 14:00 CST — Health: AMARILLO (44%) — Alerta posteada ClickUp comment 90170198518620. POSITIVO: HC-004 ahora COMPLETE (se publicó). HC-005 deadline HOY confirmado SALTADO (sigue "to do" ~2pm). Token Meta día 11. OmegaDog ~15d sin producción. HC-006 riesgo alto (Abr 5, 2d, 0%).
- 2026-04-03 19:00 CST — Health: ROJO (38%) — Alerta posteada ClickUp comment 90170198551378. HC-006 escalado a CRITICO (<36h, 0% producido, post Dom Abr 5). HC-005 confirmado SALTADO. Token Meta día 12 sin resolver (to do). OmegaDog ~15d sin actividad. Sin cambios de status vs 14:00 — degradación por ventana HC-006 cruzada.
- 2026-04-04 09:00 CST — Health: ROJO (33%) — Alerta posteada ClickUp comment 90170198611234. HC-006 CRITICO <24h (post Dom Abr 5, 0% producido). HC-005 confirmado SALTADO (2da ventana S14 perdida). Token Meta día 13 (ambas tareas "to do"). OmegaDog ~17d sin producción (86e0gcgpt "to do", último update Mar 26). Script errors día 5 sin fix (ArtriDog 100%, GastroDog 100%). HC-007 a HC-010 en riesgo (S15 empieza mañana Abr 6, 0% producido).
