#!/usr/bin/env python3
"""HARDEN: hace null-safe el sha256 del modulo Meta CAPI (id 7) del tagger 5405187.

El filtro "phone exist" no basta: los items que quedaron EN COLA durante el outage
se ejecutan contra el snapshot viejo del blueprint y siguen lanzando sha256(null),
lo que vuelve a acumular maxErrors y DESACTIVA el scenario. Fix definitivo = que el
sha256 NUNCA reciba null: coalesce del telefono a "0" antes del replace.

  first(map(2.data.conversations;"phone"))
  -> ifempty(first(map(2.data.conversations;"phone"));"0")

Solo toca el jsonStringBodyContent del modulo graph.facebook.com (NO el filtro, que
usa el mismo substring y debe quedar intacto). Idempotente. Verify-after-write.

  PYTHONUTF8=1 py harden_capi_sha256.py --dry-run
  PYTHONUTF8=1 py harden_capi_sha256.py
"""
import io, sys, json, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPKENV = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
SCENARIO = 5405187
BASE = "https://us2.make.com/api/v2/scenarios/%d" % SCENARIO
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DRY = "--dry-run" in sys.argv

OLD = 'first(map(2.data.conversations;\\"phone\\"))'
NEW = 'ifempty(first(map(2.data.conversations;\\"phone\\"));\\"0\\")'


def envget(p, key):
    for l in io.open(p, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith(key + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'").split("  #")[0].strip()
    return ""


MAKE_TOKEN = envget(SPKENV, "MAKE_API_TOKEN")
if not MAKE_TOKEN:
    sys.exit("Falta MAKE_API_TOKEN en el .env de SPK")


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


def find_capi(flow):
    for m in flow:
        url = (m.get("mapper") or {}).get("url")
        if isinstance(url, str) and "graph.facebook.com" in url:
            return m
        for route in m.get("routes", []) or []:
            hit = find_capi(route.get("flow", []))
            if hit:
                return hit
    return None


bp = get_blueprint()
capi = find_capi(bp["flow"])
if not capi:
    sys.exit("No encontre el modulo Meta CAPI (graph.facebook.com).")

body = capi["mapper"].get("jsonStringBodyContent", "")
if NEW in body:
    print("sha256 ya es null-safe -> nada que hacer. (idempotente)")
    sys.exit(0)
if "sha256(replace(" + OLD not in body:
    print("ADVERTENCIA: no encontre el patron sha256 esperado. Body actual:")
    print(body); sys.exit(1)

capi["mapper"]["jsonStringBodyContent"] = body.replace("sha256(replace(" + OLD,
                                                        "sha256(replace(" + NEW)
print("jsonStringBodyContent (modulo id %s) ahora:" % capi.get("id"))
print(capi["mapper"]["jsonStringBodyContent"])

if DRY:
    print("\n[DRY-RUN] No se PATCHeo nada.")
    sys.exit(0)

bp.pop("interface", None)
bp.pop("scheduling", None)
res = api("PATCH", BASE, {"blueprint": json.dumps(bp, ensure_ascii=False), "name": bp.get("name")})
rs = res.get("scenario", res)
print("PATCHED -> isinvalid:", rs.get("isinvalid"), "| isActive:", rs.get("isActive"))

cbp = get_blueprint()
ccapi = find_capi(cbp["flow"])
ok = ccapi and NEW in ccapi["mapper"].get("jsonStringBodyContent", "")
meta = api("GET", BASE).get("scenario", {})
print("VERIFY -> null-safe presente:", bool(ok),
      "| isinvalid:", meta.get("isinvalid"), "| isActive:", meta.get("isActive"))
