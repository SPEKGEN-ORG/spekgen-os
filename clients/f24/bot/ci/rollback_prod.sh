#!/usr/bin/env bash
# rollback_prod.sh — restaura el bot LIVE (PROD 5258612) al último estado que pasó smoke.
#
# Diseño GitOps (sin llaves en git): el punto de rollback es un SHA de commit guardado en
# _BLUEPRINTS/LAST_GOOD_prod.sha. Aquí: checkout de la FUENTE del bot en ese commit → rebuild
# del blueprint (llaves desde env/.env) → deploy a prod → restaurar el árbol de trabajo.
#
# Lo usa el pipeline cuando un deploy nuevo rompe el smoke de PROD. Reusa deploy_f24_bot.sh.
# Requiere GHL_API_KEY + ANTHROPIC_API_KEY en el entorno (CI: secrets; local: F24/.env).
#
# Uso:  ./ci/rollback_prod.sh
set -euo pipefail

BOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SHA_FILE="$BOT_DIR/_BLUEPRINTS/LAST_GOOD_prod.sha"

# Archivos FUENTE que alimentan el build (los únicos que hay que revertir para reproducir el bot).
INPUTS=(
  "F24_BOT_SYSTEM_PROMPT.md"
  "F24_BOT_CANNED_RESPONSES.md"
  "F24_BOT_KNOWLEDGE"
  "build_f24_bot_blueprint.py"
)

if [[ ! -f "$SHA_FILE" ]]; then
  echo "ERROR: no existe $SHA_FILE — no hay punto de rollback. Aborta."
  exit 1
fi
GOOD_SHA="$(tr -d '[:space:]' < "$SHA_FILE")"
if [[ -z "$GOOD_SHA" ]]; then
  echo "ERROR: $SHA_FILE está vacío. Aborta."
  exit 1
fi

cd "$BOT_DIR"
REL_INPUTS=()
for p in "${INPUTS[@]}"; do REL_INPUTS+=("clients/f24/bot/$p"); done

echo "↩️  ROLLBACK: restaurando la fuente del bot al commit bueno $GOOD_SHA"
git -C "$BOT_DIR" checkout "$GOOD_SHA" -- "${REL_INPUTS[@]}"

echo "Reconstruyendo blueprint desde la fuente buena..."
python3 build_f24_bot_blueprint.py

# Fuerza el PATCH (invalida el hash de idempotencia que quedó con el blueprint roto).
rm -f "$BOT_DIR/_BLUEPRINTS/.last_deployed_prod.sha256"
CONFIRM_PROD=yes ./deploy_f24_bot.sh prod "rollback-$(date -u +%Y%m%d-%H%M%S)"

echo "Restaurando el árbol de trabajo a HEAD (la fuente revertida era temporal)..."
git -C "$BOT_DIR" checkout HEAD -- "${REL_INPUTS[@]}"

echo "Rollback aplicado: PROD quedó con el blueprint del commit $GOOD_SHA."
