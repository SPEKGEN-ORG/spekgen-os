# Onboarding Pedro — spekgen-os

Pedro, este es tu kit de arranque post-migración a GitHub. Léelo de arriba a abajo, no te saltes pasos.

---

## 1. Acceso a GitHub

1. Tu cuenta GitHub: `<tu_username>` (Gibran te invita como Member de `spekgen-org`).
2. Aceptas el invite en https://github.com/spekgen-org → Pendientes.
3. Permisos iniciales: Maintainer en `spekgen-os` (puedes hacer PRs y mergear cosas no críticas; cambios en skills GLOBALES requieren approval de Gibran).

## 2. Clonar el repo

```powershell
# Windows (PowerShell, NO admin)
mkdir C:\dev
cd C:\dev
git clone https://github.com/spekgen-org/spekgen-os.git
cd spekgen-os
```

Si te pide credenciales, usa **personal access token** de GitHub (NO password). Generar uno: https://github.com/settings/tokens → "Generate new token (classic)" → scopes: `repo`, `read:org`, `workflow`. Guárdalo en lugar seguro — solo se muestra 1 vez.

## 3. Setup local

Sigue [SETUP.md](../SETUP.md) sección "Windows (Pedro)" paso por paso. Resumen:

```powershell
# Verificar Python ya instalado (3.12 confirmado en tu máquina)
python --version

# Instalar deps
python -m pip install --user openpyxl pypdf requests jinja2 pillow pymupdf playwright python-dotenv

# Verificar helper portable
python tools\spekgen_paths.py
# Output esperado: JSON con ruta a "01. CLIENTS OFFICIAL" + las 5 carpetas de clientes
```

Si el helper falla porque no encuentra `01. CLIENTS OFFICIAL`, define la variable de entorno con la ruta de tu Drive:

```powershell
# Ajusta la letra del drive según tu setup
[Environment]::SetEnvironmentVariable("SPEKGEN_ROOT", "G:\My Drive\01. CLIENTS OFFICIAL", "User")
# Cierra y abre PowerShell para que tome efecto.
```

## 4. Symlinks (junctions) de skills a Claude Code

Windows usa junctions en lugar de symlinks. Sin admin:

```powershell
mkdir $HOME\.claude\skills -ErrorAction SilentlyContinue

# Listar skills disponibles y crear junction de cada una
Get-ChildItem -Directory skills\GLOBALES, skills\PERSONALIZADAS | Where-Object {
    Test-Path "$($_.FullName)\SKILL.md"
} | ForEach-Object {
    $target = "$HOME\.claude\skills\$($_.Name)"
    if (Test-Path $target) { Remove-Item $target -Recurse -Force }
    cmd /c mklink /J "$target" "$($_.FullName)"
}

# Verificar (deberías ver ~37 junctions)
dir $HOME\.claude\skills
```

Cuando hagas `git pull` en el futuro, los junctions se actualizan automáticamente (apuntan a las carpetas, no a snapshots).

## 5. Credenciales — descifrar el archivo cifrado del repo

Todas las credenciales SPEKGEN viven cifradas en `secrets/credentials.env.enc` (AES-256). Gibran te pasa **un solo password** por Signal/WhatsApp encriptado — ese password descifra TODO.

```powershell
# Asegúrate de tener openssl. Si no:
#   Opción 1: Instala Git for Windows (lo incluye en C:\Program Files\Git\usr\bin\)
#   Opción 2: winget install ShiningLight.OpenSSL
#   Verifica: openssl version

# Descifrar
.\scripts\decrypt-secrets.ps1
# Te pide el password (te lo pasa Gibran). Genera $HOME\.env.spekgen.
```

Scripts del repo cargan `~\.env.spekgen` automáticamente con `python-dotenv`.

**Variables incluidas (entre las 150+):**

| Variable | Para qué |
|---|---|
| `SPEKGEN_SHOPIFY_STORE` + `SPEKGEN_SHOPIFY_TOKEN` | spekgen.com → outreach prospects |
| `APIFY_TOKEN` | Scrapear leads |
| `GMAIL_USER=outreach@spekgen.com` + `GMAIL_APP_PASSWORD` | Cold emails |
| `META_TOKEN` | SPEKGEN Agency token unificado (todos los clientes) |
| `{HC,LF,GR,MG,F24}_SHOPIFY_TOKEN` | Por cliente — los tienes pero úsalos solo si Gibran te asigna trabajo de ese cliente |
| `GHL_API_KEY_*` | GHL CRM por cliente |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | APIs directas (raro) |

**Si una credencial rota** (Gibran te avisa por chat):
```powershell
git pull origin main         # baja el .enc actualizado
.\scripts\decrypt-secrets.ps1  # re-descifra sobre tu .env.spekgen
```

**NO commitees** `~\.env.spekgen` ni ninguna versión descifrada. El `.gitignore` ya las excluye, pero ojo.

## 6. Tu primera semana

### 6.1 Cold calls B2B (arranca día 1)

Sistema completo de outreach. **Genera leads frescos cada mañana, dashboard para llamar, mockup automático cuando alguien dice "interesado".**

**Setup (una vez):**

```powershell
# Clonar el repo del sistema de prospectos (transferido a la org 2026-05-12)
cd C:\dev
git clone https://github.com/SPEKGEN-ORG/spekgen-prospectos.git
```

El sistema **vive en Drive**, no en el repo — porque el xlsx + el dashboard necesitan persistencia compartida. El repo solo contiene los GH Actions cloud (harvest bi-weekly) y el dashboard alterno cloud-friendly.

**Tu xlsx personal:** `SPK - SPEKGEN AGENCY/PROSPECTOS/SPEKGEN_PROSPECTOS_GDL.xlsx` (separado del de Gibran para evitar conflictos en Drive).

**Workflow diario (Mon-Fri):**

1. Abre el folder Drive en Explorer: `G:\My Drive\01. CLIENTS OFFICIAL\SPK - SPEKGEN AGENCY\PROSPECTOS\_tools\`
2. **Doble clic → `PEDRO_1_Generar_leads_del_dia.bat`** → genera 40 leads (20 GDL + 20 La Paz BCS) en tu xlsx.
3. **Doble clic → `PEDRO_2_Abrir_dashboard.bat`** → abre http://localhost:8771 con los leads del día.
4. Llama. Marca status en el dashboard (Pendiente / Contestó / Interesado / No interesado / Callback). El dashboard guarda al xlsx automáticamente.
5. **Cuando alguien diga "interesado"** → marca status "Interesado" y el sistema dispara un mockup automático (mockup factory). Te llega un link `spekgen.com/{slug}mockup` para mandarle.

> **Heads-up:** Los mockups actuales salen genéricos. Gibran y yo lo estamos pelando aparte — por ahora úsalos solo como referencia visual, no como propuesta final. Si llegas a un "sí", avisa para hacerle un mockup custom.

**Reglas de uso del Google Places API (compartido con Gibran):**
- 40 leads/día por operador es presupuesto razonable. NO corras el batch 2× el mismo día sin razón — la API tiene cuota.
- El `.seen_place_ids.json` es compartido entre tú y Gibran (via Drive) → no se duplican leads cross-operador.

**Skills relevantes para esta fase:**
- `/website-proposal` — genera mockup + propuesta + publica a spekgen.com (úsalo cuando un lead diga "sí, mándame algo")
- `/publish-prospect` — publica un set ya hecho
- `/kill-prospect` — cierra prospecto frío (libera el slot)

### 6.2 Familiarizarte con clientes activos
Lee `clients/{HC,LF,GR,MG,F24}/_CLIENT_CONTEXT.md` cuando los movamos al repo (próxima ola).

### 6.3 Probar el skill `/f24-product-research`
End-to-end en un SKU nuevo (sugerencia: CA-25PH Compresor de aire 25L). Pero AVÍSAME antes — quiero estar disponible si algo se rompe en tu máquina.

## 7. Workflow de cambios

- Cambios pequeños (typo en docs, fix en una skill de cliente que solo tú tocas): commit directo a main.
- Cambios grandes (skill nueva, refactor en `tools/`, cambios cross-client): branch + PR → ping a Gibran para review.
- Convención de commits: `feat(scope): mensaje` / `fix(scope): mensaje` / `docs(scope): mensaje`.

Ver [CONTRIBUTING.md](../CONTRIBUTING.md) para detalle.

## 8. Drive vs Repo — qué edita cada uno

- **Drive (Google Drive Desktop sincronizado a `01. CLIENTS OFFICIAL`):** xlsx clientes, imágenes producto, PDFs, deliverables, videos, brochures, backups. Editas directo en Drive como siempre.
- **Repo (GitHub `spekgen-org/spekgen-os`):** skills, scripts, docs, memory. Editas en VS Code/IDE → commit → push.
- **Local solo (`~\.env.spekgen`):** credenciales tuyas. NUNCA en Drive, NUNCA en repo.

## 9. Qué hacer si algo se rompe

- **Skills no aparecen en Claude Code:** corre los junctions del paso 4 de nuevo.
- **Script tira "No pude localizar 01. CLIENTS OFFICIAL":** define `$env:SPEKGEN_ROOT` (paso 3).
- **Script tira "python3 not found":** estás corriendo un comando legacy. Usa `python` o `py` en Windows. Si la skill lo tiene hardcodeado, repórtalo a Gibran como bug.
- **Permission denied al push:** revisa que tu PAT (personal access token) tenga scope `repo`.
- **Algo más:** WhatsApp a Gibran. No edites archivos críticos sin avisar.

## 10. Próximos hitos cross-team

Mes 1 (mayo):
- ☐ Migración inicial del repo (✓ hecha 11-may)
- ☐ Pedro setup + primer push
- ☐ Pedro hace primer outreach GDL
- ☐ Migrar `_CLIENT_CONTEXT.md` por cliente al repo (próxima ola)
- ☐ Migrar `delivery_data.json` + Hub builder al repo

Mes 2:
- ☐ Vault de secretos (Bitwarden free / Doppler) en lugar de Signal
- ☐ Auditoría de paths hardcodeados cross-codebase (HC outreach, GR autopublisher, etc.)
- ☐ Onboarding doc para empleado #3

---

**Bienvenido de regreso a SPEKGEN. Cualquier cosa, ping inmediato.**
