# 👋 Pedro — Empieza aquí (onboarding del repo)

> Léelo tú y déjaselo leer a tu Claude. Objetivo: que tú y Gibran trabajen el mismo código
> (bots, scripts) sin pisarse, sin duplicar y sin borrarse cambios — todo versionado.

## ✅ Tu acceso ya está listo
Eres **colaborador activo** de la org **`SPEKGEN-ORG`** con permiso de escritura en `spekgen-os`.
NO necesitas que te reinviten.

## Paso 1 — Clona (URL correcta)
```bash
mkdir -p ~/dev && cd ~/dev
git clone https://github.com/SPEKGEN-ORG/spekgen-os.git
cd spekgen-os
```
Setup completo de tu máquina (deps, Drive, OS): **`SETUP.md`**.

## Paso 2 — Activa los hooks (una vez)
```bash
git config core.hooksPath .githooks
```
Bloquea push directo a `main` → te obliga a usar PRs (así nadie borra el trabajo del otro).

## Paso 3 — Flujo de trabajo (SIEMPRE)
**Un cambio = una rama + un PR. NUNCA edites `main` directo.**
```bash
git pull                          # trae lo último ANTES de editar
git checkout -b pedro/lo-que-sea
# ...editas...
git add -A && git commit -m "feat: ..."
git push -u origin pedro/lo-que-sea && gh pr create
```
Detalle: **`SOP_COLAB_GIT.md`** + **`CONTRIBUTING.md`**.

## Paso 4 — Si trabajas el BOT de WhatsApp
Léelo obligatorio: **`clients/f24/bot/docs/BOT_DEPLOY_SOP.md`**. Reglas de oro:
- Fuente = repo `main`. NUNCA Drive ni la UI de Make (el cron borra lo de Make UI).
- Prueba en el scenario DEV aislado (`./deploy_f24_bot.sh dev mi-tag`) antes de mergear.
- El bot LIVE se deploya solo desde `main` (GitHub Action 2x/día + on-edit). Mergeas → se va al bot.
- NUNCA deployes a prod antes de mergear (el cron te lo revierte).

## 🗣️ Cómo le hablas a tu Claude (no tecleas git tú)
- "tráeme lo último" → pull · "súbelo" → rama+commit+PR · "mergéalo" → merge · "qué cambió Gibran" → PRs recientes.

## 🔑 Credenciales
- Flujo normal (branch/PR): **no necesitas ninguna API key** (los secretos viven como GitHub Secrets, los usa el Action).
- Si corres scripts a mano: pide a Gibran los `.env` de `F24- FERRE24/` y `SPK - SPEKGEN AGENCY/` por un **canal seguro** (NO git, NO chat público — están en `.gitignore`).

## 🚫 Reglas que evitan desastres
1. Código → `~/dev`, NUNCA en Google Drive.  2. Nunca el bot en Make UI ni Drive.  3. Siempre PR.
4. Secretos jamás a git.  5. Antes de una sesión grande del bot, avisa en ClickUp para no chocar.
