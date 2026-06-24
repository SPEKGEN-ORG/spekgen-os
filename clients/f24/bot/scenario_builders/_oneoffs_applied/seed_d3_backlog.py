#!/usr/bin/env python3
"""Ola inicial de re-engagement d3 al backlog de F24 — con goteo.

Regla de Gibran (2026-06-17): TODOS los contactos sin seguimiento entran en d3 ahora.
NADIE salta a d8/d18 aunque por tiempo aplicara — "haz de cuenta que apenas es día 3".

Qué hace:
  - Jala todos los contactos de F24 (GHL API, paginado).
  - Filtra dormidos elegibles: tiene phone, dnd=false, NO tags
    {requiere-humano, bot-pausado, reeng-d3-sent}. (reeng-d3-sent = dedupe, no re-enviar.)
  - Goteo: procesa solo --batch N por corrida (default 15), más viejos primero (dateAdded asc).
  - Por cada uno: pone tag `f24-send-d3` (gatilla el Workflow relay → manda plantilla d3)
    + tag `reeng-d3-sent` (dedupe) y lo apunta en el ledger local.
  - Ledger: reeng_ledger.json — {contactId, name, phone, d3_sent_at} para continuar d8/d18 después.

Uso:
  /usr/bin/python3 seed_d3_backlog.py              # DRY-RUN (no manda nada, solo lista)
  /usr/bin/python3 seed_d3_backlog.py --send       # envía el batch (default 15)
  /usr/bin/python3 seed_d3_backlog.py --send --batch 10
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
F24_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
ENV_PATH = os.path.join(F24_ROOT, ".env")
LEDGER_PATH = os.path.join(SCRIPT_DIR, "reeng_ledger.json")
LOCATION_ID = "HNuSoIl2aCXP2DXEdMVZ"
BASE = "https://services.leadconnectorhq.com"
EXCLUDE_TAGS = {"requiere-humano", "bot-pausado", "reeng-d3-sent"}
SEND_TAG = "f24-send-d3"
DEDUPE_TAG = "reeng-d3-sent"

# Internos / equipo / prueba — NUNCA mandarles re-engagement (Gibran 2026-06-17).
EXCLUDE_PHONES = {
    "+5213351199004",   # gibran
    "+5213511463770",   # pedro lopez
    "+5213541013640",   # sergio jds (cliente)
    "+16465894168",     # whatsapp business (sistema/prueba US)
    "+447710173736",    # UK sin nombre (prueba)
}
EXCLUDE_NAME_SUBSTR = {"gibran", "pedro", "sergio", "whatsapp business"}


def _digits(s):
    return "".join(ch for ch in (s or "") if ch.isdigit())


EXCLUDE_DIGITS = {_digits(p) for p in EXCLUDE_PHONES}


def read_env(key, default=""):
    try:
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return default


TOKEN = read_env("GHL_API_KEY")


def api(method, path, body=None, params=None):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}", "Version": "2021-07-28",
        "Content-Type": "application/json", "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    })
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def fetch_all_contacts():
    out, cursor = [], None
    while True:
        params = {"locationId": LOCATION_ID, "limit": 100}
        if cursor:
            params["startAfterId"] = cursor
        st, d = api("GET", "/contacts/", params=params)
        if st != 200:
            print("ERROR list:", st, d); break
        batch = d.get("contacts", [])
        if not batch:
            break
        out.extend(batch)
        meta = d.get("meta", {})
        cursor = meta.get("startAfterId") or (batch[-1].get("id"))
        if len(out) >= meta.get("total", len(out)) or not meta.get("nextPageUrl"):
            break
    return out


def eligible(c):
    if not c.get("phone"):
        return False
    if c.get("dnd"):
        return False
    tags = set(t.lower() for t in (c.get("tags") or []))
    if tags & EXCLUDE_TAGS:
        return False
    if _digits(c.get("phone")) in EXCLUDE_DIGITS:
        return False
    nm = ((c.get("firstName") or "") + " " + (c.get("lastName") or "")).lower()
    if any(s in nm for s in EXCLUDE_NAME_SUBSTR):
        return False
    return True


def load_ledger():
    try:
        return json.load(open(LEDGER_PATH))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sent": []}


def main():
    send = "--send" in sys.argv
    batch = 15
    if "--batch" in sys.argv:
        batch = int(sys.argv[sys.argv.index("--batch") + 1])
    if not TOKEN:
        print("NO GHL_API_KEY"); return

    contacts = fetch_all_contacts()
    elig = [c for c in contacts if eligible(c)]
    elig.sort(key=lambda c: c.get("dateAdded", ""))  # más viejos primero
    ledger = load_ledger()
    already = {s["contactId"] for s in ledger["sent"]}
    elig = [c for c in elig if c.get("id") not in already]

    print(f"Total contactos: {len(contacts)} | elegibles (dormidos, no excluidos, no enviados): {len(elig)}")
    target = elig[:batch]
    print(f"\nBATCH a procesar ({'ENVÍO REAL' if send else 'DRY-RUN'}): {len(target)} de {len(elig)} (goteo {batch}/corrida)\n")
    for c in target:
        nm = (c.get("firstName") or "") + " " + (c.get("lastName") or "")
        print(f"  - {c.get('id')}  {nm.strip()[:28]:28}  {c.get('phone')}  alta:{c.get('dateAdded','')[:10]}")

    if not send:
        print(f"\n(DRY-RUN. Para enviar: /usr/bin/python3 seed_d3_backlog.py --send --batch {batch})")
        print(f"Quedarían {max(0, len(elig)-len(target))} para las siguientes corridas.")
        return

    print("\nEnviando d3 (tag f24-send-d3 + dedupe)...")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    ok = 0
    for c in target:
        cid = c["id"]
        st, d = api("POST", f"/contacts/{cid}/tags", body={"tags": [SEND_TAG, DEDUPE_TAG]})
        if st in (200, 201):
            ok += 1
            ledger["sent"].append({"contactId": cid, "name": (c.get("firstName") or "").strip(),
                                    "phone": c.get("phone"), "d3_sent_at": ts})
            print(f"  ✓ {cid} {c.get('firstName','')}")
        else:
            print(f"  ✗ {cid} -> {st} {d}")
        time.sleep(0.4)
    json.dump(ledger, open(LEDGER_PATH, "w"), ensure_ascii=False, indent=2)
    print(f"\nListo: {ok}/{len(target)} d3 enviados. Ledger: {LEDGER_PATH} (total enviados: {len(ledger['sent'])})")
    print(f"Restantes para próxima corrida: {max(0, len(elig)-len(target))}")


if __name__ == "__main__":
    main()
