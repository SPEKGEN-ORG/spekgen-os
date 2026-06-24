#!/usr/bin/env python3
"""Agrega el upload a Google Ads (Data Manager API) a la RUTA B del Router del tagger 5405187.

Ruta B ya: extrae gclid -> escribe wa_gclid (modulo 8). Le agregamos en secuencia:
  modulo 9 = OAuth refresh -> access_token (scope datamanager)
  modulo 10 = POST datamanager.googleapis.com/v1/events:ingest (sube la conversion offline)
Solo corre para leads google-con-ref (el filtro ref: de la ruta ya gatea). stopOnHttpError=False.
eventTimestamp = now-5min UTC (evita rechazo por 'futuro'). transactionId = contact_id (dedup).

Creds Google se leen del .env (autorizado por Gibran; mismo Make team 354061). Idempotente.

  PYTHONUTF8=1 py add_google_upload_to_route.py            # aplica
  PYTHONUTF8=1 py add_google_upload_to_route.py --dry-run
"""
import io, sys, json, copy, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPKENV = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
F24ENV = HERE.parents[1] / ".env"
SCENARIO = 5405187
BASE = "https://us2.make.com/api/v2/scenarios/%d" % SCENARIO
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
CONV_ACTION = "7650064999"
DRY = "--dry-run" in sys.argv


def envget(p, key):
    for l in io.open(p, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith(key + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'").split("  #")[0].strip()
    return ""


MAKE_TOKEN = envget(SPKENV, "MAKE_API_TOKEN")
CID = envget(F24ENV, "GOOGLE_ADS_CLIENT_ID")
CSEC = envget(F24ENV, "GOOGLE_ADS_CLIENT_SECRET")
RTOK = envget(F24ENV, "GOOGLE_ADS_REFRESH_TOKEN")
CUSTID = envget(F24ENV, "GOOGLE_ADS_CUSTOMER_ID").replace("-", "")
LOGINCID = envget(F24ENV, "GOOGLE_ADS_LOGIN_CUSTOMER_ID").replace("-", "")
if not all([MAKE_TOKEN, CID, CSEC, RTOK, CUSTID, LOGINCID]):
    sys.exit("Faltan creds en .env")


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
router = next((m for m in bp["flow"] if m.get("module") == "builtin:BasicRouter"), None)
if not router:
    sys.exit("No hay Router en el tagger (corre restructure_tagger_router.py primero).")

# ruta B = la que tiene el modulo de gclid (wa_gclid)
routeB = None
for r in router["routes"]:
    if any("wa_gclid" in json.dumps(m.get("mapper", {})) or "FpgydkpdxKsQ7nVPkORo" in json.dumps(m.get("mapper", {}))
           for m in r["flow"]):
        routeB = r; break
if not routeB:
    sys.exit("No encontre la ruta B (gclid).")

if any("datamanager.googleapis.com" in json.dumps(m.get("mapper", {})) for m in routeB["flow"]):
    print("Upload a Google ya existe en la ruta B -> nada que hacer."); sys.exit(0)

# OAuth refresh
m_oauth = {"id": 9, "module": "http:MakeRequest", "version": 4,
           "parameters": {"authenticationType": "noAuth"},
           "mapper": {"url": "https://oauth2.googleapis.com/token", "method": "post",
                      "contentType": "urlEncoded",
                      "urlEncodedBodyContent": [
                          {"name": "client_id", "value": CID},
                          {"name": "client_secret", "value": CSEC},
                          {"name": "refresh_token", "value": RTOK},
                          {"name": "grant_type", "value": "refresh_token"}],
                      "timeout": 30, "shareCookies": False, "parseResponse": True,
                      "allowRedirects": True, "stopOnHttpError": False,
                      "requestCompressedContent": True},
           "metadata": {"designer": {"x": 1800, "y": 150}}}

gclid_expr = '{{replace(4.bodies; "/^[\\s\\S]*?ref:([A-Za-z0-9_-]+)[\\s\\S]*$/"; "$1")}}'
ts_expr = '{{formatDate(addMinutes(now; -5); "YYYY-MM-DDTHH:mm:ss"; "UTC")}}+00:00'
ingest_body = (
    '{"destinations":[{"operatingAccount":{"accountType":"GOOGLE_ADS","accountId":"' + CUSTID + '"},'
    '"loginAccount":{"accountType":"GOOGLE_ADS","accountId":"' + LOGINCID + '"},'
    '"productDestinationId":"' + CONV_ACTION + '"}],'
    '"events":[{"adIdentifiers":{"gclid":"' + gclid_expr + '"},'
    '"transactionId":"{{1.contact_id}}","eventTimestamp":"' + ts_expr + '",'
    '"conversionValue":1,"currency":"MXN","eventSource":"WEB"}]}'
)
m_ingest = {"id": 10, "module": "http:MakeRequest", "version": 4,
            "parameters": {"authenticationType": "noAuth"},
            "mapper": {"url": "https://datamanager.googleapis.com/v1/events:ingest", "method": "post",
                       "headers": [{"name": "Authorization", "value": "Bearer {{9.access_token}}"},
                                   {"name": "Content-Type", "value": "application/json"}],
                       "contentType": "json", "inputMethod": "jsonString",
                       "jsonStringBodyContent": ingest_body,
                       "timeout": 30, "shareCookies": False, "parseResponse": True,
                       "allowRedirects": True, "stopOnHttpError": False,
                       "requestCompressedContent": True},
            "metadata": {"designer": {"x": 2100, "y": 150}}}

routeB["flow"] += [m_oauth, m_ingest]
bp.pop("interface", None); bp.pop("scheduling", None)

if DRY:
    safe = copy.deepcopy(m_ingest)
    print("Ruta B ahora:", [m.get("id") for m in routeB["flow"]])
    print(json.dumps(safe, ensure_ascii=False, indent=2)[:1200]); sys.exit(0)

res = api("PATCH", BASE, {"blueprint": json.dumps(bp, ensure_ascii=False), "name": bp.get("name")})
rs = res.get("scenario", res)
print("PATCHED -> isinvalid:", rs.get("isinvalid"), "| isActive:", rs.get("isActive"))
cbp = get_blueprint()
rt = next((m for m in cbp["flow"] if m.get("module") == "builtin:BasicRouter"), {})
routes = [[mm.get("id") for mm in r.get("flow", [])] for r in rt.get("routes", [])]
has_dm = any("datamanager.googleapis.com" in json.dumps(m.get("mapper", {}))
             for r in rt.get("routes", []) for m in r.get("flow", []))
meta = api("GET", BASE); ms = meta.get("scenario", meta)
print("VERIFY -> router routes:", routes, "| datamanager presente:", has_dm,
      "| isinvalid:", ms.get("isinvalid"), "| isActive:", ms.get("isActive"))
