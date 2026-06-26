# spekgen-os — Instrucciones para Claude Code

> Este repo es compartido (Gibran + Pedro). Estas reglas son OBLIGATORIAS y existen para que
> los dos trabajen el mismo código sin pisarse, duplicar ni borrar. Léelas antes de editar.

## Reglas duras (anti-colisión)

1. **`git pull` antes de editar.** Trae lo último (del otro y del cron) al inicio de toda sesión.
2. **Un cambio = una rama + un PR. NUNCA push directo a `main`.** Rama `gibran/<tema>` o `pedro/<tema>`.
   Un hook (`core.hooksPath .githooks`) bloquea el push a main. `gh pr create` → `gh pr merge`.
3. **Conflictos: preserva AMBOS trabajos.** Nunca descartes lo del otro; si chocan en la misma línea, muestra las dos versiones y pregunta.
4. **Secretos jamás a git** (`.env`, tokens). Están en `.gitignore`. Si ves uno staged, quítalo y avisa.
5. **Código vivo → aquí (`~/dev`), NUNCA en Google Drive.** Drive = solo assets/docs/data.

## Bot de WhatsApp (F24 / HC) — reglas críticas

- **Fuente de verdad = este repo, rama `main`.** NUNCA edites el bot en la UI de Make (el deploy lo
  borra al rebuildar) ni en Drive (no se deploya).
- **El bot se deploya por un PIPELINE automático, NO a mano.** Mergeas un cambio del bot a `main` →
  el Action `f24_bot_deploy.yml` corre solo: **build → deploy DEV → smoke DEV (compuerta) → deploy
  PROD → smoke PROD → si rompe, auto-rollback al último bueno + email**. No corras `deploy prod` a mano.
- **La compuerta DEV te protege:** si tu cambio rompe el bot, falla en DEV (scenario aislado 5381174)
  y PROD (5258612, el live) NUNCA se toca. Te llega un email y el bot sigue sano.
- **Un monitor** (`f24_bot_healthcheck.yml`) prueba el bot live cada 20 min y alerta por email
  (Gibran + Pedro) si se cae — aunque la caída no venga de un deploy.
- **NO hace falta "lock" ni avisar al otro:** git serializa los merges; dos PRs no chocan en el live.
  Trabajen en paralelo con confianza (cada quien su rama + PR).
- **Deploy manual = SOLO emergencia** (`CONFIRM_PROD=yes ./deploy_f24_bot.sh prod <tag>`), p.ej. si el
  pipeline está caído. En operación normal nunca se usa.
- En Make, el nombre del scenario trae el commit git (`...PROD [abc1234]`) → así ves qué está live.
- SOP completo del bot: **`clients/f24/bot/docs/BOT_DEPLOY_SOP.md`**.

## Cómo lo pide el humano (Claude opera el git)

- "tráeme lo último" → `git pull` · "súbelo" → rama+commit+push+PR · "mergéalo" → merge del PR ·
  "qué cambió Gibran/Pedro" → lista PRs/commits recientes.

## Docs de referencia (en este repo)

- `SOP_COLAB_GIT.md` — colaboración git (detalle).  · `CONTRIBUTING.md` — convenciones.
- `SETUP.md` — instalación por OS.  · `START_HERE_PEDRO.md` — onboarding.
- `clients/f24/bot/docs/` — SOP de deploy del bot + reconciliación.

## Credenciales

Para el flujo normal (branch/PR) no se necesitan API keys (viven como GitHub Secrets, las usa el
Action). Para correr scripts a mano: `.env` de `F24- FERRE24/` y `SPK - SPEKGEN AGENCY/` (en Drive),
por canal seguro — NUNCA a git.
