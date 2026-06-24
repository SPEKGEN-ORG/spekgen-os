#!/usr/bin/env python3
"""Crea el scenario AISLADO 'F24 Google Conversion Upload' que sube la conversion offline
a Google Ads (conversion action Conversacion_WhatsApp 7650064999) usando el gclid del lead.

Aislado a proposito: toda la complejidad/secretos de Google Ads viven aqui, NO en el tagger.
El tagger solo le dispara un webhook con {gclid, contact_id}.

Flujo: 1 webhook(recibe gclid) -> 2 OAuth refresh->access_token -> 3 uploadClickConversions.
partialFailure=true: un gclid invalido NO tumba el scenario (devuelve error parcial, HTTP 200).

Secrets Google se leen del .env de F24 y se inyectan aqui (NUNCA entran al chat). Mismo
patron/limite de confianza que el token GHL/Meta ya guardados en Make (team 354061).

  PYTHONUTF8=1 py build_google_upload_scenario.py
"""
import io, sys, json, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPKENV = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
F24ENV = HERE.parents[1] / ".env"
TEAM = 354061
APIV = "v18"
CONV_ACTION = "7650064999"
BASE = "https://us2.make.com/api/v2"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def envget(p, key):
    for l in io.open(p, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith(key + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'").split("  #")[0].strip()
    return ""


MAKE_TOKEN = envget(SPKENV, "MAKE_API_TOKEN")
CID = envget(F24ENV, "GOOGLE_ADS_CLIENT_ID")
CSECRET = envget(F24ENV, "GOOGLE_ADS_CLIENT_SECRET")
RTOKEN = envget(F24ENV, "GOOGLE_ADS_REFRESH_TOKEN")
DEVTOK = envget(F24ENV, "GOOGLE_ADS_DEVELOPER_TOKEN")
LOGINCID = envget(F24ENV, "GOOGLE_ADS_LOGIN_CUSTOMER_ID").replace("-", "")
CUSTID = envget(F24ENV, "GOOGLE_ADS_CUSTOMER_ID").replace("-", "")
missing = [k for k, v in {"MAKE_API_TOKEN": MAKE_TOKEN, "CLIENT_ID": CID, "CLIENT_SECRET": CSECRET,
                          "REFRESH_TOKEN": RTOKEN, "DEVELOPER_TOKEN": DEVTOK,
                          "LOGIN_CUSTOMER_ID": LOGINCID, "CUSTOMER_ID": CUSTID}.items() if not v]
if missing:
    sys.exit("Faltan en .env: " + ", ".join(missing))


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Authorization", "Token " + MAKE_TOKEN)
    r.add_header("Content-Type", "application/json")
    r.add_header("User-Agent", UA)
    try:
        return json.loads(urllib.request.urlopen(r, timeout=60).read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:600]); sys.exit(1)


# 1) hook (reusa el existente por nombre para no acumular orphans)
HOOK_NAME = "F24 Google Upload Hook"
existing = api("GET", "/hooks?teamId=%d" % TEAM)
hooks = existing.get("hooks", existing) if isinstance(existing, dict) else existing
hook = next((h for h in (hooks or []) if h.get("name") == HOOK_NAME), None)
if hook is None:
    hk = api("POST", "/hooks", {"name": HOOK_NAME, "teamId": TEAM, "typeName": "gateway-webhook"})
    hook = hk.get("hook", hk)
HOOK_ID = hook.get("id")
HOOK_URL = hook.get("url") or ("https://hook.us2.make.com/" + str(hook.get("udid", "")))
print("Hook:", HOOK_ID, "|", HOOK_URL)

# 2) modulos
m1 = {"id": 1, "module": "gateway:CustomWebHook", "version": 1,
      "parameters": {"hook": HOOK_ID}, "mapper": {}, "metadata": {"designer": {"x": 0, "y": 0}}}

m2 = {"id": 2, "module": "http:MakeRequest", "version": 4,
      "parameters": {"authenticationType": "noAuth"},
      "mapper": {"url": "https://oauth2.googleapis.com/token", "method": "post",
                 "contentType": "urlEncoded",
                 "urlEncodedBodyContent": [
                     {"name": "client_id", "value": CID},
                     {"name": "client_secret", "value": CSECRET},
                     {"name": "refresh_token", "value": RTOKEN},
                     {"name": "grant_type", "value": "refresh_token"}],
                 "timeout": 30, "shareCookies": False, "parseResponse": True,
                 "allowRedirects": True, "stopOnHttpError": False,
                 "requestCompressedContent": True},
      "metadata": {"designer": {"x": 300, "y": 0}}}

upload_body = ('{"conversions":[{"gclid":"{{1.gclid}}",'
               '"conversionAction":"customers/' + CUSTID + '/conversionActions/' + CONV_ACTION + '",'
               '"conversionDateTime":"{{formatDate(now; "YYYY-MM-DD HH:mm:ss"; "UTC")}}+00:00",'
               '"conversionValue":1,"currencyCode":"MXN"}],"partialFailure":true}')

m3 = {"id": 3, "module": "http:MakeRequest", "version": 4,
      "parameters": {"authenticationType": "noAuth"},
      "filter": {"name": "Solo si hay gclid",
                 "conditions": [[{"a": "{{1.gclid}}", "o": "exist"}]]},
      "mapper": {"url": "https://googleads.googleapis.com/" + APIV + "/customers/" + CUSTID
                        + ":uploadClickConversions",
                 "method": "post",
                 "headers": [
                     {"name": "Authorization", "value": "Bearer {{2.access_token}}"},
                     {"name": "developer-token", "value": DEVTOK},
                     {"name": "login-customer-id", "value": LOGINCID},
                     {"name": "Content-Type", "value": "application/json"}],
                 "contentType": "json", "inputMethod": "jsonString",
                 "jsonStringBodyContent": upload_body,
                 "timeout": 30, "shareCookies": False, "parseResponse": True,
                 "allowRedirects": True, "stopOnHttpError": False,
                 "requestCompressedContent": True},
      "metadata": {"designer": {"x": 600, "y": 0}}}

blueprint = {"name": "F24 Google Conversion Upload", "flow": [m1, m2, m3],
             "metadata": {"instant": True, "version": 1, "designer": {"orphans": []},
                          "scenario": {"roundtrips": 1, "maxErrors": 3, "autoCommit": True,
                                       "autoCommitTriggerLast": True, "sequential": False,
                                       "confidential": False, "dataloss": False, "dlq": False,
                                       "freshVariables": False}}}

# 3) crear scenario
res = api("POST", "/scenarios", {"teamId": TEAM,
                                 "blueprint": json.dumps(blueprint, ensure_ascii=False),
                                 "scheduling": json.dumps({"type": "immediately"})})
sc = res.get("scenario", res)
print("SCENARIO creado -> id:", sc.get("id"), "| isinvalid:", sc.get("isinvalid"),
      "| isActive:", sc.get("isActive"))
print("HOOK_URL_PARA_TAGGER:", HOOK_URL)
