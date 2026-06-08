#!/usr/bin/env python3
"""Build FERRE24 Bot blueprint — clon del HC Bot, adaptado a ferretería.

Arquitectura espejo de build_hc_bot_blueprint.py. El "cerebro" (ParseJSON anti-crash,
datastore memoria, polling auto-handoff 4h, router) es idéntico. Diferencias F24:

  1. Knowledge = catálogo Shopify live (188 SKUs) en CATALOG_INDEX.md + PRICING_POLICY.md,
     en vez de 4 informes técnicos de producto.
  2. CIERRE = action="create_order" → sub-router post-parse → Edge Function f24-process-order
     (draftOrderCreate + invoice/payment link) → manda el link por WhatsApp. (HC usa cart permalink.)
  3. IDs propios de F24 (location, webhook, datastore, data structures).

Estado de IDs (rellenar conforme se crean):
  - F24_LOCATION_ID: LISTO (HNuSoIl2aCXP2DXEdMVZ).
  - GHL_API_KEY (PIT): PENDIENTE de Pedro → F24/.env.
  - ANTHROPIC_API_KEY: → F24/.env (NO hardcodear).
  - Webhook / Datastore / Data structures: se crean en Make (Fase 2) y se pegan abajo.

Run:  /usr/bin/python3 build_f24_bot_blueprint.py
Out:  /tmp/f24_bot_bp_v1.json
"""
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_MD_PATH = os.path.join(SCRIPT_DIR, "F24_BOT_SYSTEM_PROMPT.md")
CANNED_MD_PATH = os.path.join(SCRIPT_DIR, "F24_BOT_CANNED_RESPONSES.md")
KB_DIR = os.path.join(SCRIPT_DIR, "F24_BOT_KNOWLEDGE")
CATALOG_MD_PATH = os.path.join(KB_DIR, "CATALOG_INDEX.md")
PRICING_MD_PATH = os.path.join(KB_DIR, "PRICING_POLICY.md")
F24_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # .../F24- FERRE24
ENV_PATH = os.path.join(F24_ROOT, ".env")
OUTPUT_PATH = "/tmp/f24_bot_bp_v1.json"

# ---------- Safeguard config ----------
WHITELIST_MODE = False  # ABIERTO A TODOS (2026-06-04). Freno manual = tag 'bot-pausado' por contacto.
WHITELIST_TAG = "bot test"
PAUSE_TAG = "bot-pausado"

# ---------- F24-specific IDs ----------
F24_LOCATION_ID = "HNuSoIl2aCXP2DXEdMVZ"  # LISTO — location GHL de Ferre24

# === Objetos Make creados 2026-06-01 (team 354061) ===
F24_WEBHOOK_ID = 2394767            # gateway:CustomWebHook — URL https://hook.us2.make.com/kuyq4cksp5cy6pg9ka4mh0uriorti9o6
F24_DATASTORE_ID = 104408           # datastore "F24 Bot Conversations" (memoria + bot_muted_until)
GHL_CONTACT_DATASTRUCTURE_ID = 334877      # reusado de GR (GHL Contact Response — genérico)
ANTHROPIC_BODY_DATASTRUCTURE_ID = 334561   # reusado (Anthropic Messages Request — genérico)
CLAUDE_RESPONSE_DATASTRUCTURE_ID = 388280  # NUEVO F24: Claude Response con objeto "order"
GHL_SEND_DATASTRUCTURE_ID = 342904         # reusado de HC (GHL Send Message Body — genérico)
# === Edge Function de órdenes (Fase 3) ===
F24_PROCESS_ORDER_URL = "https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/f24-process-order"
F24_PROCESS_ORDER_DATASTRUCTURE_ID = 389552  # body del POST (serializa line_items/customer como JSON real)

# Cuenta de transferencia de Ferre24 (MXN — la que se manda a clientes). Datos de Sergio 2026-06-02.
F24_TRANSFER_CLABE = "706180276752083666"  # Banco Arcus
F24_TRANSFER_HOLDER = "Sergio Jose Duarte Simon"

# ---------- Auto-handoff (polling pre-respuesta) ----------
HANDOFF_HOURS = 4

# ---------- GHL custom field IDs (location F24, creados por API 2026-06-02) ----------
F24_CF_NUMERO_PEDIDO = "ePF4Tr2ejgRp9z6WpJbq"
F24_CF_TRACKING_URL = "PitQVTnJJ0JreENWIBtz"
F24_CF_PURCHASE_COUNT = "9d8uBdAau2ziDBDhGQF6"
F24_CF_LAST_PRODUCTS = "KNHoFK29lQ94AN9vDIU2"
F24_CF_LAST_PURCHASE_VALUE = "RiQ6mqWUd2c3cuGHokNL"


# ---------- Credentials ----------
def _read_env(path: str, key: str, default=None):
    # En cloud (GitHub Actions) las llaves vienen como env vars (secrets); preferirlas.
    if os.environ.get(key):
        return os.environ[key]
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    if default is not None:
        return default
    raise ValueError(f"{key} not found in {path}")


# Tolerante en modo offline: si faltan (aún no hay PIT / key), usa placeholder para
# poder validar el armado del prompt. El deploy real exige las llaves reales.
GHL_TOKEN = _read_env(ENV_PATH, "GHL_API_KEY", default="__PENDING_PIT__")
ANTHROPIC_TOKEN = _read_env(ENV_PATH, "ANTHROPIC_API_KEY", default="__PENDING_ANTHROPIC_KEY__")

# Saludos simples (canned, sin Claude).
GREETING_REGEX = r"^\s*([Hh][Oo][Ll][Aa]+|[Hh][Oo][Ll][Ii]+|[Bb][Uu][Ee][Nn][Aa][Ss]|[Bb][Uu][Ee][Nn][Oo][Ss]|[Hh][Ii]+|[Hh][Ee][Yy]+|[Ss][Aa][Ll][Uu][Dd][Oo][Ss]|[Qq][Uu][Ee]\s?[Oo][Nn][Dd][Aa]|[Qq][Uu][Ee]\s?[Tt][Aa][Ll])[\s!.¡¿?]*$"
GREETING_MESSAGE = (
    "¡Qué tal! Bienvenido a Ferre24 🔧 Manejamos equipo para campo, jardín, obra y "
    "construcción: generadores, motobombas, motosierras, hidrolavadoras, compresores y más. "
    "Dime qué necesitas o para qué lo vas a usar y te asesoro."
)


def read_md_raw(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_prompt_from_md(md_path: str) -> str:
    content = read_md_raw(md_path)
    match = re.search(r"```\s*\n(.*?)\n```", content, re.DOTALL)
    if not match:
        raise ValueError(f"No fenced code block found in {md_path}")
    prompt = match.group(1).strip()
    if len(prompt) < 500:
        raise ValueError(f"Extracted prompt suspiciously short ({len(prompt)} chars)")
    return prompt


def build_full_prompt() -> str:
    parts = [extract_prompt_from_md(PROMPT_MD_PATH)]

    if os.path.exists(CANNED_MD_PATH):
        parts.append("\n\n" + "=" * 40)
        parts.append("== CANNED RESPONSES ==")
        parts.append("=" * 40)
        parts.append(read_md_raw(CANNED_MD_PATH))

    parts.append("\n\n" + "=" * 40)
    parts.append("== CATÁLOGO FERRE24 (precios, SKU/ID, links) ==")
    parts.append("=" * 40)
    parts.append("\nCotiza SOLO de esta lista. Para cerrar, usa el valor EXACTO de la columna")
    parts.append("'SKU / ID' como id de cada línea del objeto order (SKU, o 'id:NÚMERO' si no hay SKU).\n")
    parts.append(read_md_raw(CATALOG_MD_PATH))

    if os.path.exists(PRICING_MD_PATH):
        parts.append("\n\n" + "=" * 40)
        parts.append("== POLÍTICA DE PRECIOS / PROMOS / ENVÍO ==")
        parts.append("=" * 40)
        parts.append(read_md_raw(PRICING_MD_PATH))

    return "\n".join(parts)


SYSTEM_PROMPT = build_full_prompt()
print(f"[builder] Prompt length: {len(SYSTEM_PROMPT)} chars (~{len(SYSTEM_PROMPT)//4} tokens)")


# ---------- Filtros gate ----------
WHITELIST_CONDITION = {"a": "{{join(11.contact.tags; \"|\")}}", "o": "text:contain", "b": WHITELIST_TAG}
PAUSE_CONDITION_PRE_ROUTER = {"a": "{{join(11.contact.tags; \"|\")}}", "o": "text:notcontain", "b": PAUSE_TAG}


def build_gate_conditions(base_condition: dict) -> list:
    conditions = [base_condition]
    if WHITELIST_MODE:
        conditions.append(WHITELIST_CONDITION)
    return [conditions]


# ---------- Resume handlers (anti-outage, idéntico a HC v2.9.0) ----------
def resume_handler(handler_id: int, output_dict: dict, x: int, y: int) -> dict:
    return {
        "id": handler_id, "module": "builtin:Resume", "version": 1,
        "mapper": output_dict, "metadata": {"designer": {"x": x, "y": y}},
    }


PARSE_FALLBACK_BUNDLE = {
    "messages": ["Disculpa, tuve un problema técnico procesando tu mensaje. Un asesor del equipo te responde en breve."],
    "attachments": [], "action": "human_handoff", "order": None,
}
ANTHROPIC_FALLBACK_BUNDLE = {
    "data": {"content": [{"type": "text", "text": (
        "{\"messages\":[\"Disculpa, tuve un problema con mi cerebro AI. Un asesor del equipo te responde en breve.\"],"
        "\"attachments\":[],\"action\":\"human_handoff\",\"order\":null}"
    )}]}
}


# ---------- Module builders (clon HC; GHL endpoints idénticos, location F24) ----------
def ghl_get_contact_module(module_id, x, y):
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": "https://services.leadconnectorhq.com/contacts/{{1.contact_id}}",
            "method": "get",
            "headers": [
                {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
                {"name": "Version", "value": "2021-07-28"},
                {"name": "Accept", "value": "application/json"},
            ],
            "timeout": 30, "shareCookies": False, "parseResponse": False,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
    }


def parse_ghl_contact_module(module_id, x, y, source_module_id):
    src = str(source_module_id)
    fallback = '{"contact":{"firstName":"","lastName":"","tags":[],"customFields":[]}}'
    fb = fallback.replace('"', '\\"')
    safe = "{{if(substring(ifempty(" + src + ".data; \"\"); 0; 1) = \"{\"; " + src + ".data; \"" + fb + "\")}}"
    return {
        "id": module_id, "module": "json:ParseJSON", "version": 1,
        "parameters": {"type": GHL_CONTACT_DATASTRUCTURE_ID},
        "mapper": {"json": safe}, "metadata": {"designer": {"x": x, "y": y}},
    }


def customer_context_module(module_id, x, y):
    """firstName + email + (cuando existan los CF IDs) tracking/numero_pedido/purchase_count."""
    def cf(fid, default="\"\""):
        if not fid:
            return default
        return ("{{ifempty(get(map(11.contact.customFields; \"value\"; \"id\"; \""
                + fid + "\"); 1); " + default + ")}}")
    return {
        "id": module_id, "module": "util:SetVariables", "version": 1, "parameters": {},
        "mapper": {"variables": [
            {"name": "first_name", "value": "{{ifempty(11.contact.firstName; \"\")}}"},
            {"name": "customer_email", "value": "{{ifempty(11.contact.email; \"\")}}"},
            {"name": "tracking_url", "value": cf(F24_CF_TRACKING_URL)},
            {"name": "numero_pedido", "value": cf(F24_CF_NUMERO_PEDIDO)},
            {"name": "purchase_count", "value": cf(F24_CF_PURCHASE_COUNT, "\"0\"")},
            {"name": "last_products", "value": cf(F24_CF_LAST_PRODUCTS)},
            {"name": "last_purchase_value", "value": cf(F24_CF_LAST_PURCHASE_VALUE, "\"0\"")},
        ], "scope": "roundtrip"},
        "metadata": {"designer": {"x": x, "y": y}, "restore": {}},
    }


def set_vars_pre_claude_module(module_id, x, y, ctx_module_id=26):
    ctx = str(ctx_module_id)
    return {
        "id": module_id, "module": "util:SetVariables", "version": 1, "parameters": {},
        "mapper": {"variables": [{"name": "user_message_content", "value": (
            "[CONTEXTO DEL CLIENTE — datos reales traidos de GHL. USAR ESTO, NUNCA INVENTAR.]\n"
            "Nombre: {{ifempty(" + ctx + ".first_name; \"(sin nombre)\")}}\n"
            "Email (para link de pago / cotizacion): {{ifempty(" + ctx + ".customer_email; \"(sin email)\")}}\n"
            "Compras totales (purchase_count): {{ifempty(" + ctx + ".purchase_count; \"0\")}}\n"
            "Ultima compra: productos [{{ifempty(" + ctx + ".last_products; \"ninguno\")}}] "
            "por ${{ifempty(" + ctx + ".last_purchase_value; \"0\")}}\n"
            "Numero de pedido: {{ifempty(" + ctx + ".numero_pedido; \"(sin numero)\")}}\n"
            "Link de seguimiento (tracking_url): {{ifempty(" + ctx + ".tracking_url; \"(sin link de seguimiento)\")}}\n"
            "\n"
            "[CONTEXTO: historial de esta conversacion. No repitas preguntas ya respondidas. "
            "Cada linea es un turno: U=usuario, B=bot.]\n"
            "{{ifempty(2.history; \"(primera interaccion, sin historial previo)\")}}\n\n"
            "[MENSAJE NUEVO DEL CLIENTE A RESPONDER]\n"
            "{{28.user_msg}}"
        )}], "scope": "roundtrip"},
        "metadata": {"designer": {"x": x, "y": y}, "restore": {}},
    }


def ghl_search_conversation_module(module_id, x, y):
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": "https://services.leadconnectorhq.com/conversations/search", "method": "get",
            "headers": [
                {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
                {"name": "Version", "value": "2021-07-28"},
                {"name": "Accept", "value": "application/json"},
            ],
            "qs": [
                {"name": "locationId", "value": F24_LOCATION_ID},
                {"name": "contactId", "value": "{{1.contact_id}}"},
                {"name": "limit", "value": "1"},
            ],
            "timeout": 30, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
    }


def ghl_list_messages_module(module_id, x, y, search_module_id):
    src = str(search_module_id)
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": ("https://services.leadconnectorhq.com/conversations/"
                    "{{ifempty(first(ifempty(" + src + ".data.conversations; " + src + ".conversations)).id; \"none\")}}/messages"),
            "method": "get",
            "headers": [
                {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
                {"name": "Version", "value": "2021-07-28"},
                {"name": "Accept", "value": "application/json"},
            ],
            "qs": [{"name": "limit", "value": "20"}],
            "timeout": 30, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
    }


def iterator_messages_module(module_id, x, y, list_module_id):
    src = str(list_module_id)
    return {
        "id": module_id, "module": "builtin:BasicFeeder", "version": 1, "parameters": {},
        "mapper": {"array": "{{ifempty(" + src + ".data.messages.messages; ifempty(" + src + ".messages.messages; emptyarray))}}"},
        "metadata": {"designer": {"x": x, "y": y}, "restore": {"expect": {"array": {"label": "GHL messages"}}}},
    }


def aggregator_human_messages_module(module_id, x, y, iterator_module_id):
    it = str(iterator_module_id)
    recent = "{{addHours(now; -" + str(HANDOFF_HOURS) + ")}}"
    base = [
        {"a": "{{" + it + ".direction}}", "o": "text:equal", "b": "outbound"},
        {"a": "{{" + it + ".source}}", "o": "text:notequal", "b": "workflow"},
        {"a": "{{parseDate(" + it + ".dateAdded)}}", "o": "date:later", "b": recent},
    ]
    case_a = base + [{"a": "{{length(ifempty(" + it + ".userId; \"\"))}}", "o": "numeric:greater", "b": "30"}]
    case_b = base + [
        {"a": "{{length(ifempty(" + it + ".userId; \"\"))}}", "o": "numeric:less", "b": "30"},
        {"a": "{{ifempty(" + it + ".from; \"\")}}", "o": "text:notcontain", "b": " "},
    ]
    return {
        "id": module_id, "module": "builtin:BasicAggregator", "version": 1,
        "parameters": {"feeder": iterator_module_id},
        "filter": {"name": "Outbound humano en ventana de handoff", "conditions": [case_a, case_b]},
        "mapper": {"value": "{{" + it + ".id}}"},
        "metadata": {"designer": {"x": x, "y": y},
                     "restore": {"expect": {"value": {"label": "Message ID"}}},
                     "expect": [{"name": "value", "type": "text", "label": "Value"}]},
    }


def aggregator_inbound_bodies_module(module_id, x, y, iterator_module_id):
    """Recolecta los bodies de los mensajes INBOUND (mismo iterator que el handoff).
    El merge field {{message.body}} del webhook GHL llega vacío, así que tomamos el
    texto del último inbound directo de la API de conversaciones de GHL. Orden DESC →
    el primer elemento del array es el mensaje más reciente (el que disparó esta corrida)."""
    it = str(iterator_module_id)
    return {
        "id": module_id, "module": "builtin:BasicAggregator", "version": 1,
        "parameters": {"feeder": iterator_module_id},
        "filter": {"name": "Solo mensajes inbound",
                   "conditions": [[{"a": "{{" + it + ".direction}}", "o": "text:equal", "b": "inbound"}]]},
        "mapper": {"value": "{{" + it + ".body}}"},
        "metadata": {"designer": {"x": x, "y": y},
                     "restore": {"expect": {"value": {"label": "Body"}}},
                     "expect": [{"name": "value", "type": "text", "label": "Value"}]},
    }


def resolved_msg_module(module_id, x, y, search_module_id):
    """user_msg = texto del mensaje del cliente.
    El merge field del webhook ({{message.body}}) llega vacío, así que tomamos el texto del
    ÚLTIMO mensaje de la conversación vía search_conv (módulo 20). En este punto del flujo el
    bot aún no respondió, así que lastMessageBody = el mensaje inbound del cliente. Prefiere el
    campo del webhook (1.message_body) por si GHL lo arregla, y cae al de la API si viene vacío."""
    sm = str(search_module_id)
    # Fuente del mensaje, en orden de confiabilidad:
    #  1) 1.message.body  → standard data de GHL (lo que usa HC; real-time, viene en el webhook)
    #  2) 1.message_body  → custom data (por si el merge field se arregla)
    #  3) first(20.conversations).lastMessageBody → API (último recurso; tiene lag de índice)
    return {
        "id": module_id, "module": "util:SetVariables", "version": 1, "parameters": {},
        "mapper": {"variables": [
            # user_msg = el BUFFER acumulado (todos los mensajes del burst, módulo 33). Fallback al
            # mensaje suelto (standard data / custom / API) por si el buffer viniera vacío.
            {"name": "user_msg", "value":
                "{{ifempty(trim(33.pending_buffer); ifempty(1.message.body; ifempty(1.message_body; first(ifempty(" + sm + ".data.conversations; " + sm + ".conversations)).lastMessageBody)))}}"},
        ], "scope": "roundtrip"},
        "metadata": {"designer": {"x": x, "y": y}, "restore": {}},
    }


def evaluate_handoff_module(module_id, x, y, agg_module_id):
    agg = str(agg_module_id)
    return {
        "id": module_id, "module": "util:SetVariables", "version": 1, "parameters": {},
        "mapper": {"variables": [
            {"name": "is_human_active", "value": "{{if(length(" + agg + ".array) > 0; \"true\"; \"false\")}}"},
            {"name": "existing_mute_active", "value": (
                "{{if((ifempty(2.bot_muted_until; \"\") != \"\") && (parseDate(2.bot_muted_until) > now); \"true\"; \"false\")}}")},
            {"name": "should_respond", "value": (
                "{{if((length(" + agg + ".array) = 0) && ((ifempty(2.bot_muted_until; \"\") = \"\") || "
                "(parseDate(2.bot_muted_until) <= now)); \"true\"; \"false\")}}")},
            {"name": "mute_until_iso", "value": (
                "{{formatDate(addHours(now; " + str(HANDOFF_HOURS) + "); \"YYYY-MM-DDTHH:mm:ss[Z]\")}}")},
        ], "scope": "roundtrip"},
        "metadata": {"designer": {"x": x, "y": y}, "restore": {}},
    }


def datastore_mute_module(module_id, x, y, eval_module_id):
    ev = str(eval_module_id)
    return {
        "id": module_id, "module": "datastore:AddRecord", "version": 1,
        "parameters": {"datastore": F24_DATASTORE_ID},
        "mapper": {"key": "{{1.contact_id}}", "overwrite": True, "data": {
            "contactId": "{{1.contact_id}}", "contactName": "{{ifempty(1.full_name; \"Desconocido\")}}",
            "phone": "{{ifempty(1.phone; \"\")}}", "channel": "WhatsApp",
            "messageCount": "{{ifempty(2.messageCount; 0)}}", "lastMessageAt": "{{ifempty(2.lastMessageAt; now)}}",
            "history": "{{ifempty(2.history; \"\")}}", "escalated": True,
            "bot_muted_until": "{{" + ev + ".mute_until_iso}}", "muted_by": "human",
        }},
        "metadata": {"designer": {"x": x, "y": y}},
    }


def anthropic_http_module(module_id, x, y, set_vars_module_id):
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": "https://api.anthropic.com/v1/messages", "method": "post",
            "headers": [
                {"name": "x-api-key", "value": ANTHROPIC_TOKEN},
                {"name": "anthropic-version", "value": "2023-06-01"},
                {"name": "content-type", "value": "application/json"},
            ],
            "timeout": 60, "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": ANTHROPIC_BODY_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2048,
                "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                "messages": [
                    {"role": "user", "content": "{{" + str(set_vars_module_id) + ".user_message_content}}"},
                    {"role": "assistant", "content": "{"},
                ],
            },
            "shareCookies": False, "parseResponse": True, "allowRedirects": True,
            "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        "onerror": [resume_handler(96, ANTHROPIC_FALLBACK_BUNDLE, x, y + 300)],
    }


def parse_json_module(module_id, x, y, source_module_id):
    src = str(source_module_id)
    inner = "ifempty(" + src + ".data.content[0].text; " + src + ".data.content[1].text)"
    return {
        "id": module_id, "module": "json:ParseJSON", "version": 1,
        "parameters": {"type": CLAUDE_RESPONSE_DATASTRUCTURE_ID},
        "mapper": {"json": "{{\"{\" + trim(replace(replace(" + inner + "; \"```json\"; \"\"); \"```\"; \"\"))}}"},
        "metadata": {"designer": {"x": x, "y": y}},
        "onerror": [resume_handler(97, PARSE_FALLBACK_BUNDLE, x, y + 300)],
    }


def ghl_send_module_from_claude(module_id, x, y, parse_module_id):
    pm = str(parse_module_id)
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": "https://services.leadconnectorhq.com/conversations/messages", "method": "post",
            "headers": [
                {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
                {"name": "Version", "value": "2021-07-28"},
                {"name": "Content-Type", "value": "application/json"},
                {"name": "Accept", "value": "application/json"},
            ],
            "timeout": 60, "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": GHL_SEND_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {
                "type": "WhatsApp", "contactId": "{{1.contact_id}}",
                "message": "{{join(" + pm + ".messages; \"\n\n\")}}",
                "attachments": "{{" + pm + ".attachments}}",
            },
            "shareCookies": False, "parseResponse": True, "allowRedirects": True,
            "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
    }


def ghl_send_module_canned(module_id, x, y, canned_message):
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": "https://services.leadconnectorhq.com/conversations/messages", "method": "post",
            "headers": [
                {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
                {"name": "Version", "value": "2021-07-28"},
                {"name": "Content-Type", "value": "application/json"},
                {"name": "Accept", "value": "application/json"},
            ],
            "timeout": 60, "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": GHL_SEND_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {"type": "WhatsApp", "contactId": "{{1.contact_id}}", "message": canned_message},
            "shareCookies": False, "parseResponse": True, "allowRedirects": True,
            "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
    }


# ---- CIERRE F24: crear draft order + mandar link de pago (sub-route create_order) ----
def f24_process_order_module(module_id, x, y, parse_module_id):
    """POST a la Edge Function f24-process-order con el objeto order de Claude + datos de contacto.
    La función crea el draft order en Shopify y regresa {invoice_url, total}."""
    pm = str(parse_module_id)
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": F24_PROCESS_ORDER_URL, "method": "post",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            # Serializar el body via data structure (NO toString — toString no produce JSON válido
            # para arrays/colecciones). line_items/customer se mapean desde el order parseado por Claude.
            "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": F24_PROCESS_ORDER_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {
                "mode": "create_draft_order",
                "line_items": "{{" + pm + ".order.line_items}}",
                "customer": "{{" + pm + ".order.customer}}",
                "contact_id": "{{1.contact_id}}",
                "phone": "{{ifempty(1.phone; \"\")}}",
                # payment_method habilita la rama msi_promo (MercadoPago Cuenta B 9/12) en la Edge Function.
                "payment_method": "{{ifempty(" + pm + ".order.payment_method; \"online\")}}",
            },
            "timeout": 60, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        "onerror": [resume_handler(98, {"invoice_url": "", "ok": False}, x, y + 300)],
    }


def ghl_send_payment_link_module(module_id, x, y, order_http_module_id, parse_module_id=8):
    """Manda el pago según método: transferencia → CLABE + total real; tarjeta/OXXO → link online.
    El total real viene del Edge Function (42.total); la CLABE de Ferre24 va literal aquí."""
    om = str(order_http_module_id)
    pm = str(parse_module_id)
    # CRÍTICO: la respuesta HTTP parseada de Make vive bajo `.data` (igual que 7.data.content del
    # módulo Claude). Usamos ifempty(om.data.X; om.X) para ser robustos en ambos casos.
    # Preferir el link ENVUELTO (pay_url, con tracking de clic); fallback al invoice_url crudo.
    inv = "ifempty(" + om + ".data.pay_url; ifempty(" + om + ".data.invoice_url; " + om + ".invoice_url))"
    tot = "ifempty(" + om + ".data.total; " + om + ".total)"
    transfer_msg = (
        "El total de tu pedido es $\" + " + tot + " + \" MXN. Para pagar por transferencia: "
        "Banco Arcus - CLABE " + F24_TRANSFER_CLABE + " - A nombre de " + F24_TRANSFER_HOLDER + ". "
        "En cuanto transfieras, mandame tu comprobante por aqui y liberamos tu pedido 🛠️"
    )
    online_msg = (
        "Aqui esta tu link de pago seguro 👇 \" + " + inv + " + \" — ahi eliges tarjeta "
        "(con MSI donde aplica) u OXXO."
    )
    fail_msg = "Tuve un detalle generando tu pago. Un asesor del equipo te ayuda en un momento por aqui 🛠️"
    msg = (
        "{{if(" + pm + ".order.payment_method = \"transferencia\"; "
        "\"" + transfer_msg + "\"; "
        "if(ifempty(" + inv + "; \"\") != \"\"; "
        "\"" + online_msg + "\"; "
        "\"" + fail_msg + "\"))}}"
    )
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": "https://services.leadconnectorhq.com/conversations/messages", "method": "post",
            "headers": [
                {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
                {"name": "Version", "value": "2021-07-28"},
                {"name": "Content-Type", "value": "application/json"},
                {"name": "Accept", "value": "application/json"},
            ],
            "timeout": 60, "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": GHL_SEND_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {"type": "WhatsApp", "contactId": "{{1.contact_id}}", "message": msg},
            "shareCookies": False, "parseResponse": True, "allowRedirects": True,
            "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
    }


def datastore_add_claude(module_id, x, y, parse_module_id):
    pm = str(parse_module_id)
    return {
        "id": module_id, "module": "datastore:AddRecord", "version": 1,
        "parameters": {"datastore": F24_DATASTORE_ID},
        "mapper": {"key": "{{1.contact_id}}", "overwrite": True, "data": {
            "contactId": "{{1.contact_id}}", "contactName": "{{ifempty(1.full_name; \"Desconocido\")}}",
            "phone": "{{ifempty(1.phone; \"\")}}", "channel": "WhatsApp",
            "messageCount": 1, "lastMessageAt": "{{now}}",
            "history": ("{{substring(ifempty(2.history; \"\"); max(0; length(ifempty(2.history; \"\")) - 2500))}}"
                        "\nU: {{28.user_msg}}\nB: {{join(" + pm + ".messages; \" \")}}"),
            "escalated": False,
            "bot_muted_until": ("{{if(" + pm + ".action = \"human_handoff\"; "
                                "formatDate(addHours(now; 24); \"YYYY-MM-DDTHH:mm:ss[Z]\"); "
                                "ifempty(2.bot_muted_until; \"\"))}}"),
            "muted_by": ("{{if(" + pm + ".action = \"human_handoff\"; \"user_request\"; ifempty(2.muted_by; \"\"))}}"),
        }},
        "metadata": {"designer": {"x": x, "y": y}},
    }


def datastore_add_greeting(module_id, x, y):
    return {
        "id": module_id, "module": "datastore:AddRecord", "version": 1,
        "parameters": {"datastore": F24_DATASTORE_ID},
        "mapper": {"key": "{{1.contact_id}}", "overwrite": True, "data": {
            "contactId": "{{1.contact_id}}", "contactName": "{{ifempty(1.full_name; \"Desconocido\")}}",
            "phone": "{{ifempty(1.phone; \"\")}}", "channel": "WhatsApp",
            "messageCount": 1, "lastMessageAt": "{{now}}",
            "history": ("{{substring(ifempty(2.history; \"\"); max(0; length(ifempty(2.history; \"\")) - 2500))}}"
                        "\nU: {{28.user_msg}}\nB: [Greeting canned enviado: Bienvenido a Ferre24]"),
            "escalated": False,
            "bot_muted_until": "{{ifempty(2.bot_muted_until; \"\")}}",
            "muted_by": "{{ifempty(2.muted_by; \"\")}}",
        }},
        "metadata": {"designer": {"x": x, "y": y}},
    }


# ---------- Buffer / debounce de mensajes (Feature F) ----------
BUFFER_SLEEP_SECONDS = 12

def setvars_my_ts_module(module_id, x, y):
    """Token único de esta corrida (timestamp con ms)."""
    return {
        "id": module_id, "module": "util:SetVariables", "version": 1, "parameters": {},
        "mapper": {"variables": [
            {"name": "my_ts", "value": "{{formatDate(now; \"x\")}}"},
        ], "scope": "roundtrip"},
        "metadata": {"designer": {"x": x, "y": y}, "restore": {}},
    }


def datastore_buffer_write_module(module_id, x, y, my_ts_module_id):
    """Apila el mensaje entrante en pending_buffer y marca buffer_token = my_ts.
    Preserva los demás campos del registro (history/mute/etc) que vienen del módulo 2."""
    ts = str(my_ts_module_id)
    return {
        "id": module_id, "module": "datastore:AddRecord", "version": 1,
        "parameters": {"datastore": F24_DATASTORE_ID},
        "mapper": {"key": "{{1.contact_id}}", "overwrite": True, "data": {
            "contactId": "{{1.contact_id}}", "contactName": "{{ifempty(1.full_name; \"Desconocido\")}}",
            "phone": "{{ifempty(1.phone; \"\")}}", "channel": "WhatsApp",
            "messageCount": "{{ifempty(2.messageCount; 0)}}",
            "lastMessageAt": "{{ifempty(2.lastMessageAt; now)}}",
            "history": "{{ifempty(2.history; \"\")}}",
            "escalated": "{{ifempty(2.escalated; false)}}",
            "bot_muted_until": "{{ifempty(2.bot_muted_until; \"\")}}",
            "muted_by": "{{ifempty(2.muted_by; \"\")}}",
            "buffer_token": "{{" + ts + ".my_ts}}",
            "pending_buffer": "{{trim(ifempty(2.pending_buffer; \"\") + \" \" + ifempty(1.message.body; 1.message_body))}}",
        }},
        "metadata": {"designer": {"x": x, "y": y}},
    }


def sleep_module(module_id, x, y, seconds=BUFFER_SLEEP_SECONDS):
    # Módulo "Sleep" de Make = util:FunctionSleep. Param `duration` en segundos (máx 300).
    return {
        "id": module_id, "module": "util:FunctionSleep", "version": 1, "parameters": {},
        "mapper": {"duration": seconds}, "metadata": {"designer": {"x": x, "y": y}},
    }


def datastore_reget_module(module_id, x, y):
    """Re-lee el registro tras el sleep: trae el buffer_token + pending_buffer más recientes."""
    return {
        "id": module_id, "module": "datastore:GetRecord", "version": 1,
        "parameters": {"datastore": F24_DATASTORE_ID},
        "mapper": {"key": "{{1.contact_id}}", "returnWrapped": False},
        "metadata": {"designer": {"x": x, "y": y}},
    }


# ---------- Handoff: aviso al equipo (email + tag GHL) ----------
# Correos del equipo F24 que reciben las escaladas. Gibran los proporciona.
F24_TEAM_EMAILS = [
    "gibran.alonzo0506@gmail.com",   # MODO PRUEBA — Gibran avisará cuándo cambiar a los reales
    # REALES (activar cuando Gibran lo confirme):
    # "edgar.gvg@hotmail.com",
    # "f24atencionalcliente@hotmail.com",
]
GMAIL_CONN_ID = 8183100        # conexión Gmail de Make (team 354061, reusada de HC)
HANDOFF_TAG = "requiere-humano"
GHL_TAGS_DATASTRUCTURE_ID = 395040   # body {tags:[...]} para POST /contacts/{id}/tags

# Filtro: dispara solo cuando Claude devuelve action escalate o human_handoff (OR).
ESCALATE_FILTER = {
    "name": "action es escalate o human_handoff",
    "conditions": [
        [{"a": "{{8.action}}", "o": "text:equal", "b": "escalate"}],
        [{"a": "{{8.action}}", "o": "text:equal", "b": "human_handoff"}],
    ],
}


def team_email_module(module_id, x, y):
    """Email interno al equipo F24 cuando el bot escala. Reusa el módulo google-email de HC."""
    subject = "[F24 BOT] Cliente necesita asesor — {{ifempty(1.full_name; \"cliente\")}} ({{8.action}})"
    inbox = f"https://app.leadconnectorhq.com/v2/location/{F24_LOCATION_ID}/conversations/conversations"
    html = (
        "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto'>"
        "<div style='background:#2A2A2A;padding:16px 24px'>"
        "<h2 style='margin:0;color:#fff;font-size:18px'>FERRE24 · Bot WhatsApp</h2>"
        "<p style='margin:4px 0 0;color:#E8731C;font-size:13px'>Un cliente necesita que entre un asesor</p></div>"
        "<div style='padding:22px 24px;background:#fff;border:1px solid #eee'>"
        "<p style='margin:0 0 8px'><b>Tipo:</b> {{8.action}}</p>"
        "<p style='margin:0 0 8px'><b>Cliente:</b> {{ifempty(1.full_name; \"(sin nombre)\")}}</p>"
        "<p style='margin:0 0 8px'><b>Teléfono:</b> {{ifempty(1.phone; \"(sin tel)\")}}</p>"
        "<p style='margin:0 0 8px'><b>Motivo / intent:</b> {{ifempty(8.intent; \"-\")}}</p>"
        "<p style='margin:0 0 8px'><b>Último mensaje del cliente:</b><br>{{ifempty(28.user_msg; \"-\")}}</p>"
        "<p style='margin:18px 0 0'><a href='" + inbox + "' "
        "style='background:#E8731C;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;font-weight:bold'>"
        "Abrir conversación en GHL</a></p>"
        "</div></div>"
    )
    return {
        "id": module_id, "module": "google-email:sendAnEmail", "version": 4,
        "parameters": {"__IMTCONN__": GMAIL_CONN_ID},
        "mapper": {"to": list(F24_TEAM_EMAILS), "subject": subject, "content": html, "bodyType": "rawHtml"},
        "filter": ESCALATE_FILTER,
        "metadata": {"designer": {"x": x, "y": y}},
    }


def ghl_tag_handoff_module(module_id, x, y):
    """Agrega el tag 'requiere-humano' al contacto en GHL. Body via data structure (patrón probado)."""
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": "https://services.leadconnectorhq.com/contacts/{{1.contact_id}}/tags",
            "method": "post",
            "headers": [
                {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
                {"name": "Version", "value": "2021-07-28"},
                {"name": "Content-Type", "value": "application/json"},
                {"name": "Accept", "value": "application/json"},
            ],
            "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": GHL_TAGS_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {"tags": [HANDOFF_TAG]},
            "timeout": 30, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        # Best-effort: si el tag falla, NO debe tumbar el bot.
        "onerror": [resume_handler(48, {"ok": True}, x, y + 200)],
    }


# ---------- Build flow ----------
webhook_module = {
    "id": 1, "module": "gateway:CustomWebHook", "version": 1,
    "parameters": {"hook": F24_WEBHOOK_ID}, "mapper": {}, "metadata": {"designer": {"x": 0, "y": 0}},
}
datastore_get_module = {
    "id": 2, "module": "datastore:GetRecord", "version": 1,
    "parameters": {"datastore": F24_DATASTORE_ID},
    "filter": {"name": "Has contact_id", "conditions": [[{"a": "{{1.contact_id}}", "o": "text:notequal", "b": ""}]]},
    "mapper": {"key": "{{1.contact_id}}", "returnWrapped": False},
    "metadata": {"designer": {"x": 300, "y": 0}},
}
# Buffer/debounce: token → escribir buffer → sleep → re-leer (entre datastore_get y el resto)
buf_my_ts = setvars_my_ts_module(30, 360, 0)
buf_write = datastore_buffer_write_module(31, 420, 0, my_ts_module_id=30)
buf_sleep = sleep_module(32, 480, 0)
buf_reget = datastore_reget_module(33, 540, 0)

ghl_get_module = ghl_get_contact_module(3, 600, 0)
parse_contact_module = parse_ghl_contact_module(11, 750, 0, source_module_id=3)
search_conv_module = ghl_search_conversation_module(20, 900, 0)
list_msgs_module = ghl_list_messages_module(21, 1050, 0, search_module_id=20)
iter_msgs_module = iterator_messages_module(22, 1200, 0, list_module_id=21)
agg_human_module = aggregator_human_messages_module(23, 1350, 0, iterator_module_id=22)
eval_handoff = evaluate_handoff_module(24, 1510, 0, agg_module_id=23)
resolved_msg = resolved_msg_module(28, 1590, 0, search_module_id=20)

should_respond_cond = {"a": "{{24.should_respond}}", "o": "text:equal", "b": "true"}
# Debounce gate: solo procesa la corrida cuyo token sigue siendo el más reciente en el datastore
# (si llegó un mensaje más nuevo, su token sobrescribió buffer_token y esta corrida sale).
is_latest_cond = {"a": "{{33.buffer_token}}", "o": "text:equal", "b": "{{30.my_ts}}"}

# Route A: greeting
greeting_base = {"a": "{{28.user_msg}}", "o": "text:pattern", "b": GREETING_REGEX}
route_a_ghl = ghl_send_module_canned(5, 1800, -300, GREETING_MESSAGE)
ra_cond = build_gate_conditions(greeting_base)
for g in ra_cond:
    g.append(should_respond_cond)
    g.append(is_latest_cond)
route_a_ghl["filter"] = {"name": "Es saludo + bot debe responder", "conditions": ra_cond}
route_a_datastore = datastore_add_greeting(6, 2100, -300)

# Route B: Claude flow + sub-router post-parse (normal vs create_order)
not_greeting_base = {"a": "{{28.user_msg}}", "o": "text:notpattern", "b": GREETING_REGEX}
route_b_customer_ctx = customer_context_module(26, 1650, 150)
route_b_setvars = set_vars_pre_claude_module(12, 1800, 150, ctx_module_id=26)
rb_cond = build_gate_conditions(not_greeting_base)
for g in rb_cond:
    g.append(should_respond_cond)
    g.append(is_latest_cond)
route_b_customer_ctx["filter"] = {"name": "No saludo + bot debe responder", "conditions": rb_cond}
route_b_anthropic = anthropic_http_module(7, 2100, 150, set_vars_module_id=12)
route_b_parse = parse_json_module(8, 2400, 150, source_module_id=7)

# Sub-router (id 40) tras el parse: separa respuesta normal de creación de orden.
sub_normal_send = ghl_send_module_from_claude(9, 2900, 0, parse_module_id=8)
sub_normal_send["filter"] = {"name": "action != create_order",
                             "conditions": [[{"a": "{{8.action}}", "o": "text:notequal", "b": "create_order"}]]}
sub_normal_ds = datastore_add_claude(10, 3200, 0, parse_module_id=8)

sub_order_send = ghl_send_module_from_claude(41, 2900, 300, parse_module_id=8)
sub_order_send["filter"] = {"name": "action == create_order",
                            "conditions": [[{"a": "{{8.action}}", "o": "text:equal", "b": "create_order"}]]}
sub_order_create = f24_process_order_module(42, 3100, 300, parse_module_id=8)
sub_order_link = ghl_send_payment_link_module(43, 3300, 300, order_http_module_id=42)
sub_order_ds = datastore_add_claude(44, 3500, 300, parse_module_id=8)

# Sub-route de HANDOFF: email al equipo + tag GHL cuando action es escalate/human_handoff.
# Email validado en prod. Tag con body via data structure (NO raw) + onerror (best-effort).
sub_handoff_email = team_email_module(45, 2900, 600)   # lleva el ESCALATE_FILTER (gate de la sub-route)
sub_handoff_tag = ghl_tag_handoff_module(46, 3150, 600)

post_parse_router = {
    "id": 40, "module": "builtin:BasicRouter", "version": 1, "mapper": None,
    "metadata": {"designer": {"x": 2650, "y": 150}},
    "routes": [
        {"flow": [sub_normal_send, sub_normal_ds]},
        {"flow": [sub_order_send, sub_order_create, sub_order_link, sub_order_ds]},
        {"flow": [sub_handoff_email, sub_handoff_tag]},
    ],
}

# Route C: humano detectado -> mutear 4h
route_c_mute = datastore_mute_module(25, 1800, 450, eval_module_id=24)
route_c_mute["filter"] = {"name": "Humano respondio -> mutear bot 4h",
                          "conditions": [[{"a": "{{24.is_human_active}}", "o": "text:equal", "b": "true"}, is_latest_cond]]}

router_module = {
    "id": 4, "module": "builtin:BasicRouter", "version": 1, "mapper": None,
    "filter": {"name": f"NO tiene tag '{PAUSE_TAG}'", "conditions": [[PAUSE_CONDITION_PRE_ROUTER]]},
    "metadata": {"designer": {"x": 1650, "y": 0}},
    "routes": [
        {"flow": [route_a_ghl, route_a_datastore]},
        {"flow": [route_b_customer_ctx, route_b_setvars, route_b_anthropic, route_b_parse, post_parse_router]},
        {"flow": [route_c_mute]},
    ],
}

blueprint = {
    "name": "Ferre24 AI Bot — WhatsApp",
    "flow": [webhook_module, datastore_get_module,
             buf_my_ts, buf_write, buf_sleep, buf_reget,
             ghl_get_module, parse_contact_module,
             search_conv_module, list_msgs_module, iter_msgs_module, agg_human_module,
             eval_handoff, resolved_msg, router_module],
    "metadata": {
        "instant": True, "version": 1,
        "scenario": {"roundtrips": 1, "maxErrors": 100, "autoCommit": True,
                     "autoCommitTriggerLast": True, "sequential": False, "confidential": False,
                     "dataloss": False, "dlq": False, "freshVariables": False},
        "designer": {"orphans": []},
    },
    "scheduling": {"type": "immediately"},
    "interface": {"input": [], "output": []},
}


def _validate_ids():
    pending = [n for n, v in {
        "F24_WEBHOOK_ID": F24_WEBHOOK_ID, "F24_DATASTORE_ID": F24_DATASTORE_ID,
        "GHL_CONTACT_DATASTRUCTURE_ID": GHL_CONTACT_DATASTRUCTURE_ID,
        "ANTHROPIC_BODY_DATASTRUCTURE_ID": ANTHROPIC_BODY_DATASTRUCTURE_ID,
        "CLAUDE_RESPONSE_DATASTRUCTURE_ID": CLAUDE_RESPONSE_DATASTRUCTURE_ID,
        "GHL_SEND_DATASTRUCTURE_ID": GHL_SEND_DATASTRUCTURE_ID,
    }.items() if not v]
    creds = [n for n, v in {"GHL_API_KEY": GHL_TOKEN, "ANTHROPIC_API_KEY": ANTHROPIC_TOKEN}.items()
             if str(v).startswith("__PENDING")]
    return pending, creds


if __name__ == "__main__":
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, ensure_ascii=False, separators=(",", ":"))
    pending, creds = _validate_ids()
    print(f"Prompt length: {len(SYSTEM_PROMPT)} chars")
    print(f"Blueprint output: {OUTPUT_PATH}  ({os.path.getsize(OUTPUT_PATH)} bytes)")
    print(f"Whitelist mode: {WHITELIST_MODE} (tag '{WHITELIST_TAG}')  ·  Pause tag: '{PAUSE_TAG}'")
    print(f"Location F24: {F24_LOCATION_ID}")
    if pending:
        print(f"\n⚠️  IDs Make PENDIENTES (crear en Fase 2): {', '.join(pending)}")
    if creds:
        print(f"⚠️  Credenciales PENDIENTES (.env): {', '.join(creds)}")
    if not pending and not creds:
        print("\n✅ Todos los IDs y credenciales presentes — listo para deploy.")
