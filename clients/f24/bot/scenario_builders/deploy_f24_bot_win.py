#!/usr/bin/env python3
"""Deploy del blueprint F24 a Make (Windows-friendly, port de deploy_f24_bot.sh).

  PYTHONUTF8=1 py deploy_f24_bot_win.py dev    # scenario 5381174 (clon aislado, hook 2451202)
  PYTHONUTF8=1 py deploy_f24_bot_win.py prod   # scenario 5258612 (cerebro LIVE, hook 2394767)

Lee el blueprint del archivo versionado en _BLUEPRINTS. Hace verify-after-write
(GET) e imprime isinvalid/isActive. MAKE_API_TOKEN del .env de SPK (o env var).
"""
import os, io, sys, json, shutil, tempfile, datetime, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Lee el blueprint recién construido por build_f24_bot_blueprint.py (mismo path portable
# que ese script: /tmp en Mac/Linux, temp del sistema en Windows). Override por env/argv.
DEFAULT_BP = os.environ.get("F24_BP_OUT") or (
    "/tmp/f24_bot_bp_v1.json" if os.name != "nt"
    else os.path.join(tempfile.gettempdir(), "f24_bot_bp_v1.json"))
TARGETS = {"dev": (5381174, 2451202, "DEV"), "prod": (5258612, 2394767, "PROD")}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

target = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
if target not in TARGETS:
    sys.exit("Uso: py deploy_f24_bot_win.py <dev|prod> [version-tag] [ruta-blueprint]")
VERSION = sys.argv[2] if len(sys.argv) > 2 else "v4.7-promos-fix"
BP_FILE = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(DEFAULT_BP)
if not BP_FILE.exists():
    sys.exit(f"No existe el blueprint {BP_FILE}. Corre build_f24_bot_blueprint.py primero.")
SCENARIO_ID, HOOK, SUFFIX = TARGETS[target]

# token
tok = os.environ.get("MAKE_API_TOKEN", "")
if not tok:
    spk = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
    for l in io.open(spk, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith("MAKE_API_TOKEN="):
            tok = l.split("=", 1)[1].strip().strip('"').strip("'")
            break
if not tok:
    sys.exit("Falta MAKE_API_TOKEN (env o SPK .env)")

bp = json.load(io.open(BP_FILE, encoding="utf-8"))

# swap webhook hook id al target
def swap(flow):
    for m in flow:
        if m.get("id") == 1 and m.get("module") == "gateway:CustomWebHook":
            m["parameters"]["hook"] = HOOK
        if "routes" in m:
            for r in m["routes"]:
                swap(r.get("flow", []))
swap(bp["flow"])
bp["name"] = f"Ferre24 AI Bot WhatsApp (GHL) - {VERSION} {SUFFIX}"
scheduling = bp.pop("scheduling", None)
bp.pop("interface", None)
body = {"blueprint": json.dumps(bp, ensure_ascii=False), "name": bp["name"]}
if scheduling:
    body["scheduling"] = json.dumps(scheduling)

print(f"Deploy -> scenario {SCENARIO_ID} ({SUFFIX}), hook {HOOK}")
req = urllib.request.Request(f"https://us2.make.com/api/v2/scenarios/{SCENARIO_ID}",
                             data=json.dumps(body).encode(), method="PATCH")
req.add_header("Authorization", "Token " + tok)
req.add_header("Content-Type", "application/json")
req.add_header("User-Agent", UA)
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    s = resp.get("scenario", resp)
    print("  name     :", s.get("name"))
    print("  isinvalid:", s.get("isinvalid"), "(False = blueprint valido)")
    print("  isActive :", s.get("isActive"))
    arch = HERE / "_BLUEPRINTS" / f"f24_bot_{VERSION}_{target}_{datetime.date.today().isoformat()}.json"
    arch.parent.mkdir(exist_ok=True)
    shutil.copyfile(BP_FILE, arch)
    print("  archivado:", arch.name)
except urllib.error.HTTPError as e:
    print("PATCH ERROR", e.code, e.read().decode()[:500])
    sys.exit(1)
