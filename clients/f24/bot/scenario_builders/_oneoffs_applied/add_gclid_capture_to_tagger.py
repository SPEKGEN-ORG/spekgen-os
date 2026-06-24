#!/usr/bin/env python3
"""Agrega QUIRURGICAMENTE el modulo de captura de gclid al tagger LIVE 5405187.

Para leads fuente-google cuyo mensaje trae " ref:<gclid>" (lo estampa f24-attribution.js),
extrae el gclid y lo escribe al custom field contact.wa_gclid (id FpgydkpdxKsQ7nVPkORo).
Asi el gclid queda en GHL para luego subir la conversion offline a Google Ads.

- GET blueprint actual (preserva modulos existentes).
- Reusa el token GHL de un modulo existente (NO entra al contexto del chat).
- Filtro: el body trae "ref:" (solo google estampa ref:). Extrae con replace+regex ($1).
- stopOnHttpError=False -> un fallo HTTP no acumula errores hacia maxErrors.
- Idempotente (no duplica).

  PYTHONUTF8=1 py add_gclid_capture_to_tagger.py            # aplica
  PYTHONUTF8=1 py add_gclid_capture_to_tagger.py --dry-run  # muestra, no PATCHea
"""
import io, sys, json, copy, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPKENV = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
SCENARIO = 5405187
BASE = "https://us2.make.com/api/v2/scenarios/%d" % SCENARIO
WA_GCLID_FIELD = "FpgydkpdxKsQ7nVPkORo"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DRY = "--dry-run" in sys.argv


def envget(p, key):
    for l in io.open(p, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith(key + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'").split("  #")[0].strip()
    return ""


MAKE_TOKEN = envget(SPKENV, "MAKE_API_TOKEN")
if not MAKE_TOKEN:
    sys.exit("Falta MAKE_API_TOKEN en SPK .env")


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
print("Modulos actuales:", [m.get("id") for m in flow])

# idempotente: no duplicar
if any(WA_GCLID_FIELD in json.dumps(m.get("mapper", {})) for m in flow):
    print("Captura de gclid ya existe -> nada que hacer."); sys.exit(0)

# reusar headers GHL (con token) de un modulo http existente que apunte a leadconnector
ghl_headers = None
for m in flow:
    mp = m.get("mapper", {})
    if isinstance(mp.get("url"), str) and "leadconnectorhq.com" in mp["url"] and mp.get("headers"):
        ghl_headers = copy.deepcopy(mp["headers"]); break
if not ghl_headers:
    sys.exit("No encontre headers GHL en el blueprint para reusar el token.")

new_id = max(m.get("id", 0) for m in flow) + 1

# value = extrae el primer "ref:<gclid>" del body via replace+regex (backreference $1).
# Las comillas dentro de {{...}} las consume el evaluador de Make; el body final queda JSON valido.
json_body = ('{"customFields":[{"id":"' + WA_GCLID_FIELD + '","value":'
             '"{{replace(4.bodies; "/^[\\s\\S]*?ref:([A-Za-z0-9_-]+)[\\s\\S]*$/"; "$1")}}"}]}')

m_new = {
    "id": new_id,
    "module": "http:MakeRequest",
    "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "filter": {
        "name": "Trae gclid (ref:)",
        "conditions": [[{"a": "{{4.bodies}}", "o": "text:contain", "b": "ref:"}]],
    },
    "mapper": {
        "url": "https://services.leadconnectorhq.com/contacts/{{1.contact_id}}",
        "method": "put",
        "headers": ghl_headers,
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
    "metadata": {"designer": {"x": 1800, "y": 0}},
}
flow.append(m_new)
bp.pop("interface", None)
bp.pop("scheduling", None)

if DRY:
    safe = copy.deepcopy(m_new)
    safe["mapper"]["headers"] = "[GHL headers reused]"
    print(json.dumps(safe, ensure_ascii=False, indent=2)); sys.exit(0)

res = api("PATCH", BASE, {"blueprint": json.dumps(bp, ensure_ascii=False), "name": bp.get("name")})
rs = res.get("scenario", res)
print("PATCHED -> isinvalid:", rs.get("isinvalid"), "| isActive:", rs.get("isActive"))

cbp = get_blueprint()
ids = [m.get("id") for m in cbp["flow"]]
has_gclid = any(WA_GCLID_FIELD in json.dumps(m.get("mapper", {})) for m in cbp["flow"])
meta = api("GET", BASE); ms = meta.get("scenario", meta)
print("VERIFY -> modulos:", ids, "| captura gclid presente:", has_gclid,
      "| isinvalid:", ms.get("isinvalid"), "| isActive:", ms.get("isActive"))
