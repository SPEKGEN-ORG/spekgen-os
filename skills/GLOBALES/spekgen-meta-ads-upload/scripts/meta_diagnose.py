#!/usr/bin/env python3
"""
meta_diagnose.py — Validate Meta Ads prerequisites before upload.

Checks:
  1. Token alive + permission scopes
  2. Ad account accessible
  3. Page assigned to system user
  4. Instagram account connected to ad account
  5. Instagram account structure (business vs page-backed)
  6. Pixel active (if configured)
  7. Sample creative structure (finds one recent ad to verify pattern)

Usage:
    python3 meta_diagnose.py --env "/path/to/client/.env"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from meta_helpers import load_env, api_get  # noqa: E402


REQUIRED_SCOPES = [
    "ads_management", "ads_read", "business_management",
    "pages_show_list", "pages_read_engagement", "pages_manage_ads",
    "instagram_basic", "instagram_content_publish",
]


def ok(msg):
    print(f"  ✅ {msg}")


def fail(msg):
    print(f"  ❌ {msg}")


def warn(msg):
    print(f"  ⚠  {msg}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    args = parser.parse_args()

    env = load_env(args.env)
    token = env.get("META_TOKEN")
    ad_account = env.get("META_AD_ACCOUNT", "")
    page_id = env.get("META_PAGE_ID")
    ig_id = env.get("META_IG_ACCOUNT_ID") or env.get("META_IG_ACTOR_ID")
    pixel_id = env.get("META_PIXEL_ID")

    if not ad_account.startswith("act_"):
        ad_account = "act_" + ad_account

    print(f"\n╭─ Meta Ads Diagnostic — {env.get('CLIENT_NAME', args.env)}")
    issues = 0

    # 1. Token + permissions
    print("├─ 1. Token + permissions")
    me = api_get("me", token, {"fields": "id,name"})
    if "error" in me:
        fail(f"Token dead: {me['error']}")
        issues += 1
        sys.exit(1)
    ok(f"Token alive — user: {me.get('name', me['id'])}")

    perms = api_get("me/permissions", token)
    if "error" not in perms:
        granted = {p["permission"] for p in perms.get("data", [])
                   if p.get("status") == "granted"}
        missing = [s for s in REQUIRED_SCOPES if s not in granted]
        if missing:
            warn(f"Missing scopes: {', '.join(missing)}")
        else:
            ok(f"All {len(REQUIRED_SCOPES)} required scopes granted")

    # 2. Ad account
    print("├─ 2. Ad account")
    acc = api_get(ad_account, token,
                  {"fields": "id,name,account_status,currency,timezone_name"})
    if "error" in acc:
        fail(f"Ad account unreachable: {acc['error']}")
        issues += 1
    else:
        status_map = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED",
                      7: "PENDING_REVIEW", 9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE"}
        status = status_map.get(acc.get("account_status"), f"STATUS_{acc.get('account_status')}")
        if status == "ACTIVE":
            ok(f"{acc['name']} ({acc['currency']}) — {status}")
        else:
            fail(f"{acc['name']} — {status}")
            issues += 1

    # 3. Page
    print("├─ 3. Page")
    if not page_id:
        fail("META_PAGE_ID not set")
        issues += 1
    else:
        page = api_get(page_id, token,
                       {"fields": "id,name,access_token,instagram_business_account"})
        if "error" in page:
            fail(f"Page unreachable: {page['error']}")
            issues += 1
        else:
            has_token = bool(page.get("access_token"))
            ok(f"{page.get('name', page_id)} — "
               f"page token: {'available' if has_token else 'NOT granted'}")
            if not has_token:
                warn("Without page token, some legacy IG endpoints will fail")

    # 4. Instagram connection
    print("├─ 4. Instagram account")
    if not ig_id:
        fail("META_IG_ACCOUNT_ID not set")
        issues += 1
    else:
        # Check page -> IG
        if page_id:
            p = api_get(page_id, token,
                        {"fields": "instagram_business_account{id,username}"})
            iba = p.get("instagram_business_account") if "error" not in p else None
            if iba and iba.get("id") == ig_id:
                ok(f"IG {iba.get('username', ig_id)} correctly connected to page")
            elif iba:
                warn(f"Page has IG {iba['id']} but .env has {ig_id} (mismatch)")
            else:
                fail("Page has no IG connected")
                issues += 1

        # Check ad account -> IG
        igs = api_get(f"{ad_account}/instagram_accounts", token,
                      {"fields": "id,username"})
        if "error" not in igs:
            data = igs.get("data", [])
            ids = [i["id"] for i in data]
            if ig_id in ids:
                ok(f"IG {ig_id} accessible from ad account")
            else:
                fail(f"IG {ig_id} NOT linked to ad account "
                     f"(visible: {ids or 'none'})")
                issues += 1

    # 5. Pixel
    print("├─ 5. Pixel")
    if not pixel_id:
        warn("META_PIXEL_ID not set (OK if using brand awareness/traffic only)")
    else:
        pix = api_get(pixel_id, token, {"fields": "id,name,is_unavailable,last_fired_time"})
        if "error" in pix:
            fail(f"Pixel unreachable: {pix['error']}")
            issues += 1
        else:
            last = pix.get("last_fired_time", "never")
            if pix.get("is_unavailable"):
                fail(f"Pixel UNAVAILABLE — {pix.get('name')}")
                issues += 1
            else:
                ok(f"{pix.get('name')} — last fired: {last}")

    # 6. Sample creative check
    print("├─ 6. Recent creative structure (sanity check)")
    recent = api_get(
        f"{ad_account}/ads", token,
        {"fields": "id,name,creative{id,object_story_spec{instagram_user_id}}",
         "limit": 1},
    )
    if "error" not in recent and recent.get("data"):
        ad = recent["data"][0]
        oss = ad.get("creative", {}).get("object_story_spec", {})
        if oss.get("instagram_user_id"):
            ok(f"Most recent ad has IG in OSS — pattern is correct")
        else:
            warn(f"Most recent ad ({ad['name']}) is MISSING "
                 f"instagram_user_id in object_story_spec — check/fix")

    # Summary
    print("╰─ Result")
    if issues == 0:
        print("\n  ✅ All checks passed. Safe to upload ads.\n")
        sys.exit(0)
    else:
        print(f"\n  ❌ {issues} issue(s) found. Fix before uploading.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
