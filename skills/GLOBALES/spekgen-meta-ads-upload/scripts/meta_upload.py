#!/usr/bin/env python3
"""
meta_upload.py — Canonical Meta Ads uploader for SPEKGEN clients.

Commands:
    upload-ad        Create creative + ad from a JSON spec
    create-campaign  Create campaign + adsets + ads from a plan JSON
    verify-ad        Check if an ad's creative has IG correctly configured
    fix-creative     Repair an ad whose creative has wrong IG structure
    list-campaigns   List campaigns in ad account

Every command reads META_* vars from the client's .env (pass --env /path/to/.env)
or from the current environment.

Examples:
    # Upload single static ad
    python3 meta_upload.py upload-ad \\
        --env "/path/to/GR - GREENRAY/.env" \\
        --spec "./ad_specs/GR-AD-001.json" \\
        --adset-id 23855052705260796

    # Verify IG is properly configured
    python3 meta_upload.py verify-ad --env ./env --ad-id 23855052704800796

    # Fix all ads in a campaign
    python3 meta_upload.py fix-creative \\
        --env ./env --campaign-id 23855052698520796 --all

    # Create campaign from plan
    python3 meta_upload.py create-campaign \\
        --env ./env --plan ./campaign_plan.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running from anywhere
sys.path.insert(0, str(Path(__file__).parent))
from meta_helpers import (  # noqa: E402
    load_env, api_get, api_post, upload_image_from_path,
    build_static_creative, build_carousel_creative,
    build_dynamic_creative_specs, create_creative, create_ad,
    create_campaign as api_create_campaign, create_adset,
    build_advantage_targeting, verify_creative_ig, fix_creative_ig,
    DEFAULT_URL_TAGS,
)


# ──────────────────────────────────────────────────────────────────────────
# Env loading
# ──────────────────────────────────────────────────────────────────────────

def get_env(args):
    env = {}
    if args.env:
        env = load_env(args.env)
    # Allow overrides from real environment
    for k in ("META_TOKEN", "META_AD_ACCOUNT", "META_PAGE_ID",
              "META_IG_ACCOUNT_ID", "META_IG_ACTOR_ID", "META_PIXEL_ID"):
        if os.environ.get(k):
            env[k] = os.environ[k]

    # Normalize IG account id
    if not env.get("META_IG_ACCOUNT_ID") and env.get("META_IG_ACTOR_ID"):
        env["META_IG_ACCOUNT_ID"] = env["META_IG_ACTOR_ID"]

    missing = [k for k in ("META_TOKEN", "META_AD_ACCOUNT",
                           "META_PAGE_ID", "META_IG_ACCOUNT_ID")
               if not env.get(k)]
    if missing:
        die(f"Missing .env keys: {', '.join(missing)}")

    # Ensure ad account has act_ prefix
    if not env["META_AD_ACCOUNT"].startswith("act_"):
        env["META_AD_ACCOUNT"] = "act_" + env["META_AD_ACCOUNT"]
    return env


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


# ──────────────────────────────────────────────────────────────────────────
# upload-ad
# ──────────────────────────────────────────────────────────────────────────

def cmd_upload_ad(args):
    """
    Create creative + ad from a JSON spec file.

    Spec format (static example):
    {
      "ad_name": "GR-AD-001_PROTOCOLO",
      "creative_type": "static" | "carousel" | "dynamic",
      "landing_url": "https://greenray.mx/products/...",
      "copy": "...",
      "headline": "...",
      "description": "...",
      "cta_type": "SHOP_NOW",
      "image_paths": ["./img1.jpg"],        # static: 1; carousel: 2-10; dynamic: up to 10
      "image_paths_9x16": ["./img1_9x16.jpg"],  # optional — for Stories/Reels
      "bodies": [...], "titles": [...]       # dynamic only
    }
    """
    env = get_env(args)
    spec = json.loads(Path(args.spec).read_text())

    print(f"\n╭─ Uploading {spec['ad_name']} ({spec['creative_type']})")

    # Upload images
    print(f"│  Uploading {len(spec['image_paths'])} image(s)...")
    hashes = []
    for p in spec["image_paths"]:
        h = upload_image_from_path(env["META_TOKEN"], env["META_AD_ACCOUNT"], p)
        if isinstance(h, dict) and "error" in h:
            die(f"Image upload failed ({p}): {h['error']}")
        hashes.append(h)
        print(f"│    ✓ {Path(p).name} → {h[:12]}...")

    hashes_9x16 = []
    if spec.get("image_paths_9x16"):
        print(f"│  Uploading {len(spec['image_paths_9x16'])} 9:16 image(s)...")
        for p in spec["image_paths_9x16"]:
            h = upload_image_from_path(env["META_TOKEN"], env["META_AD_ACCOUNT"], p)
            if isinstance(h, dict) and "error" in h:
                die(f"9:16 image upload failed: {h['error']}")
            hashes_9x16.append(h)

    # Build creative
    url_tags = spec.get("url_tags", DEFAULT_URL_TAGS)
    ctype = spec["creative_type"]
    afs = None

    if ctype == "static":
        oss = build_static_creative(
            env["META_PAGE_ID"],
            env["META_IG_ACCOUNT_ID"],
            {
                **spec,
                "image_hash": hashes[0],
                "image_hash_9x16": hashes_9x16[0] if hashes_9x16 else None,
            },
        )
    elif ctype == "carousel":
        children = [
            {
                "link": spec["landing_url"],
                "image_hash": h,
                "name": spec.get("slides", [{}] * len(hashes))[i].get(
                    "name", spec.get("headline", ""))[:80],
                "description": spec.get("slides", [{}] * len(hashes))[i].get(
                    "description", "")[:80],
                "call_to_action": {
                    "type": spec.get("cta_type", "SHOP_NOW"),
                    "value": {"link": spec["landing_url"]},
                },
            }
            for i, h in enumerate(hashes)
        ]
        children_9x16 = None
        if hashes_9x16:
            children_9x16 = [
                {
                    "link": spec["landing_url"],
                    "image_hash": h,
                    "call_to_action": {
                        "type": spec.get("cta_type", "SHOP_NOW"),
                        "value": {"link": spec["landing_url"]},
                    },
                }
                for h in hashes_9x16
            ]
        oss = build_carousel_creative(
            env["META_PAGE_ID"],
            env["META_IG_ACCOUNT_ID"],
            {
                **spec,
                "child_attachments": children,
                "child_attachments_9x16": children_9x16,
            },
        )
    elif ctype == "dynamic":
        oss, afs = build_dynamic_creative_specs(
            env["META_PAGE_ID"],
            env["META_IG_ACCOUNT_ID"],
            {**spec, "image_hashes": hashes},
        )
    else:
        die(f"Unknown creative_type: {ctype}")

    print(f"│  Creating adcreative...")
    creative = create_creative(
        env["META_TOKEN"], env["META_AD_ACCOUNT"],
        name=spec["ad_name"] + "_creative",
        object_story_spec=oss,
        asset_feed_spec=afs,
        url_tags=url_tags,
    )
    if "error" in creative:
        die(f"Creative creation failed: {creative['error']}")
    creative_id = creative["id"]
    print(f"│    ✓ creative_id: {creative_id}")

    # Create ad
    print(f"│  Creating ad in adset {args.adset_id}...")
    ad = create_ad(
        env["META_TOKEN"], env["META_AD_ACCOUNT"],
        name=spec["ad_name"],
        adset_id=args.adset_id,
        creative_id=creative_id,
        status=args.status,
    )
    if "error" in ad:
        die(f"Ad creation failed: {ad['error']}")
    ad_id = ad["id"]
    print(f"│    ✓ ad_id: {ad_id}")

    # Verify
    print(f"│  Verifying IG + UTMs...")
    v = verify_creative_ig(env["META_TOKEN"], creative_id)
    status_icon = "✅" if v["ok"] else "❌"
    print(f"│    {status_icon} oss.instagram_user_id: {v.get('oss_ig')}")
    print(f"│    {status_icon} url_tags: {'set' if v.get('has_url_tags') else 'MISSING'}")
    if v.get("issues"):
        for issue in v["issues"]:
            print(f"│    ⚠ {issue}")
    print(f"╰─ Done. ad_id={ad_id} creative_id={creative_id} status={args.status}")

    return {"ad_id": ad_id, "creative_id": creative_id}


# ──────────────────────────────────────────────────────────────────────────
# verify-ad
# ──────────────────────────────────────────────────────────────────────────

def cmd_verify_ad(args):
    env = get_env(args)
    ad = api_get(args.ad_id, env["META_TOKEN"],
                 {"fields": "id,name,creative{id}"})
    if "error" in ad:
        die(f"Ad fetch failed: {ad['error']}")

    creative_id = ad["creative"]["id"]
    v = verify_creative_ig(env["META_TOKEN"], creative_id)

    print(f"\nAd: {ad['name']} ({ad['id']})")
    print(f"Creative: {creative_id}")
    print(f"Dynamic Creative: {v.get('is_dynamic_creative')}")
    print(f"instagram_user_id inside OSS: {v.get('oss_ig') or '❌ MISSING'}")
    print(f"instagram_user_id top-level:  {v.get('top_ig') or '(none — ok)'}")
    print(f"url_tags: {v.get('url_tags') or '❌ MISSING'}")
    print(f"effective_instagram_media_id: "
          f"{v.get('effective_instagram_media_id') or '(none — normal for DC)'}")

    if v["ok"]:
        print("\n✅ Creative is correctly configured.")
    else:
        print(f"\n❌ Issues found:")
        for issue in v["issues"]:
            print(f"  • {issue}")
        print("\nRun: meta_upload.py fix-creative --ad-id {0}".format(args.ad_id))


# ──────────────────────────────────────────────────────────────────────────
# fix-creative
# ──────────────────────────────────────────────────────────────────────────

def cmd_fix_creative(args):
    env = get_env(args)

    # Resolve list of ad IDs to fix
    if args.ad_id:
        ad_ids = [args.ad_id]
    elif args.campaign_id and args.all:
        result = api_get(f"{args.campaign_id}/ads", env["META_TOKEN"],
                         {"fields": "id,name", "limit": 50})
        if "error" in result:
            die(f"Failed to list ads: {result['error']}")
        ad_ids = [ad["id"] for ad in result["data"]]
        print(f"Found {len(ad_ids)} ads in campaign {args.campaign_id}")
    else:
        die("Provide --ad-id OR --campaign-id --all")

    url_tags = args.url_tags or DEFAULT_URL_TAGS
    results = []

    for ad_id in ad_ids:
        print(f"\n→ Fixing {ad_id}...")
        r = fix_creative_ig(
            env["META_TOKEN"],
            env["META_AD_ACCOUNT"],
            ad_id,
            env["META_IG_ACCOUNT_ID"],
            env["META_PAGE_ID"],
            url_tags=url_tags,
        )
        if "error" in r:
            print(f"  ❌ {r['error']}")
        else:
            print(f"  ✓ old creative: {r['old_creative']}")
            print(f"  ✓ new creative: {r['new_creative']}")
        results.append({"ad_id": ad_id, "result": r})

    print(f"\n{sum(1 for r in results if 'error' not in r['result'])} / "
          f"{len(results)} ads fixed.")
    return results


# ──────────────────────────────────────────────────────────────────────────
# create-campaign
# ──────────────────────────────────────────────────────────────────────────

def cmd_create_campaign(args):
    """
    Create campaign + adsets + ads from a plan JSON.

    Plan format:
    {
      "campaign": {
        "name": "GR_CONV_PRODUCTS_ABR26",
        "objective": "OUTCOME_SALES",
        "daily_budget_cents": 18000
      },
      "adsets": [
        {
          "name": "ADSET_NAME",
          "optimization_goal": "OFFSITE_CONVERSIONS",
          "billing_event": "IMPRESSIONS",
          "pixel_id": "1234",
          "custom_event_type": "PURCHASE",
          "geo_locations": {"countries": ["MX"]},
          "age_min": 25, "age_max": 55,
          "is_dynamic_creative": false,
          "attribution_spec": [...],
          "ads": [ { /* same shape as upload-ad spec */ } ]
        }
      ]
    }
    """
    env = get_env(args)
    plan = json.loads(Path(args.plan).read_text())

    # 1. Campaign
    print(f"\n╭─ Creating campaign {plan['campaign']['name']}")
    camp = api_create_campaign(
        env["META_TOKEN"], env["META_AD_ACCOUNT"],
        **plan["campaign"], status=args.status,
    )
    if "error" in camp:
        die(f"Campaign creation failed: {camp['error']}")
    campaign_id = camp["id"]
    print(f"│  ✓ campaign_id: {campaign_id}")

    results = {"campaign_id": campaign_id, "adsets": []}

    # 2. Ad sets + ads
    for adset_spec in plan["adsets"]:
        print(f"├─ Creating adset {adset_spec['name']}")

        targeting = build_advantage_targeting(
            adset_spec["geo_locations"],
            age_min=adset_spec.get("age_min", 18),
            age_max=adset_spec.get("age_max", 65),
            genders=adset_spec.get("genders"),
        )

        adset_params = {
            "name": adset_spec["name"],
            "campaign_id": campaign_id,
            "optimization_goal": adset_spec["optimization_goal"],
            "billing_event": adset_spec.get("billing_event", "IMPRESSIONS"),
            "targeting": targeting,
            "status": args.status,
        }
        if "daily_budget_cents" in adset_spec:
            adset_params["daily_budget"] = adset_spec["daily_budget_cents"]
        if "start_time" in adset_spec:
            adset_params["start_time"] = adset_spec["start_time"]
        if "end_time" in adset_spec:
            adset_params["end_time"] = adset_spec["end_time"]
        if "pixel_id" in adset_spec:
            adset_params["promoted_object"] = {
                "pixel_id": adset_spec["pixel_id"],
                "custom_event_type": adset_spec.get("custom_event_type", "PURCHASE"),
            }
        if "attribution_spec" in adset_spec:
            adset_params["attribution_spec"] = adset_spec["attribution_spec"]
        if adset_spec.get("is_dynamic_creative"):
            adset_params["is_dynamic_creative"] = True

        adset = create_adset(env["META_TOKEN"], env["META_AD_ACCOUNT"], adset_params)
        if "error" in adset:
            print(f"│  ❌ adset failed: {adset['error']}")
            continue
        adset_id = adset["id"]
        print(f"│  ✓ adset_id: {adset_id}")

        adset_result = {"adset_id": adset_id, "ads": []}

        # Create ads in this adset
        for ad_spec in adset_spec.get("ads", []):
            # Resolve image paths relative to plan file
            base = Path(args.plan).parent
            ad_spec["image_paths"] = [
                str(base / p) if not Path(p).is_absolute() else p
                for p in ad_spec["image_paths"]
            ]
            if ad_spec.get("image_paths_9x16"):
                ad_spec["image_paths_9x16"] = [
                    str(base / p) if not Path(p).is_absolute() else p
                    for p in ad_spec["image_paths_9x16"]
                ]

            # Mock args for upload-ad
            class A:
                pass
            a = A()
            a.env = args.env
            a.spec = None  # override below
            a.adset_id = adset_id
            a.status = args.status

            # Inline the upload with the spec dict
            # (avoid writing/reading spec file)
            tmp_spec = Path(f"/tmp/_spekgen_spec_{ad_spec['ad_name']}.json")
            tmp_spec.write_text(json.dumps(ad_spec))
            a.spec = str(tmp_spec)
            try:
                r = cmd_upload_ad(a)
                adset_result["ads"].append(r)
            except SystemExit:
                adset_result["ads"].append({"error": "upload failed"})
            finally:
                tmp_spec.unlink(missing_ok=True)

        results["adsets"].append(adset_result)

    print(f"\n╰─ Campaign created. {len(results['adsets'])} adsets, "
          f"{sum(len(a['ads']) for a in results['adsets'])} ads.")
    return results


# ──────────────────────────────────────────────────────────────────────────
# list-campaigns
# ──────────────────────────────────────────────────────────────────────────

def cmd_list_campaigns(args):
    env = get_env(args)
    result = api_get(
        f"{env['META_AD_ACCOUNT']}/campaigns",
        env["META_TOKEN"],
        {"fields": "id,name,status,daily_budget,objective", "limit": 20},
    )
    if "error" in result:
        die(f"List failed: {result['error']}")
    for c in result.get("data", []):
        budget = c.get("daily_budget")
        budget_str = f"${int(budget)/100:.0f}/day" if budget else "CBO"
        print(f"  {c['id']}  [{c['status']}]  {c['name']}  {budget_str}")


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd")

    def add_env(p):
        p.add_argument("--env", required=False,
                       help="Path to client .env file")

    p1 = sub.add_parser("upload-ad")
    add_env(p1)
    p1.add_argument("--spec", required=True)
    p1.add_argument("--adset-id", required=True)
    p1.add_argument("--status", default="PAUSED")
    p1.set_defaults(func=cmd_upload_ad)

    p2 = sub.add_parser("verify-ad")
    add_env(p2)
    p2.add_argument("--ad-id", required=True)
    p2.set_defaults(func=cmd_verify_ad)

    p3 = sub.add_parser("fix-creative")
    add_env(p3)
    p3.add_argument("--ad-id")
    p3.add_argument("--campaign-id")
    p3.add_argument("--all", action="store_true")
    p3.add_argument("--url-tags")
    p3.set_defaults(func=cmd_fix_creative)

    p4 = sub.add_parser("create-campaign")
    add_env(p4)
    p4.add_argument("--plan", required=True)
    p4.add_argument("--status", default="PAUSED")
    p4.set_defaults(func=cmd_create_campaign)

    p5 = sub.add_parser("list-campaigns")
    add_env(p5)
    p5.set_defaults(func=cmd_list_campaigns)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
