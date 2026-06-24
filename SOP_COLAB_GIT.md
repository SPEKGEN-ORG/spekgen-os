# SOP de Colaboración SPEKGEN — Gibran + Pedro (Claude Code)

> Este archivo lo lee Claude Code automáticamente al trabajar CUALQUIER repo bajo `~/dev`.
> Vive igual en la máquina de Gibran y la de Pedro → los dos Claudes operan idéntico.
> Objetivo: que Gibran y Pedro trabajen LO MISMO sin pisarse, sin duplicar, sin borrar, con versión de todo.

## Reglas para Claude (obligatorias)

1. **El código vive aquí (`~/dev`), nunca en Google Drive.** Drive = solo assets, docs, media, data de clientes.

2. **Antes de tocar un repo: trae lo último.** Al inicio de toda sesión de trabajo en un repo, corre `git pull` (o `git fetch` + status) ANTES de editar. Si el usuario dice "tráeme lo último", haz pull.

3. **Cada cambio = branch + Pull Request. NUNCA push directo a `main`.**
   - Crea branch con el nombre del autor: `gibran/<tema>` o `pedro/<tema>`.
   - Commit con mensaje claro (qué + por qué).
   - Abre PR con `gh pr create`. El PR es el registro de "qué cambió y quién".
   - Cuando el usuario diga "súbelo" → branch + commit + push + PR, todo tú.

4. **Merge:**
   - Si el cambio es del propio carril del autor y es seguro → puedes mergear (`gh pr merge --squash`).
   - Si toca trabajo activo del otro o el core compartido → deja el PR abierto y avisa para revisión.
   - Cuando el usuario diga "mergéalo" / "junta las ramas" → mergea el PR.

5. **Conflictos: NUNCA descartes el trabajo de nadie.** Si `git merge` marca conflicto, resuélvelo conservando AMBOS cambios cuando sea posible; si chocan en la misma línea, muestra las dos versiones al usuario y pregunta. El trabajo de Gibran y el de Pedro siempre se preservan.

6. **Secretos jamás a Git.** `.env`, `.env.local`, `_ghl_locations.json`, tokens → ya están en `.gitignore`. Nunca los commitees. Si ves uno staged, quítalo y avisa.

7. **Lo que NO es código (Shopify Admin en vivo, imágenes sueltas en Drive) Git NO lo fusiona.** Ahí la regla es coordinarse (avisarse antes de editar lo mismo), no hay merge automático. Usen ClickUp para eso.

8. **Bots (F24, HC): fuente = repo `main`, nunca Drive ni la UI de Make.** El bot LIVE se deploya SOLO desde `main` (cron `f24_promos_sync.yml` 2x/día + on-edit). Editar en la UI de Make se PIERDE (el cron rebuildea desde el código). Probar en el scenario DEV aislado (`./deploy_f24_bot.sh dev`) antes de mergear; nunca deployar a prod ANTES de mergear a main (se revierte). Detalle obligatorio: `clients/f24/bot/docs/BOT_DEPLOY_SOP.md`.

9. **Hooks locales:** corre `git config core.hooksPath .githooks` una vez por clon (ver `SETUP.md`). Bloquea push directo a `main` — fuerza el flujo PR. No hay branch protection (repo privado plan free).

## Cómo lo pide el humano (no teclean git)
- "tráeme lo último" → pull
- "súbelo" → branch + commit + PR
- "mergéalo" / "junta las ramas" → merge del PR
- "qué cambió Pedro/Gibran" → lista PRs/commits recientes

## Repos (org `SPEKGEN-ORG`)
greenray-theme · healthychuchos-horizon · spekgen-content-hub · editor-pro-max · ghl-mcp · spekgen-os · spekgen-prospectos

> Referencia completa: `spekgen-os/SOP_COLAB_GIT.md` y, en Drive, `SPK - 00. COMMAND CENTER/02. DOCS OPERATIVOS/FLUJO_GITHUB_PEDRO.md`.
