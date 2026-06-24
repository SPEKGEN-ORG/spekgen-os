#!/usr/bin/env python3
"""FIX QUIRURGICO: el tagger 5405187 se CAYO y se DESACTIVO (2026-06-16 ~22:16).

Causa raiz: un lead fuente-facebook llego con telefono NULL en la conversacion GHL.
El modulo Meta CAPI hace sha256(phone) -> sha256(null) lanza DataError fatal ->
tras 3 errores Make desactivo TODO el scenario -> desde entonces NINGUN lead
(google/fb/organico) se tagea. Por eso el board sale sin tags.

Fix: agregar al filtro del modulo Meta CAPI (graph.facebook.com) una 2da condicion
AND = "el telefono existe". Asi un FB-lead sin telefono SALTA la conversion (en vez de
crashear) y el tagueo (que corre ANTES del Router) sigue funcionando para todos.

Idempotente: si la condicion ya existe, no la duplica.
Verify-after-write (blueprint eventually-consistent). NO toca mapper/scheduling/interface.

  PYTHONUTF8=1 py fix_capi_null_phone.py --dry-run   # muestra el filtro nuevo, no PATCHea
  PYTHONUTF8=1 py fix_capi_null_phone.py             # aplica + verifica
"""
import io, sys, json, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPKENV = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
SCENARIO = 5405187
BASE = "https://us2.make.com/api/v2/scenarios/%d" % SCENARIO
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DRY = "--dry-run" in sys.argv
PHONE_EXPR = '{{first(map(2.data.conversations;"phone"))}}'


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
    """Devuelve el modulo cuyo url apunta a graph.facebook.com (puede estar dentro de un Router)."""
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
    sys.exit("No encontre el modulo Meta CAPI (graph.facebook.com) en el blueprint.")

flt = capi.setdefault("filter", {"name": "Solo fuente-facebook", "conditions": [[]]})
conds = flt.setdefault("conditions", [[]])
group = conds[0]  # primer grupo AND

already = any(c.get("a") == PHONE_EXPR and c.get("o") == "exist" for c in group)
if already:
    print("La guarda de telefono ya existe -> nada que hacer. (idempotente)")
    sys.exit(0)

group.append({"a": PHONE_EXPR, "o": "exist"})
print("Filtro Meta CAPI (modulo id %s) ahora:" % capi.get("id"))
print(json.dumps(flt, ensure_ascii=False, indent=2))

if DRY:
    print("\n[DRY-RUN] No se PATCHeo nada.")
    sys.exit(0)

bp.pop("interface", None)
bp.pop("scheduling", None)
res = api("PATCH", BASE, {"blueprint": json.dumps(bp, ensure_ascii=False), "name": bp.get("name")})
rs = res.get("scenario", res)
print("PATCHED -> isinvalid:", rs.get("isinvalid"), "| isActive:", rs.get("isActive"))

# verify-after-write
cbp = get_blueprint()
ccapi = find_capi(cbp["flow"])
ok = ccapi and any(c.get("a") == PHONE_EXPR and c.get("o") == "exist"
                   for c in ccapi.get("filter", {}).get("conditions", [[]])[0])
meta = api("GET", BASE).get("scenario", {})
print("VERIFY -> guarda presente:", bool(ok),
      "| isinvalid:", meta.get("isinvalid"), "| isActive:", meta.get("isActive"))
