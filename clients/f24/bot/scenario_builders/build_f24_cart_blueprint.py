#!/usr/bin/env python3
"""Build del scenario Make 'F24 Carrito Abandonado (polling)'.

Patrón: Make = cerebro (polling + dedup + tag), GHL relay = brazo (manda el template).
NO usa webhooks de Shopify (evita el storm de checkouts/update que duplica 3-4x en HC).

Flujo (cron cada 30 min):
  1. OAuth client_credentials → token Shopify.
  2. GraphQL abandonedCheckouts (recoveryUrl, customer phone/name, createdAt, completedAt).
  3. Iterator por carrito.
  4. SetVariables: phone_norm (+521…), eligible (tiene phone · edad 60min–48h · no completado).
  5. GetRecord(dedup) key=checkoutId  (onerror Resume → not-found = vacío).
  6. [filter eligible + no enviado] GHL upsert contacto (phone, firstName, custom field URL).
  7. [filter no bot-pausado] GHL add tag f24-send-cart  → dispara el relay.
  8. AddRecord(dedup) key=checkoutId status=sent  → no re-enviar.

El relay GHL ("tag f24-send-cart → Send WhatsApp Template → quita el tag") lo arma Gibran en UI.

PENDIENTE antes de deploy:
  - CUSTOM_FIELD_ID: el id del custom field GHL `carrito_abandonado_url` (Gibran lo crea en UI;
    lo resuelvo con list_custom_fields y lo pego aquí).
  - DATASTORE_ID: datastore Make nuevo para dedup (lo creo con Make MCP data-stores_create).

Run:  /usr/bin/python3 build_f24_cart_blueprint.py  → /tmp/f24_cart_bp.json
"""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
F24_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
ENV_PATH = os.path.join(F24_ROOT, ".env")
OUTPUT_PATH = "/tmp/f24_cart_bp.json"

# ---- Parámetros (rellenar los PENDING antes de deploy) ----
SHOP = "0mtky1-q6.myshopify.com"
API_VERSION = "2024-10"
GHL_LOCATION_ID = "HNuSoIl2aCXP2DXEdMVZ"
CART_TAG = "f24-send-cart"
CUSTOM_FIELD_ID = "wjZ1NZwuUowHwgz29P8F"   # custom field carrito_abandonado_url (TEXT, F24)
DATASTORE_ID = 109291                       # datastore dedup (Make) "F24 Carrito Abandonado — Dedup"

AGE_MIN_MINUTES = 60      # mandar a partir de 1h tras abandonar
AGE_MAX_MINUTES = 2880    # cap: no mandar a carritos > 48h
INTERVAL_SECONDS = 1800   # cron cada 30 min


def _read_env(path, key, default=""):
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return default


GHL_TOKEN = _read_env(ENV_PATH, "GHL_API_KEY", "__PENDING_GHL__")
SHOP_CID = _read_env(ENV_PATH, "SHOPIFY_CLIENT_ID", "__PENDING_CID__")
SHOP_CSEC = _read_env(ENV_PATH, "SHOPIFY_CLIENT_SECRET", "__PENDING_CSEC__")

GQL = ("query{ abandonedCheckouts(first:50, sortKey:CREATED_AT, reverse:true){ edges{ node{ "
       "id createdAt completedAt abandonedCheckoutUrl "
       "customer{ firstName phone } billingAddress{ phone } } } } }")

# ---- 1: OAuth token Shopify ----
m_oauth = {
    "id": 1, "module": "http:MakeRequest", "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "mapper": {
        "url": f"https://{SHOP}/admin/oauth/access_token", "method": "post",
        "headers": [{"name": "Content-Type", "value": "application/json"}],
        "contentType": "application/json", "inputMethod": "raw",
        "data": json.dumps({"client_id": SHOP_CID, "client_secret": SHOP_CSEC,
                            "grant_type": "client_credentials"}),
        "timeout": 30, "parseResponse": True, "stopOnHttpError": True,
        "shareCookies": False, "allowRedirects": True, "requestCompressedContent": False,
    },
    "metadata": {"designer": {"x": 0, "y": 0}},
}

# ---- 2: GraphQL abandonedCheckouts ----
m_gql = {
    "id": 2, "module": "http:MakeRequest", "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "mapper": {
        "url": f"https://{SHOP}/admin/api/{API_VERSION}/graphql.json", "method": "post",
        "headers": [
            {"name": "X-Shopify-Access-Token", "value": "{{1.access_token}}"},
            {"name": "Content-Type", "value": "application/json"},
        ],
        "contentType": "application/json", "inputMethod": "raw",
        "data": json.dumps({"query": GQL}),
        "timeout": 60, "parseResponse": True, "stopOnHttpError": True,
        "shareCookies": False, "allowRedirects": True, "requestCompressedContent": True,
    },
    "metadata": {"designer": {"x": 300, "y": 0}},
}

# ---- 3: Iterator por carrito ----
m_iter = {
    "id": 3, "module": "builtin:BasicFeeder", "version": 1,
    "mapper": {"array": "{{2.data.abandonedCheckouts.edges}}"},
    "metadata": {"designer": {"x": 600, "y": 0}},
}

# ---- 4: SetVariables — phone_norm + eligible ----
# phone crudo: customer.phone || billingAddress.phone. digits: solo números. last10 + +521.
phone_raw = "{{ifempty(3.node.customer.phone; 3.node.billingAddress.phone)}}"
m_vars = {
    "id": 4, "module": "util:SetVariables", "version": 1, "parameters": {},
    "mapper": {"variables": [
        {"name": "phone_digits", "value": "{{replace(" + phone_raw[2:-2] + "; \"/[^0-9]/g\"; \"\")}}"},
        {"name": "phone_norm", "value": (
            "{{\"+521\" + substring(replace(" + phone_raw[2:-2] + "; \"/[^0-9]/g\"; \"\"); "
            "max(0; length(replace(" + phone_raw[2:-2] + "; \"/[^0-9]/g\"; \"\")) - 10))}}")},
        {"name": "eligible", "value": (
            "{{if((ifempty(3.node.customer.phone; ifempty(3.node.billingAddress.phone; \"\")) != \"\") "
            "&& (ifempty(3.node.completedAt; \"\") = \"\") "
            "&& (parseDate(3.node.createdAt) <= addMinutes(now; -" + str(AGE_MIN_MINUTES) + ")) "
            "&& (parseDate(3.node.createdAt) >= addMinutes(now; -" + str(AGE_MAX_MINUTES) + ")); "
            "\"true\"; \"false\")}}")},
    ], "scope": "roundtrip"},
    "metadata": {"designer": {"x": 900, "y": 0}, "restore": {}},
}

# ---- 5: GetRecord dedup (onerror Resume → not found = vacío) ----
m_get = {
    "id": 5, "module": "datastore:GetRecord", "version": 1,
    "parameters": {"datastore": DATASTORE_ID},
    "mapper": {"key": "{{3.node.id}}"},
    "metadata": {"designer": {"x": 1200, "y": 0}},
    "filter": {"name": "elegible", "conditions": [[
        {"a": "{{4.eligible}}", "o": "text:equal", "b": "true"},
    ]]},
    "onerror": [{"id": 50, "module": "builtin:Resume", "version": 1,
                 "mapper": {"status": ""}, "metadata": {"designer": {"x": 1200, "y": 300}}}],
}

# ---- 6: GHL upsert contacto (phone + firstName + custom field URL) ----
m_upsert = {
    "id": 6, "module": "http:MakeRequest", "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "mapper": {
        "url": "https://services.leadconnectorhq.com/contacts/upsert", "method": "post",
        "headers": [
            {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
            {"name": "Version", "value": "2021-07-28"},
            {"name": "Content-Type", "value": "application/json"},
            {"name": "Accept", "value": "application/json"},
        ],
        "contentType": "application/json", "inputMethod": "raw",
        "data": ("{\"locationId\":\"" + GHL_LOCATION_ID + "\","
                 "\"phone\":\"{{4.phone_norm}}\","
                 "\"firstName\":\"{{ifempty(3.node.customer.firstName; \"\")}}\","
                 "\"customFields\":[{\"id\":\"" + CUSTOM_FIELD_ID + "\","
                 "\"value\":\"{{3.node.abandonedCheckoutUrl}}\"}]}"),
        "timeout": 30, "parseResponse": True, "stopOnHttpError": False,
        "shareCookies": False, "allowRedirects": True, "requestCompressedContent": True,
    },
    "metadata": {"designer": {"x": 1500, "y": 0}},
    "filter": {"name": "no enviado aun", "conditions": [[
        {"a": "{{ifempty(5.status; \"\")}}", "o": "text:notequal", "b": "sent"},
    ]]},
}

# ---- 7: GHL add tag f24-send-cart (filter: no bot-pausado / no requiere-humano) ----
m_tag = {
    "id": 7, "module": "http:MakeRequest", "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "mapper": {
        "url": "https://services.leadconnectorhq.com/contacts/{{6.data.contact.id}}/tags",
        "method": "post",
        "headers": [
            {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
            {"name": "Version", "value": "2021-07-28"},
            {"name": "Content-Type", "value": "application/json"},
            {"name": "Accept", "value": "application/json"},
        ],
        "contentType": "application/json", "inputMethod": "raw",
        "data": json.dumps({"tags": [CART_TAG]}),
        "timeout": 30, "parseResponse": True, "stopOnHttpError": False,
        "shareCookies": False, "allowRedirects": True, "requestCompressedContent": True,
    },
    "metadata": {"designer": {"x": 1800, "y": 0}},
    "filter": {"name": "no pausado", "conditions": [[
        {"a": "{{join(6.data.contact.tags; \"|\")}}", "o": "text:notcontain", "b": "bot-pausado"},
        {"a": "{{join(6.data.contact.tags; \"|\")}}", "o": "text:notcontain", "b": "requiere-humano"},
    ]]},
}

# ---- 8: AddRecord dedup (marca enviado) ----
m_add = {
    "id": 8, "module": "datastore:AddRecord", "version": 1,
    "parameters": {"datastore": DATASTORE_ID},
    "mapper": {"key": "{{3.node.id}}", "overwrite": True, "data": {
        "status": "sent", "phone": "{{4.phone_norm}}", "sent_at": "{{now}}",
    }},
    "metadata": {"designer": {"x": 2100, "y": 0}},
}

blueprint = {
    "name": "F24 Carrito Abandonado (polling)",
    "flow": [m_oauth, m_gql, m_iter, m_vars, m_get, m_upsert, m_tag, m_add],
    "metadata": {
        "instant": False, "version": 1,
        "scenario": {"roundtrips": 1, "maxErrors": 100, "autoCommit": True,
                     "autoCommitTriggerLast": True, "sequential": False, "confidential": False,
                     "dataloss": False, "dlq": False, "freshVariables": False},
        "designer": {"orphans": []},
    },
    "scheduling": {"type": "indefinitely", "interval": INTERVAL_SECONDS},
    "interface": {"input": [], "output": []},
}

if __name__ == "__main__":
    pend = []
    if CUSTOM_FIELD_ID.startswith("__PENDING"):
        pend.append("CUSTOM_FIELD_ID")
    if DATASTORE_ID == 0:
        pend.append("DATASTORE_ID")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Output: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)  modulos: {len(blueprint['flow'])}")
    print(f"GHL token: {'OK' if not GHL_TOKEN.startswith('__PENDING') else 'PENDIENTE'} | "
          f"Shopify creds: {'OK' if not SHOP_CID.startswith('__PENDING') else 'PENDIENTE'}")
    print(f"Cron: cada {INTERVAL_SECONDS//60} min | edad {AGE_MIN_MINUTES}-{AGE_MAX_MINUTES} min")
    if pend:
        print("PENDIENTE antes de deploy:", ", ".join(pend))
