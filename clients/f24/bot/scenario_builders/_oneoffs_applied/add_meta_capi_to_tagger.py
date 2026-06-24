#!/usr/bin/env python3
"""Agrega QUIRURGICAMENTE el modulo Meta CAPI (Lead) al tagger LIVE 5405187.

- GET del blueprint ACTUAL (preserva modulos 1-5 tal cual estan en produccion).
- Append modulo 6 SOLO si no existe ya (idempotente).
- Modulo 6 = http:MakeRequest v4, contentType json + inputMethod jsonString
  (config VALIDADA via Make validator; el intento previo fallo por usar raw/data inexistentes).
- Filtro: solo fuente-facebook (marcador U+200C en 4.bodies). Match Meta = telefono SHA-256.
- event_id = contact_id  -> Meta deduplica. stopOnHttpError=False -> un fallo HTTP NO
  acumula errores hacia maxErrors (lo que desactivo el tagger la vez pasada).
- Token Meta se lee del .env aqui (NUNCA entra al contexto del chat).

  PYTHONUTF8=1 py add_meta_capi_to_tagger.py            # aplica
  PYTHONUTF8=1 py add_meta_capi_to_tagger.py --dry-run  # muestra el modulo, no PATCHea
"""
import io, sys, json, copy, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
F24ENV = HERE.parents[1] / ".env"
SPKENV = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
SCENARIO = 5405187
BASE = "https://us2.make.com/api/v2/scenarios/%d" % SCENARIO
FB_MARK = chr(0x200C)   # marcador facebook (zero-width non-joiner)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DRY = "--dry-run" in sys.argv


def envget(p, key):
    for l in io.open(p, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith(key + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'").split("  #")[0].strip()
    return ""


MAKE_TOKEN = envget(SPKENV, "MAKE_API_TOKEN")
META_TOKEN = envget(F24ENV, "META_TOKEN")
META_PIXEL = envget(F24ENV, "META_PIXEL_ID")
if not (MAKE_TOKEN and META_TOKEN and META_PIXEL):
    sys.exit("Falta MAKE_API_TOKEN / META_TOKEN / META_PIXEL_ID en los .env")


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


# 1) GET blueprint actual (autoritativo) -- endpoint /blueprint
def get_blueprint():
    r = api("GET", BASE + "/blueprint")
    bp = r.get("response", r).get("blueprint", r.get("blueprint"))
    if isinstance(bp, str):
        bp = json.loads(bp)
    return bp

bp = get_blueprint()
flow = bp["flow"]
print("Modulos actuales:", [m.get("id") for m in flow])

# 2) idempotente: no duplicar el modulo Meta
if any(m.get("id") == 6 or (isinstance(m.get("mapper", {}).get("url"), str)
                            and "graph.facebook.com" in m["mapper"]["url"]) for m in flow):
    print("Modulo Meta CAPI ya existe -> nada que hacer."); sys.exit(0)

# 3) construir modulo 6 (config validada)
json_body = ('{"data":[{"event_name":"Lead","event_time":{{formatDate(now;"X")}},'
             '"action_source":"chat","event_id":"{{1.contact_id}}",'
             '"user_data":{"ph":["{{sha256(replace(first(map(2.data.conversations;\\"phone\\"));'
             '\\"/[^0-9]/g\\";\\"\\"))}}"]}}]}')

m6 = {
    "id": 6,
    "module": "http:MakeRequest",
    "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "filter": {
        "name": "Solo fuente-facebook",
        "conditions": [[{"a": "{{4.bodies}}", "o": "text:contain", "b": FB_MARK}]],
    },
    "mapper": {
        "url": "https://graph.facebook.com/v21.0/%s/events?access_token=%s" % (META_PIXEL, META_TOKEN),
        "method": "post",
        "headers": [{"name": "Content-Type", "value": "application/json"}],
        "contentType": "json",
        "inputMethod": "jsonString",
        "jsonStringBodyContent": json_body,
        "timeout": 30,
        "shareCookies": False,
        "parseResponse": True,
        "allowRedirects": True,
        "stopOnHttpError": False,
        "requestCompressedContent": True,
    },
    "metadata": {"designer": {"x": 1500, "y": 0}},
}
flow.append(m6)

# 4) limpiar blueprint para PATCH (sin interface/scheduling embebidos)
bp.pop("interface", None)
bp.pop("scheduling", None)

if DRY:
    safe = copy.deepcopy(m6)
    safe["mapper"]["url"] = "https://graph.facebook.com/v21.0/%s/events?access_token=***" % META_PIXEL
    print(json.dumps(safe, ensure_ascii=False, indent=2)); sys.exit(0)

# 5) PATCH
body = {"blueprint": json.dumps(bp, ensure_ascii=False), "name": bp.get("name")}
res = api("PATCH", BASE, body)
rs = res.get("scenario", res)
print("PATCHED -> isinvalid:", rs.get("isinvalid"), "| isActive:", rs.get("isActive"))

# 6) verify-after-write (blueprint es eventually-consistent)
cbp = get_blueprint()
ids = [m.get("id") for m in cbp["flow"]]
has_meta = any(isinstance(m.get("mapper", {}).get("url"), str)
               and "graph.facebook.com" in m["mapper"]["url"] for m in cbp["flow"])
meta = api("GET", BASE)
ms = meta.get("scenario", meta)
print("VERIFY -> modulos:", ids, "| meta module presente:", has_meta,
      "| isinvalid:", ms.get("isinvalid"), "| isActive:", ms.get("isActive"))
