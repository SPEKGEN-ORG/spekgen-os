# SETUP — spekgen-os

Instrucciones de instalación para Mac, Windows y Linux. Sigue la sección de tu OS.

---

## 0. Pre-requisitos (todos los OS)

1. **Cuenta GitHub con acceso a `SPEKGEN-ORG/spekgen-os`** (Gibran ya te dio acceso como collaborator de la org).
2. **Google Drive Desktop** instalado y sincronizando la carpeta compartida `01. CLIENTS OFFICIAL` (Gibran te comparte como Editor; si es Shared Drive te lo dará distinto).
3. **Python 3.9+** instalado.
4. **Claude Code** instalado.

---

## 0.5 Después de clonar — activa los git hooks (TODOS los OS)

Una vez clonado el repo, activa los hooks versionados (bloquean push directo a `main` para
forzar el flujo branch + PR — no hay branch protection en el plan free de GitHub):

```bash
cd ~/dev/spekgen-os        # o donde lo clonaste
git config core.hooksPath .githooks
```

`gh pr create` / `gh pr merge` siguen funcionando normal. Para el bot, lee además
`clients/f24/bot/docs/BOT_DEPLOY_SOP.md`.

---

## 1. Mac (Gibran)

```bash
# Clonar repo
mkdir -p ~/dev && cd ~/dev
git clone https://github.com/SPEKGEN-ORG/spekgen-os.git
cd spekgen-os

# Verificar Drive sincronizado
ls "$HOME/Library/CloudStorage/GoogleDrive-"*/My\ Drive*/01.\ CLIENTS\ OFFICIAL/ | head -3

# Instalar Python deps (usa /usr/bin/python3 por compat con PIL legacy)
/usr/bin/python3 -m pip install --user openpyxl pypdf requests jinja2 pillow pymupdf playwright python-dotenv

# Verificar helper portable
/usr/bin/python3 tools/spekgen_paths.py

# Configurar .env local (NO en repo)
cp .env.example ~/.env.spekgen
# editar ~/.env.spekgen con los valores reales (pedirlos al admin)

# Symlink skills al directorio de Claude (hook automático)
bash scripts/sync-skills.sh

# Verificar
ls -la ~/.claude/skills/ | grep -v '^total\|^d.*\.$'
```

Las skills aparecen en Claude Code como `/factory-batch`, `/publish-prospect`, `/f24-product-research`, etc.

---

## 2. Windows (Pedro)

```powershell
# Abre PowerShell (NO cmd, no admin necesario)

# Clonar repo
mkdir C:\dev
cd C:\dev
git clone https://github.com/SPEKGEN-ORG/spekgen-os.git
cd spekgen-os

# Verificar Drive sincronizado (ajusta letra según tu Drive)
dir "G:\My Drive\01. CLIENTS OFFICIAL\" | Select-Object -First 5

# Instalar Python deps
python -m pip install --user openpyxl pypdf requests jinja2 pillow pymupdf playwright python-dotenv

# Verificar helper portable
python tools\spekgen_paths.py

# Configurar .env local
copy .env.example $HOME\.env.spekgen
# editar $HOME\.env.spekgen (notepad, VS Code, etc.) con valores reales

# Symlink skills al directorio de Claude (junction — NO requiere admin)
mkdir $HOME\.claude\skills -ErrorAction SilentlyContinue
# Por cada skill folder que tenga SKILL.md, crear junction:
Get-ChildItem -Directory skills\GLOBALES, skills\PERSONALIZADAS | Where-Object {
    Test-Path "$($_.FullName)\SKILL.md"
} | ForEach-Object {
    $target = "$HOME\.claude\skills\$($_.Name)"
    if (Test-Path $target) { Remove-Item $target -Recurse -Force }
    cmd /c mklink /J "$target" "$($_.FullName)"
}

# Verificar
dir $HOME\.claude\skills
```

**Notas Windows:**
- Python desde winget se registra como `python` y `py`, no como `python3`. En la mayoría de scripts SPEKGEN dice "`python3`" — interprétalo como `python` en tu máquina.
- Si `mklink /J` falla, alternativa: copiar la carpeta con `xcopy /E /I` (pero hay que re-copiar cuando se actualice — peor opción).
- Para correr el hook `sync-skills.sh` necesitas Git Bash o WSL. El bloque de PowerShell de arriba es el equivalente nativo.

---

## 3. Linux (futuros empleados)

```bash
mkdir -p ~/dev && cd ~/dev
git clone https://github.com/SPEKGEN-ORG/spekgen-os.git
cd spekgen-os

# Drive Desktop oficial no existe para Linux. Alternativas:
#   - rclone con Google Drive (línea de comandos, gratis)
#   - insync (paga, GUI)
#   - Montar Shared Drive vía rclone con cron
# Define la ruta absoluta y exporta SPEKGEN_ROOT:
export SPEKGEN_ROOT="/ruta/absoluta/a/01. CLIENTS OFFICIAL"
echo "export SPEKGEN_ROOT=\"$SPEKGEN_ROOT\"" >> ~/.bashrc

python3 -m pip install --user openpyxl pypdf requests jinja2 pillow pymupdf playwright python-dotenv
python3 tools/spekgen_paths.py

cp .env.example ~/.env.spekgen
# llenar valores

bash scripts/sync-skills.sh
```

---

## 4. Verificación end-to-end

Después de cualquiera de los 3 setups, valida que todo jale:

```bash
# 1. El helper resuelve el Drive root
python3 tools/spekgen_paths.py        # Mac/Linux
python tools\spekgen_paths.py         # Windows

# Debe imprimir el path a "01. CLIENTS OFFICIAL" + las 5 carpetas de cliente.

# 2. Un skill puede correr (ejemplo: f24-product-research consolidator)
python3 skills/PERSONALIZADAS/f24-product-research/scripts/consolidate_to_xlsx.py HP5.5N "Hidrolavadora a gasolina 5.5hp"

# Debe imprimir: "%completo=81.2%" o similar.
```

Si los 2 comandos jalan, estás listo. Abre Claude Code dentro de `01. CLIENTS OFFICIAL/` o de `~/dev/spekgen-os/` y empieza a trabajar.

---

## 5. Manejo de secretos (transitorio hasta vault)

Mientras NO tenemos 1Password / Bitwarden / Doppler configurados:

- **Cada miembro mantiene su `~/.env.spekgen` localmente.** NO en Drive. NO en repo.
- **Para transferir credenciales** entre miembros: Signal o WhatsApp con borrado de mensajes activado, NO email plano, NO chat Slack/Discord, NO commits temporales.
- **Cuando una credencial rote**: el admin notifica + comparte la nueva. Cada quien actualiza su `.env`.
- **Convención de carga**: scripts que necesiten secretos hacen `python-dotenv` cargando de `~/.env.spekgen` por default, o aceptan path explícito vía `--env-file`.

**Migrar a vault es prioridad mes 2.** Opciones evaluadas:
- **Bitwarden** — free para 2 usuarios, $4/mes para más. CLI `bw` + integración VS Code.
- **1Password** — $8/usuario/mes. CLI `op` + integración nativa con shells.
- **Doppler** — free tier 5 usuarios, ideal para CI/CD. CLI `doppler`.

---

## 6. Updates al repo

```bash
cd ~/dev/spekgen-os          # o C:\dev\spekgen-os
git pull origin main         # antes de empezar a trabajar
# ... haces cambios ...
git add .
git commit -m "feat(scope): mensaje claro"
git push origin main         # o crea PR si es cambio grande
```

**Workflow recomendado:**
- Cambios pequeños en una skill que ya conoces → commit directo a `main`.
- Skills nuevas, refactors grandes, cambios a `tools/` o `scripts/` → branch + PR para que el otro revise.
- Convención de commits en CONTRIBUTING.md.

---

## 7. Troubleshooting común

| Síntoma | Causa probable | Fix |
|---|---|---|
| `RuntimeError: No pude localizar '01. CLIENTS OFFICIAL'` | Drive no sincronizado o ruta no canónica | Set `SPEKGEN_ROOT` env var con ruta absoluta |
| Skills no aparecen en Claude Code | Symlink no se creó (Windows) o hook no corrió (Mac) | Re-correr `sync-skills.sh` o crear junctions manuales |
| `python3: command not found` (Windows) | Windows usa `python` o `py` | Reemplazar `python3` por `python` en comandos |
| `Permission denied` al correr `.sh` | No executable | `chmod +x scripts/sync-skills.sh` |
| Scripts que mencionan `/usr/bin/python3` fallan en Windows | Path hardcodeado Mac-only | Reportarlo — el path debe ser `python3` o `python`. Audit pendiente |
