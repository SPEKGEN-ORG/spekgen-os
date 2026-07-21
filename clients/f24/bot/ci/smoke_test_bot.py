#!/usr/bin/env python3
"""smoke_test_bot.py <dev|prod> — prueba VIVA end-to-end del bot F24 en Make.

Qué hace:
  1. Crea un contacto GHL efímero (firstName "ZZ Smoke", tel sintético, tag 'smoke-test').
  2. POSTea un mensaje de compra al webhook del scenario target (dev o prod).
  3. Espera a que el bot conteste: busca un mensaje OUTBOUND en la conversación GHL del
     contacto (en un contacto recién creado, CUALQUIER outbound = el bot respondió).
  4. Borra el contacto (DELETE /contacts/{id} — funciona, HTTP 200).
  5. exit 0 = el bot respondió · exit 1 = no respondió / error.

Japan-proof: sólo stdlib (urllib), corre en GitHub Actions. El token GHL viene de la env
var F24_GHL_API_KEY (secret en CI) o GHL_API_KEY; como último recurso, de un .env vía --env-file.

Uso:
  python3 ci/smoke_test_bot.py prod
  python3 ci/smoke_test_bot.py dev --env-file "/ruta/F24- FERRE24/.env"
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GHL_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"
LOCATION_ID = "HNuSoIl2aCXP2DXEdMVZ"  # Ferre24

HOOKS = {
    "prod": "https://hook.us2.make.com/kuyq4cksp5cy6pg9ka4mh0uriorti9o6",  # scenario 5258612 (LIVE)
    "dev": "https://hook.us2.make.com/wcmd3b9697q5t4kkv2e5v1fj8oztpp6x",   # scenario 5381174 (aislado)
}

# Datastore del bot F24 en Make. El bot escribe aqui un registro por contacto;
# el smoke tiene que borrar el suyo o se acumula (ver delete_datastore_record).
MAKE_BASE = "https://us2.make.com/api/v2"
MAKE_DATASTORE_ID = 104408

TEST_MESSAGE = "hola, tienen generadores?"
POLL_TOTAL_SECONDS = 75   # ventana total de espera por la respuesta del bot
POLL_INTERVAL = 5         # cada cuánto se sondea GHL


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _read_env_file(path: str, key: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None


def get_token(env_file: str | None) -> str:
    tok = os.environ.get("F24_GHL_API_KEY") or os.environ.get("GHL_API_KEY")
    if not tok and env_file:
        tok = _read_env_file(env_file, "GHL_API_KEY")
    if not tok:
        log("ERROR: falta el token GHL (F24_GHL_API_KEY / GHL_API_KEY / --env-file).")
        sys.exit(2)
    return tok


def ghl_request(method: str, path: str, token: str, body: dict | None = None, query: dict | None = None):
    url = GHL_BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Version", GHL_VERSION)
    req.add_header("Accept", "application/json")
    # GHL está detrás de Cloudflare: el UA default de urllib (python-urllib) dispara el error
    # 1010 "browser_signature_banned". Un UA de navegador normal pasa. (Ver memoria apps_script UA.)
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return e.code, parsed
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}


def post_hook(hook_url: str, payload: dict) -> int:
    req = urllib.request.Request(hook_url, data=json.dumps(payload).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001
        log(f"ERROR posteando al webhook: {e}")
        return 0


def create_test_contact(token: str) -> str | None:
    suffix = str(int(time.time()))[-8:]
    body = {
        "locationId": LOCATION_ID,
        "firstName": "ZZ Smoke",
        "lastName": f"CI-{suffix}",
        "phone": f"+52155{suffix}",   # número sintético, no entrega WhatsApp real (no importa)
        "tags": ["smoke-test"],
        "source": "ci-smoke-test",
    }
    status, data = ghl_request("POST", "/contacts/upsert", token, body=body)
    contact = data.get("contact") or data
    cid = contact.get("id") if isinstance(contact, dict) else None
    if status in (200, 201) and cid:
        log(f"Contacto de prueba creado: {cid} (tel {body['phone']})")
        return cid
    log(f"ERROR creando contacto (HTTP {status}): {json.dumps(data)[:400]}")
    return None


def find_outbound_reply(token: str, contact_id: str) -> bool:
    """Busca un mensaje OUTBOUND en la conversación del contacto. True = el bot respondió."""
    status, data = ghl_request(
        "GET", "/conversations/search", token,
        query={"locationId": LOCATION_ID, "contactId": contact_id},
    )
    if status != 200:
        return False
    convs = data.get("conversations") or []
    for conv in convs:
        conv_id = conv.get("id")
        if not conv_id:
            continue
        st, md = ghl_request("GET", f"/conversations/{conv_id}/messages", token)
        if st != 200:
            continue
        msgs = (md.get("messages") or {}).get("messages") or []
        for m in msgs:
            if (m.get("direction") == "outbound") and (m.get("body") or "").strip():
                return True
    return False


def delete_contact(token: str, contact_id: str) -> None:
    status, _ = ghl_request("DELETE", f"/contacts/{contact_id}", token)
    log(f"Contacto de prueba borrado (HTTP {status}).")


def delete_datastore_record(contact_id: str, env_file: str | None = None) -> None:
    """Borra el registro que el bot dejo en el datastore de Make.

    Sin esto el smoke filtra un huerfano por corrida: borra el contacto en GHL
    pero la fila del datastore se queda para siempre. A 2026-07-20 eso habia
    dejado 329 huerfanos "ZZ Smoke CI" de 449 registros (73%), y el cron de
    follow-ups paga 1 operacion POR REGISTRO ESCANEADO en cada corrida — o sea
    que la basura de CI se recobra 3 veces al dia, todos los dias.

    Best-effort: si no hay MAKE_API_TOKEN solo avisa y sigue. Este script valida
    que el bot responda; nunca debe fallar por la limpieza.
    """
    tok = os.environ.get("MAKE_API_TOKEN")
    if not tok and env_file:
        tok = _read_env_file(env_file, "MAKE_API_TOKEN")
    if not tok:
        log("AVISO: sin MAKE_API_TOKEN el registro del datastore queda huerfano. "
            "Agrega el secret MAKE_API_TOKEN para que CI limpie solo.")
        return
    url = f"{MAKE_BASE}/data-stores/{MAKE_DATASTORE_ID}/data"
    req = urllib.request.Request(
        url, data=json.dumps({"keys": [contact_id]}).encode(), method="DELETE"
    )
    req.add_header("Authorization", f"Token {tok}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            log(f"Registro del datastore borrado (HTTP {resp.status}).")
    except urllib.error.HTTPError as e:
        log(f"AVISO: no se pudo borrar el registro del datastore (HTTP {e.code}).")
    except Exception as e:  # noqa: BLE001 — nunca tumbar el smoke por la limpieza
        log(f"AVISO: no se pudo borrar el registro del datastore ({e}).")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in HOOKS:
        log("Uso: smoke_test_bot.py <dev|prod> [--env-file PATH]")
        return 2
    target = sys.argv[1]
    env_file = None
    if "--env-file" in sys.argv:
        env_file = sys.argv[sys.argv.index("--env-file") + 1]

    token = get_token(env_file)
    hook_url = HOOKS[target]
    log(f"=== SMOKE TEST bot F24 [{target.upper()}] ===")

    contact_id = create_test_contact(token)
    if not contact_id:
        return 1

    try:
        payload = {
            "contact_id": contact_id,
            "message": {"body": TEST_MESSAGE},
            "full_name": "ZZ Smoke CI",
            "phone": f"+52155{str(int(time.time()))[-8:]}",
        }
        code = post_hook(hook_url, payload)
        log(f"POST al webhook → HTTP {code}")
        if code not in (200, 202):
            log("ERROR: el webhook no aceptó el mensaje.")
            return 1

        deadline = time.time() + POLL_TOTAL_SECONDS
        attempt = 0
        while time.time() < deadline:
            attempt += 1
            if find_outbound_reply(token, contact_id):
                log(f"OK: el bot respondió (intento {attempt}). PASS.")
                return 0
            time.sleep(POLL_INTERVAL)
        log(f"FALLA: el bot NO respondió en {POLL_TOTAL_SECONDS}s. FAIL.")
        return 1
    finally:
        delete_contact(token, contact_id)
        delete_datastore_record(contact_id, env_file)


if __name__ == "__main__":
    sys.exit(main())
