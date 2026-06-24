#!/usr/bin/env python3
"""Arregla el gating: pone el modulo Meta CAPI y el de captura gclid en RUTAS PARALELAS
de un Router, no en secuencia.

Bug: en Make un filtro en un modulo secuencial corta TODO el flujo aguas abajo. Con Meta(6)
y gclid(7) en secuencia, un lead google (filtro facebook de 6 falla) cortaba el flujo y el
modulo gclid(7) nunca corria. Solucion: Router con 2 rutas independientes -> cada filtro
decide su ruta sin afectar a la otra.

Estructura final: 1 webhook -> 2 GET conv -> 3 GET msgs -> 4 bodies -> 5 tag[filtro marcador]
  -> 6 Router -> ruta A: Meta CAPI [filtro facebook]
              -> ruta B: captura gclid [filtro ref:]

Preserva los mappers EXACTOS de los modulos Meta/gclid existentes (solo los re-ubica).
Idempotente: si ya hay un Router, no hace nada.

  PYTHONUTF8=1 py restructure_tagger_router.py            # aplica
  PYTHONUTF8=1 py restructure_tagger_router.py --dry-run
"""
import io, sys, json, copy, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPKENV = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
SCENARIO = 5405187
BASE = "https://us2.make.com/api/v2/scenarios/%d" % SCENARIO
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DRY = "--dry-run" in sys.argv


def envget(p, key):
    for l in io.open(p, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith(key + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'").split("  #")[0].strip()
    return ""


MAKE_TOKEN = envget(SPKENV, "MAKE_API_TOKEN")


def api(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Token " + MAKE_TOKEN)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", UA)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:600]); sys.exit(1)


def get_blueprint():
    r = api("GET", BASE + "/blueprint")
    bp = r.get("response", r).get("blueprint", r.get("blueprint"))
    if isinstance(bp, str):
        bp = json.loads(bp)
    return bp


bp = get_blueprint()
flow = bp["flow"]
print("Modulos actuales:", [m.get("module", m.get("id")) for m in flow])

if any(m.get("module") == "builtin:BasicRouter" for m in flow):
    print("Ya hay un Router -> nada que hacer."); sys.exit(0)


def is_meta(m):
    u = m.get("mapper", {}).get("url", "")
    return isinstance(u, str) and "graph.facebook.com" in u


def is_gclid(m):
    return "wa_gclid" in json.dumps(m.get("mapper", {})) or "FpgydkpdxKsQ7nVPkORo" in json.dumps(m.get("mapper", {}))


meta_mod = next((m for m in flow if is_meta(m)), None)
gclid_mod = next((m for m in flow if is_gclid(m)), None)
if not meta_mod or not gclid_mod:
    sys.exit("No encontre los modulos Meta/gclid para reubicar.")

# sacar Meta y gclid del flujo principal
base_flow = [m for m in flow if not is_meta(m) and not is_gclid(m)]
print("Flujo base (sin meta/gclid):", [m.get("id") for m in base_flow])

# re-id dentro de las rutas
meta_mod = copy.deepcopy(meta_mod); meta_mod["id"] = 7
meta_mod["metadata"] = {"designer": {"x": 1500, "y": -150}}
gclid_mod = copy.deepcopy(gclid_mod); gclid_mod["id"] = 8
gclid_mod["metadata"] = {"designer": {"x": 1500, "y": 150}}

router = {
    "id": 6,
    "module": "builtin:BasicRouter",
    "version": 1,
    "mapper": None,
    "metadata": {"designer": {"x": 1200, "y": 0}},
    "routes": [
        {"flow": [meta_mod]},    # ruta A: Meta CAPI (su filtro facebook ya viene en el modulo)
        {"flow": [gclid_mod]},   # ruta B: captura gclid (su filtro ref: ya viene en el modulo)
    ],
}
base_flow.append(router)
bp["flow"] = base_flow
bp.pop("interface", None)
bp.pop("scheduling", None)

if DRY:
    out = copy.deepcopy(router)
    for r in out["routes"]:
        for m in r["flow"]:
            m["mapper"]["headers"] = "[headers]"
            if "graph.facebook" in str(m["mapper"].get("url", "")):
                m["mapper"]["url"] = "graph.facebook.com/.../events?access_token=***"
    print("Estructura final flow:", [m.get("module", m.get("id")) for m in base_flow])
    print(json.dumps(out, ensure_ascii=False, indent=2)); sys.exit(0)

res = api("PATCH", BASE, {"blueprint": json.dumps(bp, ensure_ascii=False), "name": bp.get("name")})
rs = res.get("scenario", res)
print("PATCHED -> isinvalid:", rs.get("isinvalid"), "| isActive:", rs.get("isActive"))

cbp = get_blueprint()
top = [m.get("module", m.get("id")) for m in cbp["flow"]]
router_live = next((m for m in cbp["flow"] if m.get("module") == "builtin:BasicRouter"), None)
routes = [[mm.get("id") for mm in r.get("flow", [])] for r in (router_live or {}).get("routes", [])]
meta = api("GET", BASE); ms = meta.get("scenario", meta)
print("VERIFY -> top flow:", top, "| router routes:", routes,
      "| isinvalid:", ms.get("isinvalid"), "| isActive:", ms.get("isActive"))
