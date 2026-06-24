#!/usr/bin/env python3
"""Test OFFLINE del cerebro del bot F24 — corre el system prompt vivo contra guiones
de prueba via Anthropic API (mismo modelo/temp/prefill que el scenario Make 5258612/5381174).
NO toca Make ni WhatsApp: replica el contrato de entrada (contexto + historial + msg nuevo).

  PYTHONUTF8=1 py test_f24_bot_brain.py

Lee el system prompt del blueprint DEV (v4.6) para probar EXACTO lo desplegado en DEV.
ANTHROPIC_API_KEY del F24/.env.
"""
import os, io, json, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
BP = HERE / "_BLUEPRINTS" / "f24_bot_v4.6_qa-fixes_dev_2026-06-17.json"
ENV = HERE.parents[1] / ".env"          # F24/.env
MODEL = "claude-haiku-4-5-20251001"

def read_env(path, key):
    for l in io.open(path, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith(key + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{key} no encontrado en {path}")

def extract_system(bp_path):
    bp = json.load(io.open(bp_path, encoding="utf-8"))
    found = []
    def walk(mods):
        for m in mods:
            ds = (m.get("mapper", {}) or {}).get("dataStructureBodyContent")
            if ds and isinstance(ds.get("system"), list):
                found.append(ds["system"][0]["text"])
            for r in m.get("routes", []) or []:
                walk(r.get("flow", []))
    walk(bp["flow"])
    return found[0]

SYSTEM = extract_system(BP)
KEY = read_env(ENV, "ANTHROPIC_API_KEY")

def build_user_content(ctx, history, new_msg):
    """history = lista de (quien, texto) MAS RECIENTE PRIMERO."""
    hist = "\n".join(f"{q}: {t}" for q, t in history) or "(primera interaccion, sin historial previo)"
    return (
        "[CONTEXTO DEL CLIENTE — datos reales traidos de GHL. USAR ESTO, NUNCA INVENTAR.]\n"
        f"Nombre: {ctx.get('name','(sin nombre)')}\n"
        f"Email (para link de pago / cotizacion): {ctx.get('email','(sin email)')}\n"
        f"Compras totales (purchase_count): {ctx.get('pc','0')}\n"
        "Ultima compra: productos [ninguno] por $0\n"
        "Numero de pedido: (sin numero)\n"
        "Link de seguimiento (tracking_url): (sin link de seguimiento)\n\n"
        "[CONVERSACION RECIENTE REAL DE WHATSAPP — los ultimos mensajes, MAS RECIENTE PRIMERO.]\n"
        f"{hist}\n\n"
        "[MENSAJE NUEVO DEL CLIENTE A RESPONDER]\n"
        f"{new_msg}"
    )

def call_bot(user_content):
    body = {
        "model": MODEL, "max_tokens": 2048, "temperature": 0.3,
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_content},
                     {"role": "assistant", "content": "{"}],
    }
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                 data=json.dumps(body).encode(), method="POST")
    req.add_header("x-api-key", KEY)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    raw = urllib.request.urlopen(req, timeout=60).read().decode()
    txt = json.loads(raw)["content"][0]["text"]
    txt = "{" + txt
    txt = txt.replace("```json", "").replace("```", "").strip()
    return json.loads(txt)

def show(label, r):
    print(f"\n--- {label} ---")
    print("  action :", r.get("action"), "| intent:", r.get("intent"), "| quoted:", r.get("quoted"))
    for i, m in enumerate(r.get("messages", [])):
        print(f"  msg{i+1} : {m}")
    if r.get("products_mentioned"): print("  prods  :", r["products_mentioned"])

# ============ PROBES ============
print("System prompt:", len(SYSTEM), "chars  | blueprint:", BP.name)

# PROBE A — spec dura (200A) insistida 2 veces → debe escalar, NO repetir el pitch de 120A
ctxA = {"name": "Juarez", "pc": "0"}
a1 = call_bot(build_user_content(ctxA, [], "Quiero una soldadora inversora de 200 amperes"))
show("A1 pide 200A (1a vez)", a1)
histA = [("Bot", " ".join(a1.get("messages", []))[:400]),
         ("Cliente", "Quiero una soldadora inversora de 200 amperes")]
a2 = call_bot(build_user_content(ctxA, histA, "No, necesito de 200 amperes exactos, no de 130. ¿Tienes o no?"))
show("A2 insiste 200A (2a vez) -> ESPERADO: escalate + captura contacto", a2)

# PROBE B — dato que no tiene (origen) preguntado 2 veces → 1a responde marca, 2a escala
ctxB = {"name": "Cliente", "pc": "0"}
histB0 = [("Bot", "La Soldadora Inverter Power Hunt CENTELLA130 esta en $1,166. Te la armo?"),
          ("Cliente", "Me interesa la CENTELLA130")]
b1 = call_bot(build_user_content(ctxB, histB0, "¿De que origen es la maquina? ¿Donde se fabrica?"))
show("B1 pregunta origen (1a vez) -> ESPERADO: marca/respaldo, respond", b1)
histB1 = [("Bot", " ".join(b1.get("messages", []))[:400]),
          ("Cliente", "¿De que origen es la maquina? ¿Donde se fabrica?")] + histB0
b2 = call_bot(build_user_content(ctxB, histB1, "No me respondiste cual es la procedencia exacta, ¿de que pais es?"))
show("B2 re-pregunta origen (2a vez) -> ESPERADO: escalate + captura contacto", b2)

# PROBE C — señal de compra directa (no debe escalar, debe create_order)
ctxC = {"name": "Livier", "email": "livier@correo.com", "pc": "0"}
histC = [("Bot", "El GP9500TB cubre tu casa de 4500W. $36,949. Te lo armo?"),
         ("Cliente", "Quiero el generador para mi casa de 4500W")]
c1 = call_bot(build_user_content(ctxC, histC, "Si, lo quiero. Pasame el link para pagar con tarjeta"))
show("C1 senal de compra directa -> ESPERADO: create_order, NO escalate", c1)
print("\n[done]")
