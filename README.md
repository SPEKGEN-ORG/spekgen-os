# spekgen-os

Sistema operativo de SPEKGEN — agencia de marketing digital 99.99% AI con sede en Jalisco, México.

Este repo contiene **código, skills, configuraciones y documentación** de la agencia. Los **datos operativos** (xlsx clientes, imágenes producto, PDFs, deliverables, videos) viven en Google Drive sincronizado a `01. CLIENTS OFFICIAL/`. Los **secretos** (`.env`, tokens) viven localmente en cada máquina y se comparten entre miembros vía canal seguro (Signal/WhatsApp encriptado) hasta migrar a vault dedicado.

## Estructura

```
spekgen-os/
├── README.md                ← este archivo
├── SETUP.md                 ← cómo instalar en Mac/Windows/Linux
├── CONTRIBUTING.md          ← cómo agregar/editar skills, commit conventions
├── .gitignore               ← excluye .env, binarios, datos
├── .env.example             ← template de variables (NUNCA commits .env real)
│
├── skills/                  ← TODAS las skills SPEKGEN
│   ├── GLOBALES/            ← skills cross-client (factory-batch, yt-insights, etc.)
│   ├── PERSONALIZADAS/      ← skills específicas por cliente (f24-product-research, hc-organic-post, lf-media-buying-cycle, etc.)
│   └── meta-publish/        ← skill cross-client de publishing Meta API
│
├── tools/                   ← helpers compartidos entre skills
│   └── spekgen_paths.py     ← resolución portable de paths Drive (Mac/Win/Linux)
│
├── memory/                  ← knowledge files de Claude (project_*, feedback_*, MEMORY.md)
│
├── docs/                    ← documentación operativa
│   ├── platform-selection.md  ← cuándo usar GHL vs Make vs MCP vs etc.
│   ├── credentials-map.md     ← qué credencial vive dónde (sin valores)
│   └── client-onboarding.md   ← cómo onboardear un cliente nuevo
│
├── clients/                 ← config por cliente (NO data, solo source-of-truth de contexto)
│   ├── HC/                  ← _CLIENT_CONTEXT.md, _KNOWLEDGE_BASE.md, CLAUDE.md
│   ├── LF/
│   ├── GR/
│   ├── MG/
│   └── F24/
│
└── scripts/                 ← scripts agency-level (no son skills, son tooling)
    └── sync-skills.sh       ← hook SessionStart para Claude Code
```

## Quick start (Gibran y Pedro)

Ver [SETUP.md](SETUP.md) para instrucciones completas según OS.

Resumen:
1. `git clone https://github.com/g-bran/spekgen-os.git ~/dev/spekgen-os` (Mac/Linux) o `C:\dev\spekgen-os` (Windows)
2. Verificar que Google Drive Desktop tenga `01. CLIENTS OFFICIAL` sincronizado
3. Instalar Python 3 + deps: `pip install openpyxl pypdf playwright requests jinja2 pillow pymupdf`
4. Copiar `.env.example` a `~/.env.spekgen` y llenar con valores reales (pedirlos por canal seguro al admin)
5. Symlink skills al directorio de Claude (Mac/Linux automático vía hook; Windows manual — ver SETUP.md)
6. En Claude Code: las skills aparecen como `/factory-batch`, `/publish-prospect`, `/f24-product-research`, etc.

## Reglas

- **NUNCA** commits `.env`, `*.xlsx`, `*.pdf`, imágenes, o binarios > 1MB.
- **NUNCA** hardcodear `/Users/gibranalonzo/...` o `C:\Users\...` en código. Usar `tools/spekgen_paths.py`.
- **SIEMPRE** PR para cambios en `skills/`. Auto-merge solo para `docs/` y `memory/`.
- **Convención de commits:** `tipo(scope): mensaje`. Tipos: `feat`, `fix`, `docs`, `refactor`, `chore`. Scope = skill name o folder. Ej: `fix(f24-product-research): portable path resolution`.

## Stack técnico común

- **Python 3.9+** (en Mac usar `python3`, en Windows `python` o `py`)
- **Claude Code** como host de skills
- **Google Drive Desktop** para data sync
- **Make** para automatizaciones recurrentes
- **GH Actions** para crons autónomos
- **Shopify Admin API** para PDPs/páginas
- **Meta Marketing API** para ads CRUD
- **Various** MCPs conectados (GHL, ClickUp, Gmail, Calendar, Clarity, Chrome, Canva)

## Soporte

- Gibran Alonzo — fundador, decisiones de vida o muerte
- Pedro — socio, ops y outreach GDL
- Futuros empleados → seguir CONTRIBUTING.md
