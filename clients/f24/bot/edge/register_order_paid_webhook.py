#!/usr/bin/env python3
"""Registra (idempotente) el webhook Shopify `orders/paid` → edge function f24-order-paid.

NO contiene secretos: lee las credenciales Shopify del entorno o de clients/f24/.env.
Si el webhook ya existe apuntando a la misma address, no duplica.

Uso:
    python edge/register_order_paid_webhook.py           # registra / verifica
    python edge/register_order_paid_webhook.py --list    # solo lista los webhooks actuales
"""
import os, sys, json, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
F24_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # edge -> bot -> clients/f24
ADDRESS = "https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/f24-order-paid"
TOPIC = "orders/paid"


def env(key, default=None):
    if os.environ.get(key):
        return os.environ[key]
    envp = os.path.join(F24_ROOT, ".env")
    if os.path.exists(envp):
        for line in open(envp, encoding="utf-8"):
            line = line.strip()
            if line.startswith(key + "=") and "=" in line:
                return line.split("=", 1)[1].split("#", 1)[0].strip().strip('"').strip("'")
    return default


SHOP = env("SHOPIFY_SHOP")
CLIENT_ID = env("SHOPIFY_CLIENT_ID")
CLIENT_SECRET = env("SHOPIFY_CLIENT_SECRET")
API_VERSION = env("SHOPIFY_API_VERSION", "2024-10")
if not (SHOP and CLIENT_ID and CLIENT_SECRET):
    raise SystemExit("FALTAN credenciales Shopify (SHOPIFY_SHOP/CLIENT_ID/CLIENT_SECRET) en env o clients/f24/.env")

BASE = f"https://{SHOP}/admin/api/{API_VERSION}"


def _req(url, method="GET", headers=None, data=None):
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=data)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After", "2"))); continue
            raise SystemExit(f"Shopify {method} {url} → {e.code}: {e.read().decode()[:300]}")


def get_token():
    body = json.dumps({"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}).encode()
    d = _req(f"https://{SHOP}/admin/oauth/access_token", "POST", {"Content-Type": "application/json"}, body)
    return d["access_token"]


def main():
    tok = get_token()
    h = {"X-Shopify-Access-Token": tok, "Content-Type": "application/json"}
    hooks = _req(f"{BASE}/webhooks.json", "GET", h).get("webhooks", [])

    if "--list" in sys.argv:
        for hh in hooks:
            print(f"  [{hh['id']}] {hh['topic']} -> {hh['address']}")
        print(f"total: {len(hooks)}")
        return

    existing = [hh for hh in hooks if hh["topic"] == TOPIC and hh["address"] == ADDRESS]
    if existing:
        print(f"OK ya existe {TOPIC} -> {ADDRESS} (id {existing[0]['id']}). No se duplica.")
        return

    body = json.dumps({"webhook": {"topic": TOPIC, "address": ADDRESS, "format": "json"}}).encode()
    resp = _req(f"{BASE}/webhooks.json", "POST", h, body)
    print(f"CREADO webhook id {resp.get('webhook', {}).get('id')} · {TOPIC} -> {ADDRESS}")


if __name__ == "__main__":
    main()
