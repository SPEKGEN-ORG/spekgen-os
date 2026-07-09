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

# ---------- Durable fix: inyección determinista de link por SKU (anti-alucinación de URLs) ----------
# Cuando está ON: el LLM NO escribe URLs de producto; el sistema adjunta el link OFICIAL resuelto
# desde catalog_links.json por cada SKU/ID en products_mentioned (hasta 3). El link se resuelve con
# un switch() Make (match literal, dot-safe para SKUs como GPD8.5M). Cero módulos/datastores nuevos:
# la resolución vive en el mapper del módulo de envío existente. Default OFF → build live sin cambio.
# Activar para el candidato v2.1:  F24_LINK_INJECTION=1 /usr/bin/python3 build_f24_bot_blueprint.py
SYSTEM_LINK_INJECTION = os.environ.get("F24_LINK_INJECTION") == "1"
LINK_INJECTION_MAX_PRODUCTS = 3
CATALOG_LINKS_PATH = os.path.join(KB_DIR, "catalog_links.json") if "KB_DIR" in dir() else None

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
F24_OPP_TRACK_URL = "https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/f24-opp-track"
F24_OPP_TRACK_DATASTRUCTURE_ID = 420195  # body {contact_id, action, intent, products} para crear/avanzar la opp
# === Edge Function de cotización de envío (Skydropx quote — feature 2026-07) ===
# El bot emite action="quote_shipping" con CP + SKUs; este EF cotiza la tarifa REAL por CP y regresa
# {ok, cheapest, mensaje}. La sub-route quote manda `mensaje` al cliente. Reemplaza el escalate por
# costo de envío. NO genera guía (eso es f24-generate-guide/Envíoclick). Ver edge/f24-quote-shipping.
F24_QUOTE_SHIPPING_URL = "https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/f24-quote-shipping"
F24_QUOTE_DATASTRUCTURE_ID = 420242  # body {cp_destino, skus[], contact_id} — serializa skus como array real

# === Edge Function de agenda de llamadas (GHL calendars — feature 2026-07) ===
# El bot emite action="get_call_slots" (ofrece horarios reales) y luego "book_call" (agenda la cita).
# El EF consulta free-slots del calendario del asesor (round-robin Alfredo/Edgar por hash del contacto)
# y crea la cita real. Reemplaza el viejo R32 "prometo la llamada por texto + escalo por correo".
# El `mensaje` que regresa (horarios o confirmación) lo manda la sub-route al cliente. Ver edge/f24-book-appointment.
F24_BOOK_APPT_URL = "https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/f24-book-appointment"
F24_BOOK_APPT_DATASTRUCTURE_ID = 423734  # body {mode, contact_id, call_choice}

# Cuenta de transferencia de Ferre24 (MXN — la que se manda a clientes). Datos de Sergio 2026-06-02.
F24_TRANSFER_CLABE = "706180276752083666"  # Banco Arcus
F24_TRANSFER_HOLDER = "Sergio Jose Duarte Simon"

# ---------- Auto-handoff (polling pre-respuesta) ----------
# Controla DOS cosas en la ruta de polling (Route C): (1) la ventana de detección del
# aggregator (módulo 23) — cuántas horas hacia atrás se busca un mensaje OUTBOUND de un
# humano staff, y (2) la duración del mute que se escribe al detectarlo (módulo 24).
# 24h = cuando un humano (Sergio/Gibran) contesta, el bot se apaga 24h. Además Route C
# escribe el tag 'bot-pausado' (VISIBLE en el inbox); el cron de follow-ups (5278490) lo
# retira cuando bot_muted_until expira. OJO: una vez puesto el tag, el pre-router (módulo 4)
# bloquea TODO → el tag es el gate de reactivación, no el datastore. Por eso el cron debe
# retirarlo. NO afecta los mutes por acción de Claude (escalate 4h / human_handoff 24h
# viven hardcodeados en datastore_add_claude).
HANDOFF_HOURS = 24

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

    # Durable fix: cuando el sistema adjunta los links oficiales por SKU, el LLM NO debe escribir
    # URLs de producto (evita duplicados y elimina la alucinación de slugs de raíz).
    if SYSTEM_LINK_INJECTION:
        parts.append("\n\n" + "=" * 40)
        parts.append("== LINKS DE PRODUCTO: LOS ADJUNTA EL SISTEMA (NO LOS ESCRIBAS) ==")
        parts.append("=" * 40)
        parts.append(
            "IMPORTANTE (override de la sección LINKS Y PRECIOS): NO escribas URLs de producto "
            "(ferre24.com.mx/products/...) dentro de messages. Solo menciona el producto por nombre "
            "y pon su SKU/ID EXACTO (de la columna 'SKU / ID' del catálogo) en products_mentioned. "
            "El sistema adjunta automáticamente el link OFICIAL de cada SKU al final del mensaje. "
            "Tú asegúrate de poner el/los SKU correctos en products_mentioned (hasta 3). Los PRECIOS "
            "sí los sigues citando tú, copiados VERBATIM del catálogo (formato $X (antes $Y)). Las "
            "URLs de imagen siguen yendo en attachments como siempre."
        )

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
            "[CONVERSACION RECIENTE REAL DE WHATSAPP — los ultimos mensajes, MAS RECIENTE PRIMERO. "
            "Incluye al Cliente, al Asesor humano (si un humano del equipo intervino) y al Bot. "
            "Continua con PLENA conciencia de lo ya hablado; si un Asesor ya atendio o acordo algo, "
            "respetalo y NO lo repreguntes ni lo contradigas. No repitas preguntas ya respondidas.]\n"
            "{{ifempty(join(35.array; \"\n\"); ifempty(2.history; \"(primera interaccion, sin historial previo)\"))}}\n\n"
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
    # DISCRIMINADOR F24 (verificado con data real 2026-06-14): el bot manda vía API/PIT con
    # `userId` VACÍO; un humano staff desde el inbox GHL manda con su `userId` POBLADO (~20 chars).
    # Ambos salen como source="app" y con el MISMO `from` (+52 1 33 1790 3630), así que lo único
    # que los separa es el userId. La lógica vieja de HC (userId>30 chars  O  userId<30 + from
    # sin espacios) NUNCA hacía match aquí: el userId es ~20 chars y el from SIEMPRE trae espacios
    # → el bot no detectaba la intervención humana. Regla correcta: outbound + userId no vacío.
    human = [
        {"a": "{{" + it + ".direction}}", "o": "text:equal", "b": "outbound"},
        {"a": "{{" + it + ".source}}", "o": "text:notequal", "b": "workflow"},
        {"a": "{{parseDate(" + it + ".dateAdded)}}", "o": "date:later", "b": recent},
        {"a": "{{length(ifempty(" + it + ".userId; \"\"))}}", "o": "numeric:greater", "b": "0"},
    ]
    return {
        "id": module_id, "module": "builtin:BasicAggregator", "version": 1,
        "parameters": {"feeder": iterator_module_id},
        "filter": {"name": "Outbound humano (userId poblado) en ventana", "conditions": [human]},
        "mapper": {"value": "{{" + it + ".id}}"},
        "metadata": {"designer": {"x": x, "y": y},
                     "restore": {"expect": {"value": {"label": "Message ID"}}},
                     "expect": [{"name": "value", "type": "text", "label": "Value"}]},
    }


def aggregator_transcript_module(module_id, x, y, iterator_module_id):
    """Arma el TRANSCRIPT REAL de la conversación de GHL (últimos ~20 mensajes) etiquetado por rol,
    para dárselo a Claude como contexto. Resuelve el hueco de contexto cuando un humano (Asesor) toma
    el chat durante una pausa por tag 'bot-pausado': al quitarse el tag, el bot lee TODO lo que se
    habló (Cliente + Asesor + Bot) aunque su history interno del datastore no lo tenga.
    Rol: inbound = Cliente; outbound con userId poblado = Asesor (humano staff); outbound sin userId = Bot.
    (Usa el mismo discriminador userId que separa staff del bot.) Loop independiente del de handoff."""
    it = str(iterator_module_id)
    role = ("if(" + it + ".direction = \"inbound\"; \"Cliente\"; "
            "if(length(ifempty(" + it + ".userId; \"\")) > 0; \"Asesor\"; \"Bot\"))")
    return {
        "id": module_id, "module": "builtin:BasicAggregator", "version": 1,
        "parameters": {"feeder": iterator_module_id},
        "mapper": {"value": "{{" + role + " + \": \" + ifempty(" + it + ".body; \"\")}}"},
        "metadata": {"designer": {"x": x, "y": y},
                     "restore": {"expect": {"value": {"label": "Linea"}}},
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
                # temperature 0.3: bot de ventas con reglas estrictas + salida JSON. A 1.0 (default)
                # el comportamiento variaba (a veces inventaba envío, a veces escalaba). Requiere que
                # la data structure ANTHROPIC_BODY_DATASTRUCTURE_ID tenga el campo 'temperature' (number).
                "temperature": 0.3,
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


def _link_switch_cases() -> str:
    """Construye los pares 'SKU'; 'NL+url' del switch() Make desde catalog_links.json.
    Match literal (dot-safe para SKUs como GPD8.5M). Valor = doble salto de línea + URL oficial,
    así el default '' no agrega línea en blanco cuando el SKU no resuelve."""
    with open(CATALOG_LINKS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    pairs = []
    for key, v in raw.items():
        url = (v.get("url") or "").strip()
        if not url or '"' in key or '"' in url:
            continue
        pairs.append('"%s"; "\n\n%s"' % (key, url))
    return "; ".join(pairs)


def _link_inject_suffix(pm: str) -> str:
    """Sufijo Make que adjunta el link oficial de hasta N SKUs de products_mentioned via switch()."""
    cases = _link_switch_cases()
    segs = ""
    for i in range(1, LINK_INJECTION_MAX_PRODUCTS + 1):
        segs += " + switch(get(" + pm + ".products_mentioned; %d); %s; \"\")" % (i, cases)
    return segs


def ghl_send_module_from_claude(module_id, x, y, parse_module_id):
    pm = str(parse_module_id)
    base = "join(" + pm + ".messages; \"\n\n\")"
    message_expr = "{{" + base + (_link_inject_suffix(pm) if SYSTEM_LINK_INJECTION else "") + "}}"
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
                "message": message_expr,
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
                # CP del cliente → la Edge Function lo escribe en el custom field codigo_postal de GHL.
                # Prefiere order.customer.codigo_postal; cae al top-level codigo_postal si falta.
                "codigo_postal": "{{ifempty(" + pm + ".order.customer.codigo_postal; ifempty(" + pm + ".codigo_postal; \"\"))}}",
            },
            "timeout": 60, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        "onerror": [resume_handler(98, {"invoice_url": "", "ok": False}, x, y + 300)],
    }


def f24_opp_track_module(module_id, x, y, parse_module_id):
    """POST best-effort a la Edge Function f24-opp-track: crea/AVANZA la oportunidad del contacto en
    el pipeline "Ventas Whatsapp" (Nuevo→Calificado→Cotizado→Link según action/intent/products de
    Claude) y, al CREAR, hereda el dueño del contacto (round-robin 50/50 de GHL a nivel contacto).
    Va en su PROPIA ruta del post-router SIN filtro → corre en cada turno atendido. onerror = nunca
    rompe el bot. RECONSTRUYE el módulo que un rebuild borró (~19-jun-2026) y que dejó de crear opps."""
    pm = str(parse_module_id)
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": F24_OPP_TRACK_URL, "method": "post",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": F24_OPP_TRACK_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {
                "contact_id": "{{1.contact_id}}",
                "action": "{{" + pm + ".action}}",
                "intent": "{{" + pm + ".intent}}",
                "products": "{{join(" + pm + ".products_mentioned; \",\")}}",
            },
            "timeout": 30, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        "onerror": [resume_handler(92, {"ok": False}, x, y + 300)],
    }


def f24_save_cp_module(module_id, x, y, parse_module_id):
    """POST best-effort a la Edge Function (mode=save_cp) para guardar el codigo_postal del cliente
    en su contacto GHL cuando lo da SIN crear orden (ej. al preguntar por el envío). En el cierre
    (create_order) el CP ya lo escribe la rama de la orden, así que este módulo va en la ruta NORMAL
    y se gatea con un filtro a codigo_postal no vacío. onerror = nunca rompe el bot."""
    pm = str(parse_module_id)
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": F24_PROCESS_ORDER_URL, "method": "post",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "contentType": "json", "inputMethod": "dataStructure",
            # Reusa la DS del process-order (389552) mapeando solo mode + contact_id + codigo_postal.
            "bodyDataStructure": F24_PROCESS_ORDER_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {
                "mode": "save_cp",
                "contact_id": "{{1.contact_id}}",
                "codigo_postal": "{{" + pm + ".codigo_postal}}",
            },
            "timeout": 60, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        "onerror": [resume_handler(95, {"ok": False}, x, y + 300)],
    }


def f24_quote_shipping_module(module_id, x, y, parse_module_id):
    """POST a la Edge Function f24-quote-shipping cuando action=quote_shipping. Manda el CP + los SKUs
    mencionados; el EF cotiza la tarifa REAL por CP con Skydropx y regresa {ok, cheapest, mensaje}.
    El `mensaje` lo envía el módulo siguiente al cliente. onerror = nunca rompe el bot (fallback)."""
    pm = str(parse_module_id)
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": F24_QUOTE_SHIPPING_URL, "method": "post",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": F24_QUOTE_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {
                "cp_destino": "{{" + pm + ".codigo_postal}}",
                "skus": "{{" + pm + ".products_mentioned}}",
                "contact_id": "{{1.contact_id}}",
            },
            "timeout": 60, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        # onerror: si el EF cae, manda un mensaje-fallback para que el cliente no quede colgado.
        "onerror": [resume_handler(93, {"mensaje": "Déjame confirmar el costo del envío a tu CP con el equipo y te lo paso en un momento 📦"}, x, y + 300)],
    }


def ghl_send_quote_message_module(module_id, x, y, quote_http_module_id):
    """Manda al cliente el `mensaje` que regresó f24-quote-shipping (la tarifa real, o el fallback).
    La respuesta HTTP parseada de Make vive bajo `.data`; fallback al top-level por robustez."""
    qm = str(quote_http_module_id)
    message_expr = "{{ifempty(" + qm + ".data.mensaje; " + qm + ".mensaje)}}"
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
            "dataStructureBodyContent": {"type": "WhatsApp", "contactId": "{{1.contact_id}}", "message": message_expr},
            "shareCookies": False, "parseResponse": True, "allowRedirects": True,
            "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
    }


def f24_book_appointment_module(module_id, x, y, mode, err_module_id):
    """POST a la Edge Function f24-book-appointment (agenda de llamadas con calendarios GHL).
    mode="slots": consulta la agenda REAL del asesor (round-robin Alfredo/Edgar) y regresa los horarios
      libres → el bot los ofrece (action=get_call_slots).
    mode="book": agenda la cita al horario que eligió el cliente (action=book_call). `call_choice` = el
      mensaje del cliente ({{28.user_msg}}); el EF lo mapea al slot real (no dependemos de que Claude
      arme una fecha ISO). El `mensaje` que regresa (horarios o confirmación) lo manda el módulo
      siguiente al cliente. onerror = nunca rompe el bot (fallback)."""
    body = {"mode": mode, "contact_id": "{{1.contact_id}}"}
    fb = "Con gusto te agendo la llamada con un asesor. ¿Qué día y horario te acomoda? Yo lo coordino."
    if mode == "book":
        body["call_choice"] = "{{28.user_msg}}"
        fb = "¡Va! Dejo agendada tu llamada con un asesor. Te marca a este mismo número. Si prefieres otro horario, dime."
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": F24_BOOK_APPT_URL, "method": "post",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "contentType": "json", "inputMethod": "dataStructure",
            "bodyDataStructure": F24_BOOK_APPT_DATASTRUCTURE_ID,
            "dataStructureBodyContent": body,
            "timeout": 60, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        "onerror": [resume_handler(err_module_id, {"mensaje": fb}, x, y + 300)],
    }


def f24_save_name_module(module_id, x, y, parse_module_id):
    """POST best-effort a la Edge Function (mode=save_name) para guardar el firstName REAL del cliente
    en su contacto GHL cuando el bot lo captura ("¿con quién tengo el gusto?"). Reemplaza el alias
    basura del perfil de WhatsApp para que los follow-ups ({{contact.first_name}}) dejen de mandar
    "Hola Modelorma". Va en su PROPIA ruta del router (NO encadenado tras save_cp, porque el nombre se
    captura seguido SIN CP) y se gatea con un filtro a customer_name no vacío. onerror = nunca rompe."""
    pm = str(parse_module_id)
    return {
        "id": module_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": F24_PROCESS_ORDER_URL, "method": "post",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "contentType": "json", "inputMethod": "dataStructure",
            # Reusa la DS del process-order mapeando solo mode + contact_id + customer_name.
            "bodyDataStructure": F24_PROCESS_ORDER_DATASTRUCTURE_ID,
            "dataStructureBodyContent": {
                "mode": "save_name",
                "contact_id": "{{1.contact_id}}",
                "customer_name": "{{" + pm + ".customer_name}}",
            },
            "timeout": 60, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        "onerror": [resume_handler(94, {"ok": False}, x, y + 300)],
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


def datastore_add_claude(module_id, x, y, parse_module_id, is_order=False):
    """Guarda el registro tras una respuesta de Claude.

    Estado de conversación (lo leen el bot vía should_respond y el cron de follow-ups vía muted_by):
      - is_order=True (módulo 44, rama create_order): muted_by='order_pending'. El bot SIGUE
        contestando (no se mutea), pero el follow-up cron NO manda nudge de venta (manda recordatorio
        de pago o nada). escalated=False.
      - is_order=False (módulo 10, rama normal):
          action='escalate'     → muteo 4h, muted_by='escalation', escalated=True, escalated_at=now.
          action='human_handoff'→ muteo 24h, muted_by='user_request', escalated=True, escalated_at=now.
          action='respond'      → estado BOT limpio (muted_by='', sin mute) → el cron sí puede dar nudge.
    El cron de follow-ups solo nudgea cuando muted_by='' (estado BOT activo). escalated se auto-limpia
    en la siguiente respuesta normal; escalated_at deja rastro para recuperación SLA del cron.
    """
    pm = str(parse_module_id)
    iso24 = "formatDate(addHours(now; 24); \"YYYY-MM-DDTHH:mm:ss[Z]\")"
    iso4 = "formatDate(addHours(now; 4); \"YYYY-MM-DDTHH:mm:ss[Z]\")"
    if is_order:
        state = {
            "escalated": False,
            "escalated_at": "",
            "bot_muted_until": "",
            "muted_by": "order_pending",
        }
    else:
        state = {
            "escalated": "{{if(" + pm + ".action = \"human_handoff\" || " + pm + ".action = \"escalate\"; true; false)}}",
            "escalated_at": "{{if(" + pm + ".action = \"human_handoff\" || " + pm + ".action = \"escalate\"; now; \"\")}}",
            "bot_muted_until": ("{{if(" + pm + ".action = \"human_handoff\"; " + iso24 + "; "
                                "if(" + pm + ".action = \"escalate\"; " + iso4 + "; \"\"))}}"),
            "muted_by": ("{{if(" + pm + ".action = \"human_handoff\"; \"user_request\"; "
                         "if(" + pm + ".action = \"escalate\"; \"escalation\"; \"\"))}}"),
        }
    data = {
        "contactId": "{{1.contact_id}}", "contactName": "{{ifempty(1.full_name; \"Desconocido\")}}",
        "phone": "{{ifempty(1.phone; \"\")}}", "channel": "WhatsApp",
        "messageCount": 1, "lastMessageAt": "{{now}}",
        "history": ("{{substring(ifempty(2.history; \"\"); max(0; length(ifempty(2.history; \"\")) - 2500))}}"
                    "\nU: {{28.user_msg}}\nB: {{join(" + pm + ".messages; \" \")}}"),
        "followup_stage": 0,
    }
    data.update(state)
    return {
        "id": module_id, "module": "datastore:AddRecord", "version": 1,
        "parameters": {"datastore": F24_DATASTORE_ID},
        "mapper": {"key": "{{1.contact_id}}", "overwrite": True, "data": data},
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
            # Saludo = estado BOT limpio (el saludo solo dispara cuando should_respond=true, o sea no muteado).
            "escalated": False,
            "escalated_at": "",
            "bot_muted_until": "",
            "muted_by": "",
            "followup_stage": 0,
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
    "gibran.alonzo0506@gmail.com",      # Gibran (supervisión)
    "edgar.gvg@hotmail.com",            # Edgar (equipo F24) — activado 2026-06-11
    "a25077492@gmail.com",              # Alfredo (equipo F24) — activado 2026-07-07 (rolado 50/50 de leads)
    "f24atencionalcliente@hotmail.com", # Sergio Duarte (atención cliente) — activado 2026-06-11
]
GMAIL_CONN_ID = 8183100        # conexión Gmail de Make (team 354061, reusada de HC)
HANDOFF_TAG = "requiere-humano"
CALL_TAG = "pidio-llamada"            # R32: el cliente pidió que le llamen → alerta en el panel del rep
GHL_TAGS_DATASTRUCTURE_ID = 395040   # body {tags:[...]} para POST /contacts/{id}/tags

# Filtro: dispara solo cuando Claude devuelve action escalate o human_handoff (OR).
ESCALATE_FILTER = {
    "name": "action es escalate o human_handoff",
    "conditions": [
        [{"a": "{{8.action}}", "o": "text:equal", "b": "escalate"}],
        [{"a": "{{8.action}}", "o": "text:equal", "b": "human_handoff"}],
    ],
}


# CRM SPEKGEN (white-label de GHL). El equipo abre aquí las conversaciones — NUNCA decir "GHL".
SPEKGEN_CRM_URL = f"https://app.spekgen.com/v2/location/{F24_LOCATION_ID}/conversations/conversations/"
# Logos hospedados (bucket público Supabase post-media) para el email.
LOGO_F24 = "https://wjlwpfaogjpeqgyxxnwa.supabase.co/storage/v1/object/public/post-media/f24/email-assets/f24-logo.png"
LOGO_SPEKGEN = "https://wjlwpfaogjpeqgyxxnwa.supabase.co/storage/v1/object/public/post-media/f24/email-assets/spekgen-logo.png"


def team_email_module(module_id, x, y):
    """Email interno al equipo F24 cuando el bot escala. google-email (conn HC) + branding."""
    subject = "[Ferre24] Un cliente necesita asesor — {{ifempty(1.full_name; \"cliente\")}}"
    html = (
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' "
        "style='background:#f4f4f5;padding:24px 0;font-family:Arial,Helvetica,sans-serif'><tr><td align='center'>"
        "<table role='presentation' width='600' cellpadding='0' cellspacing='0' "
        "style='max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e7e7e9'>"
        # Header con logo F24 (fondo cream para logo a color)
        "<tr><td style='background:#F8F3E9;padding:18px 28px' align='left'>"
        "<img src='" + LOGO_F24 + "' alt='Ferre24' height='40' style='height:40px;display:block;border:0'></td></tr>"
        # Franja de alerta naranja F24
        "<tr><td style='background:#FF5C00;padding:15px 28px' align='left'>"
        "<p style='margin:0;color:#ffffff;font-size:17px;font-weight:bold'>🔔 Un cliente necesita un asesor</p>"
        "<p style='margin:3px 0 0;color:#ffe2cf;font-size:12px'>Entra a la conversación para atenderlo</p></td></tr>"
        # Body: datos
        "<tr><td style='padding:24px 28px'>"
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' style='font-size:14px;color:#333333'>"
        "<tr><td style='padding:6px 0;color:#999999;width:120px'>Tipo</td>"
        "<td style='padding:6px 0;font-weight:bold'>{{if(8.action = \"human_handoff\"; \"Pidió hablar con humano\"; \"Escalación\")}}</td></tr>"
        "<tr><td style='padding:6px 0;color:#999999'>Cliente</td>"
        "<td style='padding:6px 0;font-weight:bold'>{{ifempty(1.full_name; \"(sin nombre)\")}}</td></tr>"
        "<tr><td style='padding:6px 0;color:#999999'>Teléfono</td>"
        "<td style='padding:6px 0;font-weight:bold'>{{ifempty(1.phone; \"(sin tel)\")}}</td></tr>"
        "<tr><td style='padding:6px 0;color:#999999;vertical-align:top'>Motivo</td>"
        "<td style='padding:6px 0'>{{ifempty(8.intent; \"-\")}}</td></tr>"
        "<tr><td style='padding:6px 0;color:#999999'>Producto(s)</td>"
        "<td style='padding:6px 0;font-weight:bold'>{{ifempty(join(8.products_mentioned; \", \"); \"-\")}}</td></tr>"
        "<tr><td style='padding:6px 0;color:#999999'>Código postal</td>"
        "<td style='padding:6px 0;font-weight:bold'>{{ifempty(8.codigo_postal; \"(no proporcionado)\")}}</td></tr></table>"
        # Resumen del lead calificado (lead_summary) — vacío en handoffs emocionales/queja.
        "<div style='margin-top:14px;background:#fff7f2;border-left:3px solid #FF5C00;padding:12px 14px;border-radius:4px'>"
        "<p style='margin:0 0 4px;font-size:11px;color:#999999;text-transform:uppercase;letter-spacing:.5px'>Resumen del lead</p>"
        "<p style='margin:0;font-size:14px;color:#333333;font-weight:bold'>{{ifempty(8.lead_summary; \"(lead no calificado — ver conversación)\")}}</p></div>"
        "<div style='margin-top:14px;background:#f7f7f8;border-left:3px solid #FF5C00;padding:12px 14px;border-radius:4px'>"
        "<p style='margin:0 0 4px;font-size:11px;color:#999999;text-transform:uppercase;letter-spacing:.5px'>Último mensaje del cliente</p>"
        "<p style='margin:0;font-size:14px;color:#333333'>{{ifempty(28.user_msg; \"-\")}}</p></div>"
        # Botón → CRM SPEKGEN
        "<table role='presentation' cellpadding='0' cellspacing='0' style='margin:22px 0 2px'><tr>"
        "<td style='border-radius:8px;background:#FF5C00' align='center'>"
        "<a href='" + SPEKGEN_CRM_URL + "' style='display:inline-block;padding:13px 28px;color:#ffffff;"
        "font-size:15px;font-weight:bold;text-decoration:none'>Abrir conversación en SPEKGEN &rarr;</a>"
        "</td></tr></table></td></tr>"
        # Footer con logo SPEKGEN
        "<tr><td style='background:#fafafa;padding:18px 28px;border-top:1px solid #eeeeee' align='center'>"
        "<img src='" + LOGO_SPEKGEN + "' alt='SPEKGEN' height='20' style='height:20px;display:block;margin:0 auto 7px;border:0'>"
        "<p style='margin:0;font-size:11px;color:#aaaaaa'>Notificación automática del bot de WhatsApp &middot; CRM SPEKGEN</p>"
        "</td></tr></table></td></tr></table>"
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


def ghl_tag_call_module(module_id, x, y):
    """Agrega el tag 'pidio-llamada' SOLO cuando el lead_summary marca 'LLAMADA SOLICITADA'
    (R32 callback). El panel del rep lo fija arriba con alerta '📞 PIDIÓ LLAMADA'."""
    m = ghl_tag_handoff_module(module_id, x, y)          # reusa el patrón probado
    m["mapper"]["dataStructureBodyContent"] = {"tags": [CALL_TAG]}
    m["filter"] = {"name": "solo si pidió llamada",
                   "conditions": [[{"a": "{{8.lead_summary}}", "o": "text:contain",
                                    "b": "LLAMADA SOLICITADA"}]]}
    m["onerror"] = [resume_handler(100, {"ok": True}, x, y + 200)]
    return m


def ghl_tag_pause_module(module_id, x, y):
    """Agrega el tag 'bot-pausado' al contacto cuando un humano staff toma la conversación
    (Route C / polling). Hace el mute VISIBLE en el inbox de GHL. Mismo patrón probado que
    ghl_tag_handoff_module (body via data structure 395040 + onerror best-effort).
    El cron de follow-ups (5278490) retira este tag cuando bot_muted_until expira (24h)."""
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
            "dataStructureBodyContent": {"tags": [PAUSE_TAG]},
            "timeout": 30, "shareCookies": False, "parseResponse": True,
            "allowRedirects": True, "stopOnHttpError": False, "requestCompressedContent": True,
        },
        "metadata": {"designer": {"x": x, "y": y}},
        # Best-effort: si el tag falla, el mute en datastore ya quedó escrito (módulo 25).
        "onerror": [resume_handler(99, {"ok": True}, x, y + 200)],
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
# 2do loop (independiente del de handoff) sobre los mismos 20 mensajes de GHL: arma el transcript
# real etiquetado por rol → contexto para Claude (resuelve el hueco tras una pausa por handoff).
iter_transcript = iterator_messages_module(34, 1430, 250, list_module_id=21)
agg_transcript = aggregator_transcript_module(35, 1510, 250, iterator_module_id=34)
eval_handoff = evaluate_handoff_module(24, 1650, 0, agg_module_id=23)
resolved_msg = resolved_msg_module(28, 1740, 0, search_module_id=20)

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
# Guarda el CP en GHL cuando el cliente lo da en una respuesta normal (ej. pregunta de envío),
# sin crear orden. Gateado a codigo_postal no vacío. Va al final de la ruta normal (id 50).
sub_cp_save = f24_save_cp_module(50, 3500, 0, parse_module_id=8)
sub_cp_save["filter"] = {"name": "codigo_postal presente",
                         "conditions": [[{"a": "{{8.codigo_postal}}", "o": "text:notequal", "b": ""}]]}

sub_order_send = ghl_send_module_from_claude(41, 2900, 300, parse_module_id=8)
sub_order_send["filter"] = {"name": "action == create_order",
                            "conditions": [[{"a": "{{8.action}}", "o": "text:equal", "b": "create_order"}]]}
sub_order_create = f24_process_order_module(42, 3100, 300, parse_module_id=8)
sub_order_link = ghl_send_payment_link_module(43, 3300, 300, order_http_module_id=42)
sub_order_ds = datastore_add_claude(44, 3500, 300, parse_module_id=8, is_order=True)

# Sub-route de HANDOFF: email al equipo + tag GHL cuando action es escalate/human_handoff.
# Email validado en prod. Tag con body via data structure (NO raw) + onerror (best-effort).
sub_handoff_email = team_email_module(45, 2900, 600)   # lleva el ESCALATE_FILTER (gate de la sub-route)
sub_handoff_tag = ghl_tag_handoff_module(46, 3150, 600)
sub_handoff_call_tag = ghl_tag_call_module(49, 3400, 600)  # tag 'pidio-llamada' solo si fue callback R32

# Sub-route de NOMBRE: guarda el firstName real en GHL cuando el bot capturó customer_name.
# Ruta propia (independiente de action/CP) — corre en cualquier acción si hay customer_name.
sub_name_save = f24_save_name_module(51, 2900, 850, parse_module_id=8)
sub_name_save["filter"] = {"name": "customer_name presente",
                           "conditions": [[{"a": "{{8.customer_name}}", "o": "text:notequal", "b": ""}]]}

# Sub-route de COTIZACIÓN DE ENVÍO: cuando action=quote_shipping, cotiza la tarifa real (Skydropx)
# por CP + SKUs y manda el `mensaje` con el monto al cliente. Reemplaza el escalate por costo de
# envío. El puente corto SIN monto ("Déjame checar el envío...") ya lo mandó la ruta normal (que
# corre para toda action != create_order), así el cliente ve "checando..." y luego la tarifa real.
sub_quote_http = f24_quote_shipping_module(52, 2900, 1100, parse_module_id=8)
sub_quote_http["filter"] = {"name": "action == quote_shipping",
                            "conditions": [[{"a": "{{8.action}}", "o": "text:equal", "b": "quote_shipping"}]]}
sub_quote_send = ghl_send_quote_message_module(53, 3150, 1100, quote_http_module_id=52)

# Sub-route OPP-TRACK: crea/avanza la oportunidad del contacto en "Ventas Whatsapp" en CADA turno
# atendido (ruta SIN filtro → siempre corre). Reconstruye la creación de opps que murió ~19-jun.
sub_opp_track = f24_opp_track_module(54, 2900, 1350, parse_module_id=8)

# Sub-route AGENDA DE LLAMADA (2 acciones):
#  - get_call_slots → consulta la agenda REAL del asesor (round-robin) y ofrece los horarios libres.
#  - book_call      → agenda la cita al horario que eligió el cliente (call_choice = su mensaje).
# El `mensaje` del EF (horarios o confirmación) lo manda el módulo _send al cliente. El puente corto
# ("Déjame ver los horarios..." / "Va, te la agendo") ya lo mandó la ruta normal (action != create_order).
sub_book_slots = f24_book_appointment_module(60, 2900, 1500, mode="slots", err_module_id=96)
sub_book_slots["filter"] = {"name": "action == get_call_slots",
                            "conditions": [[{"a": "{{8.action}}", "o": "text:equal", "b": "get_call_slots"}]]}
sub_book_slots_send = ghl_send_quote_message_module(61, 3150, 1500, quote_http_module_id=60)

sub_book_call = f24_book_appointment_module(62, 2900, 1650, mode="book", err_module_id=97)
sub_book_call["filter"] = {"name": "action == book_call",
                           "conditions": [[{"a": "{{8.action}}", "o": "text:equal", "b": "book_call"}]]}
sub_book_call_send = ghl_send_quote_message_module(63, 3150, 1650, quote_http_module_id=62)

post_parse_router = {
    "id": 40, "module": "builtin:BasicRouter", "version": 1, "mapper": None,
    "metadata": {"designer": {"x": 2650, "y": 150}},
    "routes": [
        {"flow": [sub_normal_send, sub_normal_ds, sub_cp_save]},
        {"flow": [sub_order_send, sub_order_create, sub_order_link, sub_order_ds]},
        {"flow": [sub_handoff_email, sub_handoff_tag, sub_handoff_call_tag]},
        {"flow": [sub_name_save]},
        {"flow": [sub_quote_http, sub_quote_send]},
        {"flow": [sub_book_slots, sub_book_slots_send]},
        {"flow": [sub_book_call, sub_book_call_send]},
        {"flow": [sub_opp_track]},
    ],
}

# Route C: humano staff detectado -> mutear 24h + escribir tag 'bot-pausado' (visible en inbox).
# El tag lo retira el cron de follow-ups cuando bot_muted_until expira. route_c_tag va encadenado
# después del mute (sin filtro propio): solo corre si route_c_mute corrió (su filtro pasó).
route_c_mute = datastore_mute_module(25, 1800, 450, eval_module_id=24)
route_c_mute["filter"] = {"name": "Humano respondio -> mutear bot 24h + tag",
                          "conditions": [[{"a": "{{24.is_human_active}}", "o": "text:equal", "b": "true"}, is_latest_cond]]}
route_c_tag = ghl_tag_pause_module(47, 2050, 450)

router_module = {
    "id": 4, "module": "builtin:BasicRouter", "version": 1, "mapper": None,
    "filter": {"name": f"NO tiene tag '{PAUSE_TAG}'", "conditions": [[PAUSE_CONDITION_PRE_ROUTER]]},
    "metadata": {"designer": {"x": 1650, "y": 0}},
    "routes": [
        {"flow": [route_a_ghl, route_a_datastore]},
        {"flow": [route_b_customer_ctx, route_b_setvars, route_b_anthropic, route_b_parse, post_parse_router]},
        {"flow": [route_c_mute, route_c_tag]},
    ],
}

blueprint = {
    "name": "Ferre24 AI Bot — WhatsApp",
    "flow": [webhook_module, datastore_get_module,
             buf_my_ts, buf_write, buf_sleep, buf_reget,
             ghl_get_module, parse_contact_module,
             search_conv_module, list_msgs_module, iter_msgs_module, agg_human_module,
             iter_transcript, agg_transcript,
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
