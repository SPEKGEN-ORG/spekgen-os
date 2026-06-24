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

# === Scenario IDs + hook IDs (Make team 354061) ===
# PROD = cerebro LIVE (recibe tráfico real de WhatsApp). DEV = clon aislado para pruebas.
# OJO: mapeo CORREGIDO 2026-06-24. Antes 'dev' apuntaba al LIVE 5258612 (footgun grave:
# cualquiera que corriera "deploy dev" pisaba el bot de producción).
case "$TARGET" in
  prod) SCENARIO_ID=5258612; HOOK=2394767; SUFFIX="PROD" ;;   # LIVE — tráfico real
  dev)  SCENARIO_ID=5381174; HOOK=2451202; SUFFIX="DEV"  ;;   # aislado — sin tráfico
  *) echo "Target must be prod or dev"; exit 1 ;;
esac

# Candado anti-accidente: deployar a PROD (el bot LIVE) exige confirmación explícita.
# Interactivo → teclear PROD. No interactivo (cron/CI) → exportar CONFIRM_PROD=yes.
if [[ "$TARGET" == "prod" && "${CONFIRM_PROD:-}" != "yes" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "⚠️  Vas a deployar al BOT LIVE (5258612). Escribe PROD para confirmar: " _ans
    [[ "$_ans" == "PROD" ]] || { echo "Cancelado."; exit 1; }
  else
    echo "ERROR: deploy a PROD requiere CONFIRM_PROD=yes (no interactivo). Cancelado."; exit 1
  fi
fi

if [[ "$SCENARIO_ID" == "0" || "$HOOK" == "0" ]]; then
  echo "ERROR: scenario/hook IDs no configurados. Edita deploy_f24_bot.sh."
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

# Estampa el commit git en el nombre del scenario → en Make UI se ve EXACTAMENTE qué commit
# está live. "-dirty" = se deployó con cambios SIN COMMITEAR en archivos FUENTE del bot (señal
# de un deploy manual fuera de git). Acotado a fuente para que el cron —que regenera los JSON de
# knowledge antes de deployar— NO salga falsamente dirty.
_HD="$(dirname "$0")"
GITSHA="$(git -C "$_HD" rev-parse --short HEAD 2>/dev/null || echo nogit)"
git -C "$_HD" diff --quiet -- F24_BOT_SYSTEM_PROMPT.md F24_BOT_CANNED_RESPONSES.md build_f24_bot_blueprint.py 2>/dev/null || GITSHA="${GITSHA}-dirty"

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
bp["name"] = "Ferre24 AI Bot WhatsApp (GHL) - $VERSION $SUFFIX [$GITSHA]"
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
