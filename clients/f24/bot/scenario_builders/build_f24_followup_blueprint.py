#!/usr/bin/env python3
"""Build del scenario de FOLLOW-UPS de F24 (cron) — Feature E.  [B-lite 2026-06-16]

Corre cada ~10 min. Escanea el datastore de conversaciones (104408) y, por cada contacto que
se quedó callado, avanza UNA etapa del ladder (nunca salta) según el tiempo desde el último
mensaje del propio ladder (pacing relativo). Requisito de Gibran: aunque un contacto lleve 20
días dormido, recibe PRIMERO d3 — y solo si no reactiva, +5d → d8, +10d → d18.

  VENTANA LIBRE (texto directo, dentro de las 24h) — rotación aleatoria entre 3 variantes:
    Etapa 2 = 2 h     → "¿Te quedó alguna duda? / ¿Sigues por ahí? / Por si el precio te frena..."
    Etapa 3 = ~22.5 h → "Vi que quedamos a medias..." (3 variantes)
    (Etapa 1 = 15 min ELIMINADA 2026-06-13.)

  FUERA DE VENTANA (plantilla Meta aprobada — el envío lo hace un Workflow GHL "relay"):
    Etapa 4 = Día 3   → T1 d3   (plantilla_meta_f24_reengagement_d3)
    Etapa 5 = +5 días → T2 d8   (plantilla_meta_f24_reengagement_d8)
    Etapa 6 = +10 días→ T3 d18  (plantilla_meta_f24_reengagement_d18)

ARQUITECTURA B-lite (2026-06-16): la API pública de GHL NO puede mandar estas plantillas
(probado: templateId con id Meta = "not found"; viven en phone-system/whatsapp, solo UI/Workflow).
→ Para etapas 4-6 este cron NO manda mensaje: solo PONE el tag `f24-send-d3|d8|d18` en el
contacto (POST /contacts/{id}/tags). Un Workflow GHL "relay" (trigger: tag → Send WhatsApp
Template → quita el tag) hace el envío real. Make = cerebro; GHL = brazo.

LADDER (orden, sin etapa 1): 2 → 3 → 4 → 5 → 6.
  next_stage = la siguiente etapa después de followup_stage, con clamp:
    - fs >= 4            → next = fs + 1            (ladder de plantillas)
    - fuera de ventana   → next = 4                 (dormido >24h entra DIRECTO en d3, nunca 5/6)
    - dentro de ventana  → next = (fs<2 ? 2 : fs+1) (ladder de texto: 2, 3, luego 4)
  Elegible si: anchor más viejo que el gap del next_stage, y next > followup_stage, y next <= MAX.
  anchor = max(lastMessageAt, followup_last_at)  (pacing relativo al último mensaje del ladder).

HARD STOP: el cap next<=6 ya impide más envíos tras d18 (no se necesita tag extra).
El bot principal resetea followup_stage=0 (+ lastMessageAt=now) en cada inbound → reactivación.

PENDIENTE go-live (NO encender hasta tener):
  1) los 3 Workflows relay creados en GHL (tag f24-send-dN → Send Template → quita tag),
  2) throttle de goteo ~15/día (contador diario en datastore) — TODO,
  3) seed de leads NO-chat al datastore (los que nunca escribieron) — TODO,
  luego: TEMPLATES_LIVE=True + redeploy scenario 5278490.

Run:  /usr/bin/python3 build_f24_followup_blueprint.py   → /tmp/f24_followup_bp.json
"""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
F24_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
ENV_PATH = os.path.join(F24_ROOT, ".env")
OUTPUT_PATH = "/tmp/f24_followup_bp.json"

F24_DATASTORE_ID = 104408
F24_LOCATION_ID = "HNuSoIl2aCXP2DXEdMVZ"
GHL_SEND_DATASTRUCTURE_ID = 342904  # body POST /conversations/messages (type/contactId/message)
GHL_TAGS_DATASTRUCTURE_ID = 395040  # body {tags:[...]} para POST/DELETE /contacts/{id}/tags
PAUSE_TAG = "bot-pausado"

# Máxima etapa que se avanza. 6 = ladder completo (texto 2-3 + plantillas 4-6).
FOLLOWUP_MAX_STAGE = 6

# Switch maestro de plantillas. MIENTRAS sea False, el cron NUNCA pone tags f24-send-dN
# (solo corre el ladder de texto 2-3). Poner True SOLO cuando: relays GHL listos + throttle
# + seed no-chat. Evita que se acumulen tags y al crear los relays se disparen todos de golpe.
TEMPLATES_LIVE = True

# Plantillas Meta aprobadas (ids reales del backend GHL phone-system/whatsapp). Solo referencia
# documental — el envío lo hace el Workflow relay por nombre de plantilla; aquí solo ponemos el tag.
TEMPLATE_TAGS = {4: "f24-send-d3", 5: "f24-send-d8", 6: "f24-send-d18"}
TEMPLATE_IDS = {4: "857068617015027", 5: "1656192009844928", 6: "2782252138818935"}

# Ventana WhatsApp (min). Si el último mensaje es más viejo que esto, el texto libre ya no
# se puede mandar → el contacto entra directo al ladder de plantillas (d3).
WINDOW_MIN = 1440  # 24 h

# Gap relativo (min desde anchor) para AVANZAR a cada etapa. Pacing pedido por Gibran:
#   2: 2h · 3: ~+20h (≈22.5h total para fresh) · 4 (d3): 24h · 5 (d8): +5 días · 6 (d18): +10 días.
STEP_GAP = {2: 120, 3: 1230, 4: 1440, 5: 7200, 6: 14400}

NUDGES = {
    2: [
        "¿Te quedó alguna duda sobre specs, meses sin intereses o tiempos de entrega? Puedo asesorarte sin compromiso — solo pregunta.",
        "¿Sigues por ahí? A veces la decisión no es fácil cuando hay varias opciones. Si quieres te ayudo a comparar o te paso el precio exacto del equipo que viste.",
        "Por si te lo preguntas: tenemos meses sin intereses en varios equipos. Si el precio es lo que te frena, puedo mostrarte cómo queda con el plan que más te convenga. ¿Le buscamos?",
    ],
    3: [
        "Hola, vi que quedamos a media conversación. ¿Sigues buscando equipo? Dime qué necesitas y le seguimos. 🔧",
        "¿Sigues por ahí? Quedamos a medias con tu cotización — si tienes dudas o quieres retomar, aquí ando.",
        "Hola, veo que nos quedamos sin cerrar tu consulta. ¿Aún necesitas equipo o maquinaria? Con gusto te ayudo a cotizar. 🛠️",
    ],
}


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


GHL_TOKEN = _read_env(ENV_PATH, "GHL_API_KEY", "__PENDING__")

# ---- Módulo 1: SearchRecord (emite cada registro del datastore) ----
search_records = {
    "id": 1, "module": "datastore:SearchRecord", "version": 1,
    "parameters": {"datastore": F24_DATASTORE_ID},
    "mapper": {"filter": [[{"a": "contactId", "o": "text:notequal", "b": "__none__"}]]},
    "metadata": {"designer": {"x": 0, "y": 0}},
}

# ---- Módulo 2: SetVariables base — anchor + muted_ok + pause_expired + nudge_roll ----
# OJO (memoria feedback): NO se puede auto-referenciar una variable dentro del mismo SetVariables.
# Por eso anchor va aquí y next_stage/due_ok van en módulos posteriores (10, 11).
anchor_expr = (
    "{{if(ifempty(1.data.followup_last_at; \"\") = \"\"; 1.data.lastMessageAt; "
    "if(parseDate(1.data.followup_last_at) > parseDate(1.data.lastMessageAt); "
    "1.data.followup_last_at; 1.data.lastMessageAt))}}"
)
eval_mod = {
    "id": 2, "module": "util:SetVariables", "version": 1, "parameters": {},
    "mapper": {"variables": [
        {"name": "anchor", "value": anchor_expr},
        {"name": "muted_ok", "value": (
            "{{if((ifempty(1.data.bot_muted_until; \"\") = \"\") || (parseDate(1.data.bot_muted_until) <= now); \"true\"; \"false\")}}")},
        {"name": "pause_expired", "value": (
            "{{if((1.data.muted_by = \"human\") && (ifempty(1.data.bot_muted_until; \"\") != \"\") "
            "&& (parseDate(1.data.bot_muted_until) <= now); \"true\"; \"false\")}}")},
        {"name": "nudge_roll", "value": (
            "{{if(parseNumber(substring(formatDate(now; \"x\"); 12; 13)) <= 3; 0; "
            "if(parseNumber(substring(formatDate(now; \"x\"); 12; 13)) <= 6; 1; 2))}}")},
    ], "scope": "roundtrip"},
    "metadata": {"designer": {"x": 300, "y": 0}, "restore": {}},
}

# ---- Módulo 10: SetVariables — next_stage (avanzar UNA etapa, clamp dormido→d3) ----
# fs = followup_stage actual (0 si vacío). within = anchor más nuevo que 24h.
next_stage_expr = (
    "{{if(ifempty(1.data.followup_stage; 0) >= 4; ifempty(1.data.followup_stage; 0) + 1; "
    "if(parseDate(2.anchor) <= addMinutes(now; -" + str(WINDOW_MIN) + "); 4; "
    "if(ifempty(1.data.followup_stage; 0) < 2; 2; ifempty(1.data.followup_stage; 0) + 1)))}}"
)
next_stage_mod = {
    "id": 10, "module": "util:SetVariables", "version": 1, "parameters": {},
    "mapper": {"variables": [{"name": "next_stage", "value": next_stage_expr}], "scope": "roundtrip"},
    "metadata": {"designer": {"x": 450, "y": -150}, "restore": {}},
}

# ---- Módulo 11: SetVariables — due_ok (anchor más viejo que el gap del next_stage) ----
# Sin aritmética en IML: nested-if con addMinutes literal por etapa (patrón probado).
def due_ok_expr():
    parts = []
    for st in (2, 3, 4, 5, 6):
        g = STEP_GAP[st]
        parts.append("if(10.next_stage = " + str(st) + "; "
                      "if(parseDate(2.anchor) <= addMinutes(now; -" + str(g) + "); \"true\"; \"false\"); ")
    return "{{" + "".join(parts) + "\"false\"" + (")" * 5) + "}}"
due_ok_mod = {
    "id": 11, "module": "util:SetVariables", "version": 1, "parameters": {},
    "mapper": {"variables": [{"name": "due_ok", "value": due_ok_expr()}], "scope": "roundtrip"},
    "metadata": {"designer": {"x": 600, "y": -150}, "restore": {}},
}

# nudge_expr (texto) — solo etapas 2 y 3, indexado por next_stage + nudge_roll.
def rotation_expr_for_stage(stage):
    msgs = NUDGES[stage]
    return ("if(2.nudge_roll = 0; \"" + msgs[0] + "\"; "
            "if(2.nudge_roll = 1; \"" + msgs[1] + "\"; \"" + msgs[2] + "\"))")
nudge_expr = "{{" + (
    "if(10.next_stage = 2; " + rotation_expr_for_stage(2) + "; "
    "if(10.next_stage = 3; " + rotation_expr_for_stage(3) + "; \"\"))"
) + "}}"

# tag a poner para plantillas — depende de next_stage (4→d3, 5→d8, 6→d18).
template_tag_expr = (
    "{{if(10.next_stage = 4; \"" + TEMPLATE_TAGS[4] + "\"; "
    "if(10.next_stage = 5; \"" + TEMPLATE_TAGS[5] + "\"; \"" + TEMPLATE_TAGS[6] + "\"))}}"
)

# Teléfonos internos / equipo / prueba — el bot NUNCA les hace follow-up (texto ni plantilla).
# Gibran 2026-06-17: Sergio (cliente) y Pedro están en el datastore; sin esto el cerebro
# les mandaría d3 solo. Se filtran por phone en AMBAS rutas de envío.
EXCLUDE_PHONES = [
    "+5213351199004",   # gibran
    "+5213511463770",   # pedro lopez
    "+5213541013640",   # sergio jds (cliente)
    "+16465894168",     # whatsapp business (sistema/prueba)
    "+447710173736",    # UK sin nombre (prueba)
]

# Filtro común de elegibilidad (texto y plantilla lo comparten en su 1er módulo).
def eligible_conditions(extra):
    base = [
        {"a": "{{10.next_stage}}", "o": "number:greater", "b": "{{ifempty(1.data.followup_stage; 0)}}"},
        {"a": "{{10.next_stage}}", "o": "number:lessorequal", "b": str(FOLLOWUP_MAX_STAGE)},
        {"a": "{{11.due_ok}}", "o": "text:equal", "b": "true"},
        {"a": "{{2.muted_ok}}", "o": "text:equal", "b": "true"},
    ]
    excl = [{"a": "{{1.data.phone}}", "o": "text:notequal", "b": p} for p in EXCLUDE_PHONES]
    return [base + excl + extra]

# ---- Módulo 3: GHL get contact (chequear tag bot-pausado) — usado por ambas ramas de envío ----
def ghl_get_mod(mod_id, x, route_extra):
    return {
        "id": mod_id, "module": "http:MakeRequest", "version": 4,
        "parameters": {"authenticationType": "noAuth"},
        "mapper": {
            "url": "https://services.leadconnectorhq.com/contacts/{{1.data.contactId}}", "method": "get",
            "headers": [
                {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
                {"name": "Version", "value": "2021-07-28"},
                {"name": "Accept", "value": "application/json"},
            ],
            "timeout": 30, "parseResponse": True, "stopOnHttpError": False,
            "requestCompressedContent": True, "shareCookies": False, "allowRedirects": True,
        },
        "metadata": {"designer": {"x": x, "y": 0}},
        "filter": {"name": "elegible", "conditions": eligible_conditions(route_extra)},
    }

# ---- Rama TEXTO (next 2-3): GHL send nudge libre ----
ghl_get_text = ghl_get_mod(3, 700, [{"a": "{{10.next_stage}}", "o": "number:lessorequal", "b": "3"}])
ghl_send_text = {
    "id": 4, "module": "http:MakeRequest", "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "mapper": {
        "url": "https://services.leadconnectorhq.com/conversations/messages", "method": "post",
        "headers": [
            {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
            {"name": "Version", "value": "2021-07-28"},
            {"name": "Content-Type", "value": "application/json"},
            {"name": "Accept", "value": "application/json"},
        ],
        "contentType": "json", "inputMethod": "dataStructure",
        "bodyDataStructure": GHL_SEND_DATASTRUCTURE_ID,
        "dataStructureBodyContent": {"type": "WhatsApp", "contactId": "{{1.data.contactId}}", "message": nudge_expr},
        "timeout": 60, "parseResponse": True, "stopOnHttpError": False,
        "requestCompressedContent": True, "shareCookies": False, "allowRedirects": True,
    },
    "metadata": {"designer": {"x": 1000, "y": 0}},
    "filter": {"name": "no pausado", "conditions": [[
        {"a": "{{join(3.data.contact.tags; \"|\")}}", "o": "text:notcontain", "b": "bot-pausado"},
    ]]},
}
update_text = {
    "id": 5, "module": "datastore:UpdateRecord", "version": 1,
    "parameters": {"datastore": F24_DATASTORE_ID},
    "mapper": {"key": "{{1.key}}", "upsert": False, "overwriteArrays": False, "data": {
        "followup_stage": "{{10.next_stage}}", "followup_last_at": "{{now}}",
    }},
    "metadata": {"designer": {"x": 1300, "y": 0}},
}

# ---- Rama PLANTILLA (next 4-6): pone tag f24-send-dN (el Workflow relay manda la plantilla) ----
# Gated por TEMPLATES_LIVE: si False, el filtro nunca pasa (cero tags hasta encender).
templ_live_extra = [
    {"a": "{{10.next_stage}}", "o": "number:greaterorequal", "b": "4"},
    {"a": ("true" if TEMPLATES_LIVE else "false"), "o": "text:equal", "b": "true"},
]
ghl_get_tpl = ghl_get_mod(12, 700, templ_live_extra)
add_template_tag = {
    "id": 13, "module": "http:MakeRequest", "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "mapper": {
        "url": "https://services.leadconnectorhq.com/contacts/{{1.data.contactId}}/tags", "method": "post",
        "headers": [
            {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
            {"name": "Version", "value": "2021-07-28"},
            {"name": "Content-Type", "value": "application/json"},
            {"name": "Accept", "value": "application/json"},
        ],
        "contentType": "json", "inputMethod": "dataStructure",
        "bodyDataStructure": GHL_TAGS_DATASTRUCTURE_ID,
        "dataStructureBodyContent": {"tags": [template_tag_expr]},
        "timeout": 30, "parseResponse": True, "stopOnHttpError": False,
        "requestCompressedContent": True, "shareCookies": False, "allowRedirects": True,
    },
    "metadata": {"designer": {"x": 1000, "y": 150}},
    "filter": {"name": "no pausado", "conditions": [[
        {"a": "{{join(12.data.contact.tags; \"|\")}}", "o": "text:notcontain", "b": "bot-pausado"},
    ]]},
}
update_tpl = {
    "id": 14, "module": "datastore:UpdateRecord", "version": 1,
    "parameters": {"datastore": F24_DATASTORE_ID},
    "mapper": {"key": "{{1.key}}", "upsert": False, "overwriteArrays": False, "data": {
        "followup_stage": "{{10.next_stage}}", "followup_last_at": "{{now}}",
    }},
    "metadata": {"designer": {"x": 1300, "y": 150}},
}

# ---- Rama B: retira 'bot-pausado' cuando el mute de 24h expiró ----
remove_pause_tag = {
    "id": 7, "module": "http:MakeRequest", "version": 4,
    "parameters": {"authenticationType": "noAuth"},
    "mapper": {
        "url": "https://services.leadconnectorhq.com/contacts/{{1.data.contactId}}/tags", "method": "delete",
        "headers": [
            {"name": "Authorization", "value": f"Bearer {GHL_TOKEN}"},
            {"name": "Version", "value": "2021-07-28"},
            {"name": "Content-Type", "value": "application/json"},
            {"name": "Accept", "value": "application/json"},
        ],
        "contentType": "json", "inputMethod": "dataStructure",
        "bodyDataStructure": GHL_TAGS_DATASTRUCTURE_ID,
        "dataStructureBodyContent": {"tags": [PAUSE_TAG]},
        "timeout": 30, "parseResponse": True, "stopOnHttpError": False,
        "requestCompressedContent": True, "shareCookies": False, "allowRedirects": True,
    },
    "metadata": {"designer": {"x": 700, "y": 300}},
    "filter": {"name": "pausa de 24h expirada", "conditions": [[
        {"a": "{{2.pause_expired}}", "o": "text:equal", "b": "true"},
    ]]},
    "onerror": [{"id": 9, "module": "builtin:Resume", "version": 1,
                 "mapper": {"ok": True}, "metadata": {"designer": {"x": 700, "y": 500}}}],
}
clear_mute_rec = {
    "id": 8, "module": "datastore:UpdateRecord", "version": 1,
    "parameters": {"datastore": F24_DATASTORE_ID},
    "mapper": {"key": "{{1.key}}", "upsert": False, "overwriteArrays": False, "data": {
        "muted_by": "", "bot_muted_until": "",
    }},
    "metadata": {"designer": {"x": 1000, "y": 300}},
}

# Router: Route A (texto 2-3), Route A2 (plantilla 4-6 via tag), Route B (retiro pausa).
router = {
    "id": 6, "module": "builtin:BasicRouter", "version": 1, "mapper": None,
    "metadata": {"designer": {"x": 750, "y": 0}},
    "routes": [
        {"flow": [ghl_get_text, ghl_send_text, update_text]},
        {"flow": [ghl_get_tpl, add_template_tag, update_tpl]},
        {"flow": [remove_pause_tag, clear_mute_rec]},
    ],
}

blueprint = {
    "name": "Ferre24 Bot — Follow-ups (cron)",
    "flow": [search_records, eval_mod, next_stage_mod, due_ok_mod, router],
    "metadata": {
        "instant": False, "version": 1,
        "scenario": {"roundtrips": 1, "maxErrors": 100, "autoCommit": True,
                     "autoCommitTriggerLast": True, "sequential": False, "confidential": False,
                     "dataloss": False, "dlq": False, "freshVariables": False},
        "designer": {"orphans": []},
    },
    "scheduling": {"type": "indefinitely", "interval": 600},
    "interface": {"input": [], "output": []},
}

if __name__ == "__main__":
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Output: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")
    print(f"FOLLOWUP_MAX_STAGE={FOLLOWUP_MAX_STAGE}  TEMPLATES_LIVE={TEMPLATES_LIVE}")
    print("Ladder (avanza 1 etapa a la vez, dormido>24h entra en d3):")
    labels = {2: "2h texto (rotación)", 3: "~22.5h texto (rotación)",
              4: "Día 3 → tag f24-send-d3 → relay GHL", 5: "+5d → tag f24-send-d8", 6: "+10d → tag f24-send-d18"}
    for s in (2, 3, 4, 5, 6):
        print(f"  {s}: {labels[s]}  (gap {STEP_GAP[s]} min)")
    if not TEMPLATES_LIVE:
        print("  [GUARD] TEMPLATES_LIVE=False → NO se ponen tags de plantilla todavía (solo texto 2-3).")
    print("Pendiente go-live: relays GHL + throttle ~15/día + seed no-chat → TEMPLATES_LIVE=True + redeploy 5278490.")
    print(f"GHL token: {'OK' if not GHL_TOKEN.startswith('__PENDING') else 'PENDIENTE'}")
