#!/usr/bin/env python3
"""Barrido de DMs + comentarios sin atender en IG/FB para clientes SPEKGEN.
Escribe lo pendiente a la cola Supabase social_inbox (dedupe por external_id).

Uso:
  python3 social_sweep.py --client F24 --dry-run     # solo imprime, no escribe
  python3 social_sweep.py --client all               # barre todos los activos -> Supabase
  python3 social_sweep.py --client HC --no-dm        # solo comentarios
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import secrets, meta, store  # noqa: E402
from lib.classify import classify  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(HERE, "clients.json")) as f:
        return json.load(f)


def sweep_client(code, cfg, conf, include_dms=True):
    token_ref = conf["token_refs"][cfg["token_ref"]]
    user_token = secrets.meta_token(token_ref)
    page_id = cfg["page_id"]
    page_token = meta.page_access_token(page_id, user_token)

    items = []
    errors = []

    # 1) Comentarios FB organico
    try:
        items += meta.fb_feed_comments(page_id, page_token)
    except Exception as e:
        errors.append(f"fb_feed: {e}")

    # 2) Comentarios en ADS (dark posts) — la fuente real
    if cfg.get("ad_account"):
        try:
            items += meta.ad_comments(cfg["ad_account"], page_id, user_token, page_token)
        except Exception as e:
            errors.append(f"ads: {e}")

    # 3) Comentarios IG organico
    if cfg.get("ig_id"):
        try:
            items += meta.ig_media_comments(cfg["ig_id"], page_token, cfg.get("ig_username"))
        except Exception as e:
            errors.append(f"ig_media: {e}")

    # 4) DMs IG sin responder
    if include_dms and cfg.get("ig_id"):
        try:
            items += meta.ig_unanswered_dms(page_id, page_token)
        except Exception as e:
            errors.append(f"ig_dm: {e}")

    # enriquecer con metadata del cliente + politica + clasificacion
    internal_set = {a.lower().lstrip("@") for a in conf.get("internal_accounts", [])}
    for it in items:
        it["client"] = code
        it["token_ref"] = cfg["token_ref"]
        if it["type"] == "comment":
            it["mode"] = cfg.get("comment_mode", "draft")
        else:
            it["mode"] = cfg.get("dm_mode", "draft")
        status, reason, category = classify(it, internal_set)
        it["status"] = status
        meta_obj = {}
        if reason:
            meta_obj["skip_reason"] = reason
        if category:
            meta_obj["category"] = category
        it["meta"] = meta_obj or None
    return items, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default="all", help="HC | LF | F24 | all")
    ap.add_argument("--dry-run", action="store_true", help="no escribe a Supabase, solo imprime")
    ap.add_argument("--no-dm", action="store_true", help="omite barrido de DMs")
    args = ap.parse_args()

    conf = load_config()
    clients = conf["clients"]
    targets = list(clients) if args.client == "all" else [args.client.upper()]

    grand_total = 0
    for code in targets:
        cfg = clients.get(code)
        if not cfg:
            print(f"[{code}] no existe en clients.json", file=sys.stderr)
            continue
        if not cfg.get("active", True):
            print(f"[{code}] inactivo, skip")
            continue
        items, errors = sweep_client(code, cfg, conf, include_dms=not args.no_dm)
        for e in errors:
            print(f"[{code}] WARN {e}", file=sys.stderr)

        pending = [i for i in items if i["status"] == "pending"]
        skipped = [i for i in items if i["status"] == "skipped"]
        ads = [i for i in pending if i["source"] == "ad"]
        dms = [i for i in pending if i["type"] == "dm"]
        print(f"\n=== {code} ({cfg['name']}) === SEÑAL: {len(pending)} a atender "
              f"({len(ads)} en ads, {len(dms)} DMs)  |  ruido/interno filtrado: {len(skipped)}")
        for it in sorted(pending, key=lambda x: (x.get("age_days") or 0), reverse=True):
            cat = (it.get("meta") or {}).get("category", "?")
            tag = f"AD:{it['ad_name'][:20]}" if it.get("ad_name") else it["channel"]
            print(f"  [{it.get('age_days','?')}d] {cat:8} {it.get('author') or '?':16} "
                  f"{(it.get('body') or '')[:55]!r}  ({tag})")

        if not args.dry_run and items:
            n = store.upsert(items)
            print(f"  -> {n} filas nuevas en social_inbox (dedupe por external_id)")
        grand_total += len(pending)

    print(f"\nTOTAL a atender (señal): {grand_total}"
          + ("  [DRY-RUN, nada escrito]" if args.dry_run else ""))


if __name__ == "__main__":
    main()
