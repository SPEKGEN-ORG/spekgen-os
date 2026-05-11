#!/bin/bash
# sync-skills.sh — Symlinkea todas las skills del repo a ~/.claude/skills/
#
# Busca SKILL.md en:
#   $REPO/skills/GLOBALES/*
#   $REPO/skills/PERSONALIZADAS/*
#   $REPO/skills/meta-publish/   (caso especial — skill standalone)
# y los symlinkea con el nombre de la carpeta a $HOME/.claude/skills/.
#
# Personal scope (~/.claude/skills) aparece en panel "Personal skills" del app
# y está disponible en cualquier proyecto. Ref: https://code.claude.com/docs/en/skills
#
# Idempotente: limpia symlinks rotos previos, skip los que ya están correctos.
# Para Mac/Linux. En Windows usar el equivalente PowerShell en SETUP.md sección 2.

set -e

# Detecta REPO root caminando hacia arriba desde este script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_SOURCE="$REPO_ROOT/skills"
SKILLS_TARGET="$HOME/.claude/skills"
LOG="$SCRIPT_DIR/sync-skills.log"

if [ ! -d "$SKILLS_SOURCE" ]; then
    echo "ERROR: No existe $SKILLS_SOURCE. ¿Estás corriendo desde un clone correcto del repo?" >&2
    exit 1
fi

mkdir -p "$SKILLS_TARGET"

installed=0
updated=0
skipped=0
broken_cleaned=0

# Limpia symlinks rotos previos
for link in "$SKILLS_TARGET"/*; do
    if [ -L "$link" ] && [ ! -e "$link" ]; then
        rm "$link"
        broken_cleaned=$((broken_cleaned + 1))
    fi
done

# Categorías a escanear
categories=("GLOBALES" "PERSONALIZADAS")

for category in "${categories[@]}"; do
    src_dir="$SKILLS_SOURCE/$category"
    [ -d "$src_dir" ] || continue

    for skill_dir in "$src_dir"/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name=$(basename "$skill_dir")

        # Skip _DEPRECATED, _ARCHIVE, *.skill, *.bak
        case "$skill_name" in
            _DEPRECATED|_ARCHIVE|_deprecated|_archive|*.skill|*.bak) continue ;;
        esac

        # Debe contener SKILL.md
        if [ ! -f "$skill_dir/SKILL.md" ]; then
            skipped=$((skipped + 1))
            continue
        fi

        target="$SKILLS_TARGET/$skill_name"
        expected="${skill_dir%/}"

        if [ -L "$target" ]; then
            current=$(readlink "$target")
            if [ "$current" = "$expected" ]; then
                continue  # ya correcto
            fi
            rm "$target"
            updated=$((updated + 1))
        elif [ -e "$target" ]; then
            # No es symlink pero existe (carpeta real o archivo) — no tocar
            echo "WARN: $target existe y no es symlink. Skip." >&2
            skipped=$((skipped + 1))
            continue
        fi

        ln -s "$expected" "$target"
        installed=$((installed + 1))
    done
done

# Caso especial meta-publish (en raíz de skills/)
if [ -d "$SKILLS_SOURCE/meta-publish" ] && [ -f "$SKILLS_SOURCE/meta-publish/SKILL.md" ]; then
    target="$SKILLS_TARGET/meta-publish"
    expected="$SKILLS_SOURCE/meta-publish"
    if [ -L "$target" ]; then
        [ "$(readlink "$target")" = "$expected" ] || { rm "$target"; ln -s "$expected" "$target"; updated=$((updated + 1)); }
    else
        ln -s "$expected" "$target"
        installed=$((installed + 1))
    fi
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] $installed installed, $updated updated, $broken_cleaned cleaned, $skipped skipped" >> "$LOG"

if [ "$installed" -gt 0 ] || [ "$updated" -gt 0 ] || [ "$broken_cleaned" -gt 0 ]; then
    echo "Skills synced: $installed installed, $updated updated, $broken_cleaned cleaned ($SKILLS_SOURCE → $SKILLS_TARGET)"
fi
