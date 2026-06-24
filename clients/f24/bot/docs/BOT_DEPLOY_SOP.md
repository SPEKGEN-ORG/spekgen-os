# SOP — Cómo trabajar el bot F24 sin pisarse (Gibran + Pedro)

> Lee esto ANTES de tocar el bot. Resuelve el problema raíz: dos personas editando →
> cambios duplicados, borrados o "se suponía que ya estaba hecho".

## La regla de oro: UNA fuente, UN camino de deploy

- **Fuente de verdad ÚNICA:** este repo, carpeta `clients/f24/bot/`, rama `main`.
  NO Drive. NO la UI de Make. NO copias sueltas.
- **El bot LIVE se deploya SOLO desde `main`** (vía el cron `f24_promos_sync.yml`).
  Lo que NO está en `main` NO está en producción, aunque lo hayas editado en otro lado.

## Las 3 cosas que causaban colisiones (y ya no deben pasar)

1. **Editar en Drive** (`bot_multimodal/`) — era un fork huérfano que NO se deploya. ELIMINADO
   2026-06-24. Si encuentras una copia del bot en Drive, está mal: el bot vive en el repo.
2. **Editar en la UI de Make** — el cron REBUILDA el scenario desde el código 2x/día y BORRA
   cualquier cambio hecho a mano en Make. Nunca edites el scenario en la UI; edita el código.
3. **`deploy_f24_bot.sh dev` apuntaba al LIVE** (footgun) — CORREGIDO 2026-06-24:
   `prod` = 5258612 (LIVE), `dev` = 5381174 (aislado). Ahora "dev" es seguro.

## El cron (`f24_promos_sync.yml`)

- Corre **2x/día (16:00 y 22:00 UTC)** + **on-edit** (cuando cambia la hoja de promos, vía Apps Script).
- En cada corrida: sync promos/inventario → rebuild knowledge → **build blueprint → deploy a PROD 5258612** (desde `main`).
- O sea: **mergear a `main` = el bot se actualiza solo** en la siguiente corrida del cron.
- El nombre del scenario en Make queda estampado con el **commit git** (`... PROD [abc1234]`).
  Si ves `-dirty` o un SHA que no está en `main`, alguien deployó a mano fuera de git → revisar.

## Flujo para CUALQUIER cambio al bot (los dos, igual)

1. **`git pull`** en `main` antes de empezar (trae lo último de Pedro/Gibran/cron).
2. **Branch:** `gibran/<tema>` o `pedro/<tema>`. (Nunca edites directo en `main`.)
3. Edita SOLO archivos fuente: `F24_BOT_SYSTEM_PROMPT.md`, `F24_BOT_CANNED_RESPONSES.md`,
   `build_f24_bot_blueprint.py`, knowledge builders. (El blueprint JSON se genera, no se edita.)
4. **Prueba en DEV aislado** (no toca el live):
   ```
   python3 build_f24_bot_blueprint.py
   ./deploy_f24_bot.sh dev v-mi-prueba        # → scenario 5381174, hook 2451202
   ```
   Manda mensajes de prueba al hook de DEV o usa `test_f24_bot_brain.py`.
5. **Sube:** `git push` + `gh pr create`. El PR es el registro de qué cambió y quién.
6. **Merge a `main`** (tú o Pedro revisan el PR). **Recién DESPUÉS de mergear**, el cambio
   puede ir al live.
7. **Para que salga YA** (sin esperar al cron): `./deploy_f24_bot.sh prod v-tag` (te pide
   teclear `PROD`). **NUNCA deployes a prod ANTES de mergear a main** — el cron rebuildea
   desde main y te lo revertiría.

## Anti-colisión (porque NO hay branch protection — repo privado en plan free)

- **Todo cambio = PR.** Aunque puedas pushear directo a `main`, NO lo hagas. El PR detecta si
  el otro tocó lo mismo (conflicto visible) en vez de borrarse en silencio.
- **Un hook local bloquea push directo a `main`** (`.githooks/pre-push`). Instálalo una vez:
  `git config core.hooksPath .githooks` (ver `SETUP.md`).
- **Avisa antes de una sesión grande de bot.** Crea/usa la task ClickUp **"🔒 Bot F24 en edición"**
  (Delivery → Ferre24) y asígnate. Si ya está tomada, coordínate. Es el "lock" humano.
- **Conflictos:** se preservan AMBOS trabajos (ver `SOP_COLAB_GIT.md`). Nunca descartar lo del otro.

## Rollback de emergencia

- El bot es reproducible desde cualquier commit: `git checkout <commit-bueno> -- clients/f24/bot/`
  → `build` → `./deploy_f24_bot.sh prod rollback`. O `git revert` del commit malo + merge a main.
- Backups de blueprint en `_BLUEPRINTS/` (locales/CI) como respaldo extra.

## Scenarios Make (referencia)

| | Scenario | Hook | Uso |
|---|---|---|---|
| **PROD (LIVE)** | 5258612 | 2394767 | Tráfico real de WhatsApp. Solo el cron o `deploy prod`. |
| **DEV (aislado)** | 5381174 | 2451202 | Pruebas. `deploy dev`. Sin tráfico real. |

Edge functions (Supabase `wjlwpfaogjpeqgyxxnwa`): la versión DEPLOYADA es la verdad; el código
fuente vive en `edge/`. Ver `RECONCILIATION_2026-06-24.md`.
