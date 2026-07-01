#!/usr/bin/env python3
"""Comment -> DM: cumple el 'te escribimos por DM' enviando la respuesta privada real
al autor del comentario (ventana de 7 días de Meta), y lo enruta a WhatsApp donde el
bot ya vive (HC/LF). F24 dm_enabled=false (WABA baneada, sin bot de handoff).

Corre DESPUÉS de social_publish (el comentario público ya se respondió).
Estados en meta.dm_status: sent | failed | window_closed | skipped.

Uso:
  python3 social_dm.py --dry-run          # muestra qué DM mandaría, sin enviar
  python3 social_dm.py --client HC --limit 3
  python3 social_dm.py                     # envía los DMs pendientes elegibles
"""
import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import secrets, meta, store  # noqa: E402
from social_brain import load_knowledge, load_config, MODEL  # noqa: E402

DM_WINDOW_DAYS = 7


def call_claude_text(system, user, api_key):
    """Como social_brain.call_claude pero devuelve TEXTO plano (el DM no es JSON)."""
    body = {"model": MODEL, "max_tokens": 300, "system": system,
            "messages": [{"role": "user", "content": user}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", method="POST",
        data=json.dumps(body).encode(),
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.load(r)
    return "".join(b.get("text", "") for b in resp.get("content", [])).strip()

DM_SYSTEM = """Eres el asesor de {name}. Un cliente comentó en un anuncio/publicación y le \
prometimos escribirle por privado. Redacta el PRIMER mensaje directo (DM), cálido y humano, \
en español de México (trato de "tú", nunca voseo).

REGLAS:
- Máximo 2 frases cortas. Es un DM de apertura, no un catálogo.
- Referencia natural a su interés (sin copiar textual su comentario).
- NO escribas precios ni cifras (pueden estar vencidos); eso se ve al continuar.
- Termina invitando a seguir la conversación. NO incluyas links tú: el sistema agrega el de WhatsApp.
- Español impecable (ñ, tildes). Sin exceso de emojis (máx 1).

Contexto del negocio (para tono, NO para citar precios):
{knowledge}

Devuelve SOLO el texto del mensaje, sin comillas ni JSON."""


def build_dm(cfg, row, api_key, know):
    system = DM_SYSTEM.format(name=cfg["name"], knowledge=know[:6000] or "(sin catálogo)")
    user = (f"El cliente comentó: \"{row.get('body') or ''}\" "
            f"en {row.get('ad_name') or row['channel']}. Redacta el DM de apertura.")
    try:
        text = call_claude_text(system, user, api_key)
    except Exception:
        text = ""
    text = (text or "").strip().strip('"')
    if not text:
        text = "¡Hola! Vimos tu comentario y con gusto te ayudamos."
    wa = cfg.get("whatsapp")
    if wa:
        text += f"\n\nContinuemos por WhatsApp para atenderte al instante 👇\n{wa}"
    return text


def eligible(row, cfg):
    if not cfg.get("dm_enabled"):
        return False, "cliente sin dm_enabled"
    if row["type"] != "comment":
        return False, "no es comentario"
    st = (row.get("meta") or {}).get("dm_status")
    if st in ("sent", "failed", "window_closed", "skipped"):
        return False, f"dm ya {st}"
    age = row.get("age_days")
    if age is not None and age > DM_WINDOW_DAYS:
        return False, "window_closed"
    return True, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default="all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()

    conf = load_config()
    api_key = secrets.anthropic_key()
    clients = list(conf["clients"]) if args.client == "all" else [args.client.upper()]

    # comentarios con respuesta pública ya publicada
    rows = store.fetch(status="published")
    know_cache, page_tokens = {}, {}
    sent = failed = 0

    for row in rows:
        code = row["client"]
        if code not in clients:
            continue
        cfg = conf["clients"].get(code)
        if not cfg:
            continue
        ok, why = eligible(row, cfg)
        if not ok:
            if why == "window_closed":  # marca para no reintentar
                if not args.dry_run:
                    store.update(row["external_id"],
                                 {"meta": {**(row.get("meta") or {}), "dm_status": "window_closed"}})
            continue

        if code not in know_cache:
            know_cache[code] = load_knowledge(cfg["knowledge"]) if cfg.get("knowledge") else ""
        dm = build_dm(cfg, row, api_key, know_cache[code])
        print(f"\n[{code}] {row['channel']} · {(row.get('body') or '')[:35]!r} ({row.get('age_days')}d)")
        print(f"    DM -> {dm!r}")

        if args.dry_run:
            continue
        try:
            if code not in page_tokens:
                utok = secrets.meta_token(conf["token_refs"][cfg["token_ref"]])
                page_tokens[code] = meta.page_access_token(cfg["page_id"], utok)
            res = meta.send_private_reply(row["channel"], cfg["page_id"], cfg.get("ig_id"),
                                          row["external_id"], dm, page_tokens[code])
            store.update(row["external_id"], {"meta": {**(row.get("meta") or {}),
                         "dm_status": "sent", "dm_message": dm,
                         "dm_reply_id": res.get("message_id") or res.get("id")}})
            print(f"    -> DM ENVIADO ({res.get('message_id') or res.get('id')})")
            sent += 1
        except Exception as e:
            store.update(row["external_id"], {"meta": {**(row.get("meta") or {}),
                         "dm_status": "failed", "dm_message": dm, "dm_error": str(e)[:250]}})
            print(f"    -> ERROR: {e}")
            failed += 1

    print(f"\nDMs enviados: {sent}  Fallidos: {failed}" + ("  [DRY-RUN]" if args.dry_run else ""))


if __name__ == "__main__":
    main()
