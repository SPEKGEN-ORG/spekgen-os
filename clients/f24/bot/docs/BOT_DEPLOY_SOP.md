# SOP — Cómo trabajar el bot F24 sin pisarse (Gibran + Pedro)

> Lee esto ANTES de tocar el bot. Resuelve el problema raíz: dos personas editando →
> cambios duplicados, borrados o "se suponía que ya estaba hecho".

## La regla de oro: UNA fuente, UN camino de deploy

- **Fuente de verdad ÚNICA:** este repo, carpeta `clients/f24/bot/`, rama `main`.
  NO Drive. NO la UI de Make. NO copias sueltas.
- **El bot LIVE se deploya SOLO desde `main`** vía el pipeline `f24_bot_deploy.yml` (al mergear) y el
  cron `f24_promos_sync.yml` (datos de promos). Lo que NO está en `main` NO está en producción.
- **Nadie deploya a prod a mano.** El pipeline lo hace, con compuerta DEV + smoke + auto-rollback.

## Las 3 cosas que causaban colisiones (y ya no deben pasar)

1. **Editar en Drive** (`bot_multimodal/`) — era un fork huérfano que NO se deploya. ELIMINADO
   2026-06-24. Si encuentras una copia del bot en Drive, está mal: el bot vive en el repo.
2. **Editar en la UI de Make** — el cron REBUILDA el scenario desde el código 2x/día y BORRA
   cualquier cambio hecho a mano en Make. Nunca edites el scenario en la UI; edita el código.
3. **`deploy_f24_bot.sh dev` apuntaba al LIVE** (footgun) — CORREGIDO 2026-06-24:
   `prod` = 5258612 (LIVE), `dev` = 5381174 (aislado). Ahora "dev" es seguro.

## El cron (`f24_promos_sync.yml`)

- Corre **2x/día (16:00 y 22:00 UTC)** + **on-edit** (cuando cambia la hoja de promos, vía Apps Script).
- En cada corrida: sync promos/inventario → rebuild knowledge → **build blueprint → deploy a PROD 5258612
  → smoke PROD → si rompe, auto-rollback + email** (desde `main`).
- O sea: **mergear a `main` = el bot se actualiza solo** (por `f24_bot_deploy.yml` al instante, y el cron
  refresca los datos de promos 2x/día).
- El nombre del scenario en Make queda estampado con el **commit git** (`... PROD [abc1234]`).
  Si ves `-dirty` o un SHA que no está en `main`, alguien deployó a mano fuera de git → revisar.

## Flujo para CUALQUIER cambio al bot (los dos, igual) — vía PIPELINE

Desde 2026-06-26 el bot tiene un pipeline CI/CD. **Tu único trabajo es mergear a `main`; el deploy,
las pruebas y el rollback son automáticos.** No deployas a prod a mano.

1. **`git pull`** en `main` antes de empezar (trae lo último de Pedro/Gibran/deploy).
2. **Branch:** `gibran/<tema>` o `pedro/<tema>`. (Nunca edites directo en `main`.)
3. Edita SOLO archivos fuente: `F24_BOT_SYSTEM_PROMPT.md`, `F24_BOT_CANNED_RESPONSES.md`,
   `build_f24_bot_blueprint.py`, knowledge builders. (El blueprint JSON se genera, no se edita.)
4. **(Opcional) Prueba local rápida del cerebro:** `python3 scenario_builders/test_f24_bot_brain.py`.
   No es obligatoria — la compuerta DEV del pipeline ya prueba el bot real antes de tocar prod.
5. **Sube:** `git push` + `gh pr create`. El PR es el registro de qué cambió y quién.
6. **Merge a `main`.** Eso es todo. El Action **`f24_bot_deploy.yml`** arranca solo y hace:
   `build → deploy DEV → smoke DEV (compuerta) → deploy PROD → smoke PROD`.
   - Si tu cambio **rompe el bot en DEV**, el pipeline se detiene ahí: **PROD nunca se toca** y te
     llega un email. El bot live sigue sano. Corriges y vuelves a mergear.
   - Si pasa DEV pero **rompe PROD**, el pipeline hace **auto-rollback** al último blueprint bueno y
     te avisa por email. El bot vuelve solo a la versión anterior.
   - Si todo pasa, guarda el blueprint como `LAST_GOOD` (el punto de rollback) y listo.
7. Mira el resultado en **Actions → "F24 Bot Deploy"**. Verde = tu cambio está live y verificado.

## Monitor de salud (corre solo)

- **`f24_bot_healthcheck.yml`** prueba el bot live cada **20 min** (smoke test real) y manda email a
  Gibran + Pedro si NO responde — aunque la caída no venga de un deploy (p.ej. Make o el puente GHL).
- Es **solo-alerta** (no hace rollback): un blip momentáneo no debe revertir un deploy que estaba bien.

## Anti-colisión — ya NO necesitas avisar ni "lock"

- **Git serializa los merges:** dos PRs no pueden tocar el live al mismo tiempo. El pipeline corre con
  `concurrency: f24-bot-deploy` → un deploy y el cron de promos jamás corren juntos (uno cancela al otro).
  Eso mata el thrash que tiró el bot el 24-jun. **Trabajen en paralelo con confianza.**
- **Todo cambio = PR** (lo exige la branch protection de `main`). El PR muestra si el otro tocó lo
  mismo (conflicto visible) en vez de borrarse en silencio.
- **Hook local** bloquea push directo a `main` (`git config core.hooksPath .githooks`, una vez).
- ~~Task ClickUp "🔒 Bot F24 en edición"~~ — **YA NO hace falta.** El pipeline hace la coordinación
  estructural; no hay que avisarle al otro antes de editar.

## Rollback

- **Automático:** si un deploy rompe PROD, el pipeline ejecuta `ci/rollback_prod.sh` solo. Diseño GitOps:
  el target es un **SHA de git** en `_BLUEPRINTS/LAST_GOOD_prod.sha` (el commit que pasó el último smoke,
  sin llaves en git). El rollback hace checkout de esa fuente, reconstruye y re-deploya, y verifica con
  otro smoke. `LAST_GOOD` lo fija el pipeline de deploy en cada merge verificado.
- **Manual de emergencia** (si el pipeline mismo está caído): `cd clients/f24/bot && ./ci/rollback_prod.sh`.
  O reproducir desde cualquier commit: `git checkout <commit-bueno> -- clients/f24/bot/` → mergear.

## Building blocks del pipeline (`clients/f24/bot/ci/`)

| Archivo | Qué hace |
|---|---|
| `smoke_test_bot.py <dev\|prod>` | Prueba VIVA: contacto efímero → mensaje al bot → verifica respuesta → borra contacto. exit 0/1. |
| `alert_email.py` | Email de alerta a `BOT_ALERT_RECIPIENTS` (var de repo = Gibran + Pedro) por Gmail SMTP. |
| `rollback_prod.sh` | Restaura PROD al commit `LAST_GOOD_prod.sha` (checkout → rebuild → deploy, reusa `deploy_f24_bot.sh`). |

> Destinatarios de alertas: variable de repo **`BOT_ALERT_RECIPIENTS`** (coma-separada). Fuente única
> para los 3 workflows. Cambiarla: `gh variable set BOT_ALERT_RECIPIENTS -b "a@x.com,b@y.com"`.

## Scenarios Make (referencia)

| | Scenario | Hook | Uso |
|---|---|---|---|
| **PROD (LIVE)** | 5258612 | 2394767 | Tráfico real de WhatsApp. Solo el cron o `deploy prod`. |
| **DEV (aislado)** | 5381174 | 2451202 | Pruebas. `deploy dev`. Sin tráfico real. |

Edge functions (Supabase `wjlwpfaogjpeqgyxxnwa`): la versión DEPLOYADA es la verdad; el código
fuente vive en `edge/`. Ver `RECONCILIATION_2026-06-24.md`.
