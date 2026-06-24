#!/usr/bin/env python3
"""Crea un escenario Make DEDICADO (aislado del bot) que etiqueta la fuente en tiempo real.
Flujo: webhook (GHL dispara en cada inbound) -> GET conversacion -> GET mensajes ->
detecta el marcador invisible -> agrega tag fuente-* al contacto. Inmune a ediciones del bot.

Reusa shapes de modulos http:MakeRequest del blueprint LIVE del bot (auth GHL valida).
Detecta con contains() + chars literales (independiente del flavor de regex).
"""
import io, os, json, copy, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE / "_BLUEPRINTS" / "f24_bot_LIVE_current_2026-06-16.json"
F24ENV = HERE.parents[1] / ".env"
SPKENV = HERE.parents[2] / "SPK - SPEKGEN AGENCY" / ".env"
HOOK = 2461980
TEAM = 354061


def envget(p, key):
    for l in io.open(p, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith(key + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'").split("  #")[0].strip()
    return ""


LOC = envget(F24ENV, "GHL_LOCATION_ID")
MAKE_TOKEN = envget(SPKENV, "MAKE_API_TOKEN")
META_TOKEN = envget(F24ENV, "META_TOKEN")
META_PIXEL = envget(F24ENV, "META_PIXEL_ID")
TEST_EVENT_CODE = os.environ.get("META_TEST_EVENT_CODE", "")  # set for safe Test-Events validation

bp = json.load(io.open(LIVE, encoding="utf-8"))
def find(flow, mid):
    for m in flow:
        if m.get("id") == mid:
            return m
        for r in (m.get("routes") or []):
            x = find(r.get("flow", []), mid)
            if x:
                return x
    return None
tagtpl = find(bp["flow"], 46)   # POST /tags template (trae headers con token GHL)
gettpl = find(bp["flow"], 3)    # GET contact template (http GET valido)

SENT = chr(0x2063); G = chr(0x200B); FB = chr(0x200C); OO = chr(0x200D); DD = chr(0x2060)

read_headers = copy.deepcopy(tagtpl["mapper"]["headers"])   # Version 2021-07-28 (igual que el bot)

# --- Modulos ---
m1 = {"id": 1, "module": "gateway:CustomWebHook", "version": 1,
      "parameters": {"hook": HOOK}, "mapper": {}, "metadata": {"designer": {"x": 0, "y": 0}}}

m2 = copy.deepcopy(gettpl); m2["id"] = 2; m2.pop("filter", None); m2.pop("onerror", None)
m2["metadata"] = {"designer": {"x": 300, "y": 0}}
m2["mapper"] = copy.deepcopy(gettpl["mapper"])
m2["mapper"]["url"] = ("https://services.leadconnectorhq.com/conversations/search?locationId="
                       + LOC + "&contactId={{1.contact_id}}")
m2["mapper"]["method"] = "get"; m2["mapper"]["headers"] = read_headers; m2["mapper"]["parseResponse"] = True

m3 = copy.deepcopy(gettpl); m3["id"] = 3; m3.pop("filter", None); m3.pop("onerror", None)
m3["metadata"] = {"designer": {"x": 600, "y": 0}}
m3["mapper"] = copy.deepcopy(gettpl["mapper"])
m3["mapper"]["url"] = ("https://services.leadconnectorhq.com/conversations/"
                       "{{first(map(ifempty(2.data.conversations; 2.conversations); \"id\"))}}/messages?limit=10")
m3["mapper"]["method"] = "get"; m3["mapper"]["headers"] = read_headers; m3["mapper"]["parseResponse"] = True

m4 = {"id": 4, "module": "util:SetVariables", "version": 1,
      "mapper": {"scope": "roundtrip", "variables": [
          {"name": "bodies", "value": "{{join(map(ifempty(3.data.messages.messages; ifempty(3.messages.messages; emptyarray)); \"body\"); \" || \")}}"}]},
      "metadata": {"designer": {"x": 900, "y": 0}}}

src = ('{{if(contains(4.bodies; "' + G + '"); "fuente-google"; '
       'if(contains(4.bodies; "' + FB + '"); "fuente-facebook"; '
       'if(contains(4.bodies; "' + OO + '"); "fuente-organico"; '
       'if(contains(4.bodies; "' + DD + '"); "fuente-directo"; ""))))}}')

m5 = copy.deepcopy(tagtpl); m5["id"] = 5; m5["metadata"] = {"designer": {"x": 1200, "y": 0}}
m5["mapper"] = copy.deepcopy(tagtpl["mapper"])
m5["mapper"]["url"] = "https://services.leadconnectorhq.com/contacts/{{1.contact_id}}/tags"
m5["mapper"]["dataStructureBodyContent"] = {"tags": [src]}
m5["filter"] = {"name": "Trae marcador de fuente",
                "conditions": [[{"a": "{{4.bodies}}", "o": "text:contain", "b": SENT}]]}
m5.pop("onerror", None)

# Module 6: Meta CAPI "Lead" event — SOLO fuente-facebook, match por telefono hasheado (SHA-256).
meta_data = ('{"data":[{"event_name":"Lead","event_time":{{formatDate(now; "X")}},'
             '"action_source":"chat","user_data":{"ph":["{{sha256(replace(first(map(2.data.conversations; "phone")); "/[^0-9]/g"; ""))}}"]}}]'
             + (',"test_event_code":"' + TEST_EVENT_CODE + '"' if TEST_EVENT_CODE else '') + '}')
m6 = copy.deepcopy(tagtpl); m6["id"] = 6; m6["metadata"] = {"designer": {"x": 1500, "y": 0}}
m6["mapper"] = copy.deepcopy(tagtpl["mapper"])
m6["mapper"]["url"] = "https://graph.facebook.com/v21.0/" + META_PIXEL + "/events?access_token=" + META_TOKEN
m6["mapper"]["headers"] = [{"name": "Content-Type", "value": "application/json"}]
m6["mapper"].pop("bodyDataStructure", None); m6["mapper"].pop("dataStructureBodyContent", None)
m6["mapper"]["inputMethod"] = "raw"; m6["mapper"]["bodyType"] = "raw"
m6["mapper"]["contentType"] = "application/json"; m6["mapper"]["data"] = meta_data
m6["mapper"]["stopOnHttpError"] = False
m6["filter"] = {"name": "Solo fuente-facebook", "conditions": [[{"a": "{{4.bodies}}", "o": "text:contain", "b": FB}]]}
m6.pop("onerror", None)

blueprint = {"name": "F24 Source Tagger (Google vs Facebook)",
             "flow": [m1, m2, m3, m4, m5],  # m6 (Meta CAPI) removed — fired via Python instead (raw-body validation issue)
             "metadata": {"instant": True, "version": 1,
                          "scenario": {"roundtrips": 1, "maxErrors": 3, "autoCommit": True,
                                       "autoCommitTriggerLast": True, "sequential": False,
                                       "confidential": False, "dataloss": False, "dlq": False,
                                       "freshVariables": False},
                          "designer": {"orphans": []}}}

body = json.dumps({"blueprint": json.dumps(blueprint, ensure_ascii=False),
                   "name": blueprint["name"]})
req = urllib.request.Request("https://us2.make.com/api/v2/scenarios/5405187",
                             data=body.encode(), method="PATCH")
req.add_header("Authorization", "Token " + MAKE_TOKEN)
req.add_header("Content-Type", "application/json")
req.add_header("User-Agent", "Mozilla/5.0")
try:
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    s = r.get("scenario", r)
    print("PATCHED scenario id:", s.get("id"), "| isinvalid:", s.get("isinvalid"))
except urllib.error.HTTPError as e:
    print("PATCH ERROR", e.code, e.read().decode()[:700])
