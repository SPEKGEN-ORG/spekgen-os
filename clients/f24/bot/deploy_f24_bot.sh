#!/usr/bin/env bash
# Deploy Ferre24 bot blueprint a prod o dev. Clon de HC deploy_bot.sh.
#
# Usage:
#   ./deploy_f24_bot.sh dev v1.0      # deploy /tmp/f24_bot_bp_v1.json a DEV
#   ./deploy_f24_bot.sh prod v1.0     # deploy a PROD
#
# Antes: /usr/bin/python3 build_f24_bot_blueprint.py  (regenera /tmp/f24_bot_bp_v1.json)
# El archivo se archiva en _BLUEPRINTS/ al terminar con éxito.

set -euo pipefail

TARGET="${1:-}"
VERSION="${2:-}"

if [[ -z "$TARGET" || -z "$VERSION" ]]; then
  echo "Usage: $0 <prod|dev> <version-tag>   (e.g. $0 dev v1.0)"
  exit 1
fi

# === Scenario IDs + hook IDs (Make team 354061, creados 2026-06-01) ===
# Nota: por ahora hay 1 solo webhook (2394767). DEV usa ese hook. Cuando se cree el
# scenario PROD con su propio webhook, rellenar prod abajo.
case "$TARGET" in
  prod) SCENARIO_ID=0; HOOK=0; SUFFIX="PROD" ;;          # PENDIENTE: crear PROD + su hook
  dev)  SCENARIO_ID=5258612; HOOK=2394767; SUFFIX="DEV" ;;
  *) echo "Target must be prod or dev"; exit 1 ;;
esac

if [[ "$SCENARIO_ID" == "0" || "$HOOK" == "0" ]]; then
  echo "ERROR: scenario/hook IDs no configurados todavía (Fase 2). Edita deploy_f24_bot.sh."
  exit 1
fi

BP="/tmp/f24_bot_bp_v1.json"
PATCH="/tmp/f24_bot_patch.json"
BLUEPRINTS_DIR="$(dirname "$0")/_BLUEPRINTS"
# Cloud (GitHub Actions): MAKE_API_TOKEN viene como env var (secret). Local: del .env de SPK.
ENV_SPK="$(dirname "$0")/../../../SPK - SPEKGEN AGENCY/.env"
MAKE_TOKEN="${MAKE_API_TOKEN:-}"
if [[ -z "$MAKE_TOKEN" && -f "$ENV_SPK" ]]; then
  MAKE_TOKEN=$(grep -E '^MAKE_API_TOKEN=' "$ENV_SPK" | cut -d= -f2)
fi

if [[ ! -f "$BP" ]]; then
  echo "ERROR: $BP no existe. Corre '/usr/bin/python3 build_f24_bot_blueprint.py' primero."
  exit 1
fi

mkdir -p "$BLUEPRINTS_DIR"

python3 <<PYEOF
import json
with open("$BP") as f: bp = json.load(f)
def swap(flow):
    for m in flow:
        if m.get("id") == 1 and m.get("module") == "gateway:CustomWebHook":
            m["parameters"]["hook"] = $HOOK
        if "routes" in m:
            for r in m["routes"]: swap(r.get("flow", []))
swap(bp["flow"])
bp["name"] = "Ferre24 AI Bot WhatsApp (GHL) - $VERSION $SUFFIX"
scheduling = bp.pop("scheduling", None)
bp.pop("interface", None)
body = {"blueprint": json.dumps(bp),
        "scheduling": json.dumps(scheduling) if scheduling else None,
        "name": bp["name"]}
body = {k: v for k, v in body.items() if v is not None}
with open("$PATCH", "w") as f: json.dump(body, f)
PYEOF

echo "Subiendo a scenario $SCENARIO_ID ($SUFFIX)..."
RESP=$(curl -sS -X PATCH "https://us2.make.com/api/v2/scenarios/$SCENARIO_ID" \
  -H "Authorization: Token $MAKE_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @"$PATCH")

echo "$RESP" | python3 -c "
import json, sys
r = json.load(sys.stdin); s = r.get('scenario', r)
print('  name:', s.get('name')); print('  isinvalid:', s.get('isinvalid')); print('  isActive:', s.get('isActive'))
"

ARCHIVE="$BLUEPRINTS_DIR/f24_bot_${VERSION}_${TARGET}_$(date +%Y-%m-%d).json"
cp "$BP" "$ARCHIVE"
echo "Archivado: $ARCHIVE"
