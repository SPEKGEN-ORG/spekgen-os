---
name: Skill Creation — Solo carpeta con SKILL.md. Sin empaquetar. Sin .skill. Sin clicks.
description: Arquitectura oficial Anthropic (2026-04-17). Las skills son simplemente carpetas con SKILL.md en ~/.claude/skills/. El hook SessionStart de SPEKGEN symlinkea automáticamente desde SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/{GLOBALES,PERSONALIZADAS}/. Ref oficial https://code.claude.com/docs/en/skills
type: feedback
originSessionId: 8fc86e47-8ccd-434f-a763-69bd1874cb37
---
## Lo que dice la docu oficial (https://code.claude.com/docs/en/skills)

Skills tienen 4 scopes, nada más:

| Scope | Path | Aparece en |
|---|---|---|
| Enterprise | Managed settings | Toda la org |
| **Personal** | `~/.claude/skills/<nombre>/SKILL.md` | Panel "Personal skills" de claude.ai + disponible en todos tus proyectos |
| Project | `.claude/skills/<nombre>/SKILL.md` | Solo ese proyecto, NO aparece en panel |
| Plugin | `<plugin>/skills/<nombre>/SKILL.md` | Donde el plugin esté activado |

**Una skill ES una carpeta con SKILL.md adentro.** Sin zip, sin empacar, sin archivos `.skill`, sin clicks de GUI. Claude Code tiene live change detection: cambios en `~/.claude/skills/` se detectan dentro de la misma sesión (solo requiere reinicio si la carpeta top-level no existía al iniciar).

## Arquitectura SPEKGEN (2026-04-17)

**Fuente de verdad (organización humana):**
```
SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/
├── GLOBALES/                    ← skills cross-client
│   └── <nombre>/SKILL.md
└── PERSONALIZADAS/              ← skills client-specific
    └── <nombre>/SKILL.md
```

El split GLOBALES/PERSONALIZADAS es solo organización mental para Gibran. A Claude Code le da igual.

**Lo que Claude Code realmente lee:**
```
~/.claude/skills/
└── <nombre> → symlink → SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/<cat>/<nombre>/
```

**Pegamento:** `.claude/hooks/sync-skills.sh` (ejecutado por hook SessionStart en `.claude/settings.local.json`) symlinkea toda carpeta con SKILL.md de GLOBALES/PERSONALIZADAS hacia `~/.claude/skills/`.

## Flujo para crear una skill nueva

1. `mkdir -p "SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/<GLOBALES|PERSONALIZADAS>/<nombre>/"`
2. Escribir `SKILL.md` con frontmatter válido:
   ```yaml
   ---
   name: nombre-skill
   description: Qué hace la skill y cuándo usarla (front-load key use case, 1,536 char cap)
   ---
   ```
   Campos opcionales: `allowed-tools`, `disable-model-invocation`, `user-invocable`, `argument-hint`, `model`, `effort`, `context: fork`, `agent`, `paths`, `hooks`
3. Agregar scripts, templates o referencias dentro de la misma carpeta si aplica
4. **Al siguiente SessionStart**, el hook symlinkea automáticamente → aparece en panel Personal skills y es invocable como `/nombre-skill`

**No hay que:** empacar, abrir bundles, hacer clicks en GUI, `package_skill.py`, copiar archivos manualmente.

## Frontmatter — cosas importantes

- `name`: kebab-case (lowercase + hyphens), max 64 chars. Si se omite, usa nombre de carpeta.
- `description`: lo más importante. Claude lo usa para decidir cuándo invocar la skill. Pushy > neutral.
- `disable-model-invocation: true`: solo Gibran invoca con `/nombre`. Para deploys, commits, acciones con side effects.
- `user-invocable: false`: solo Claude la invoca (background knowledge).
- `allowed-tools`: pre-approve herramientas mientras la skill está activa.
- `$ARGUMENTS`, `$0`, `$1`, etc.: substitución de argumentos al invocar.
- `` !`comando` ``: inyecta output de shell antes de mandar el prompt a Claude.

## Qué NO hacer

- ❌ No dejar SKILL.md suelto en `.claude/commands/` o `.claude/skills/` fuera de SPEKGEN AGENCY (se pierde la fuente de verdad)
- ❌ No empacar `.skill` bundles (obsoleto para uso local — solo distribución externa)
- ❌ No crear skills en `_ARCHIVE/` o con nombres que terminen en `.skill`/`.bak` (el hook los ignora)
- ❌ No usar el flujo viejo `package_skill.py + open .skill + GUI install` — era workaround de antes del live-reload

## Verificación

- Log del sync: `.claude/hooks/sync-skills.log`
- `ls ~/.claude/skills/` debe incluir la skill como symlink
- Panel "Personal skills" en claude.ai debe mostrarla
- Invocable con `/nombre-skill` en cualquier sesión de Claude Code

## Historia

**2026-04-17:** Corrección de arquitectura. El flujo viejo `package_skill.py + .skill + GUI install` era un workaround que Anthropic ya no necesita. Antes 3+ skills quedaron huérfanas (hc-organic-post, hc-cold-outreach, cross-client-intel, etc.) porque el flujo tenía 6 pasos manuales fáciles de romper. Arquitectura actual: 1 paso (escribir SKILL.md en la carpeta correcta), 0 clicks.
