#!/usr/bin/env python3
"""Publisher: toma los comentarios aprobados (status='approved') y publica la respuesta
en Meta vía Graph API. Corre en el cron (tiene los tokens del .env / GH secrets).

El botón del email solo marca 'approved'; ESTE worker publica. Así los tokens de Meta
nunca viven en la Edge Function ni en la base.

Uso:
  python3 social_publish.py            # publica todo lo aprobado
  python3 social_publish.py --dry-run  # muestra qué publicaría, sin tocar Meta
  python3 social_publish.py --limit 5
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import secrets, meta, store  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(HERE, "clients.json")) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    conf = load_config()
    approved = [r for r in store.fetch(status="approved", order="acted_at.asc")
                if r["type"] == "comment"][:args.limit]
    if not approved:
        print("Nada aprobado pendiente de publicar.")
        return

    page_tokens = {}   # cache por cliente
    published = failed = 0

    for r in approved:
        code = r["client"]
        cfg = conf["clients"].get(code)
        draft = (r.get("draft") or "").strip()
        if not cfg or not draft:
            store.update(r["external_id"], {"status": "publish_failed",
                         "meta": {**(r.get("meta") or {}), "publish_error": "sin cfg/draft"}})
            failed += 1
            continue

        print(f"[{code}] {r['channel']} {r['external_id']}")
        print(f"    respuesta: {draft!r}")
        if args.dry_run:
            continue

        try:
            if code not in page_tokens:
                user_token = secrets.meta_token(conf["token_refs"][cfg["token_ref"]])
                page_tokens[code] = meta.page_access_token(cfg["page_id"], user_token)
            res = meta.reply_to_comment(r["channel"], r["external_id"], draft, page_tokens[code])
            store.update(r["external_id"], {
                "status": "published",
                "reply_external_id": res.get("id"),
                "meta": {**(r.get("meta") or {}), "publish_error": None},
            })
            print(f"    -> publicado id={res.get('id')}")
            published += 1
        except Exception as e:
            store.update(r["external_id"], {"status": "publish_failed",
                         "meta": {**(r.get("meta") or {}), "publish_error": str(e)[:300]}})
            print(f"    -> ERROR: {e}")
            failed += 1

    print(f"\nPublicados: {published}  Fallidos: {failed}"
          + ("  [DRY-RUN]" if args.dry_run else ""))


if __name__ == "__main__":
    main()
