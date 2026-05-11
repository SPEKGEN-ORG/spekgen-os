"""
meta_helpers.py — Funciones compartidas para Meta Marketing API v21.0

Este módulo encapsula las reglas críticas aprendidas en producción:
  - instagram_user_id SIEMPRE dentro de object_story_spec (no top-level)
  - NUNCA usar instagram_actor_id (cross-BM system user lo rechaza)
  - Pixel en promoted_object del ad set, no en tracking_specs del ad
  - Advantage+ audience con targeting_automation.advantage_audience=1 y age_min<=25
  - Dynamic Creative: asset_feed_spec con ad_formats=["SINGLE_IMAGE"]
"""

import hashlib
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

META_API_VERSION = "v21.0"
META_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"


# ──────────────────────────────────────────────────────────────────────────
# Environment loading
# ──────────────────────────────────────────────────────────────────────────

def load_env(env_path):
    """Load .env file into dict. Supports KEY=VALUE per line, ignores #comments."""
    env = {}
    p = Path(env_path)
    if not p.exists():
        raise FileNotFoundError(f".env not found at {env_path}")
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        # Strip quotes
        v = v.strip().strip('"').strip("'")
        env[k.strip()] = v
    return env


# ──────────────────────────────────────────────────────────────────────────
# API helpers
# ──────────────────────────────────────────────────────────────────────────

def _encode(data):
    """Encode dict values — serialize nested dicts/lists to JSON strings."""
    out = {}
    for k, v in data.items():
        if isinstance(v, (dict, list)):
            out[k] = json.dumps(v)
        else:
            out[k] = v
    return urllib.parse.urlencode(out).encode()


def api_get(path, token, params=None):
    url = f"{META_BASE_URL}/{path}?" + urllib.parse.urlencode({
        **(params or {}), "access_token": token
    })
    try:
        with urllib.request.urlopen(urllib.request.Request(url)) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return {"error": json.loads(e.read())}
        except Exception:
            return {"error": {"message": str(e), "code": e.code}}


def api_post(path, token, data):
    url = f"{META_BASE_URL}/{path}"
    body = _encode({**data, "access_token": token})
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return {"error": json.loads(e.read())}
        except Exception:
            return {"error": {"message": str(e), "code": e.code}}


def api_delete(path, token):
    url = f"{META_BASE_URL}/{path}"
    body = urllib.parse.urlencode({"access_token": token}).encode()
    req = urllib.request.Request(url, data=body, method="DELETE")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read())}


# ──────────────────────────────────────────────────────────────────────────
# Image upload
# ──────────────────────────────────────────────────────────────────────────

def upload_image_from_path(token, ad_account, image_path):
    """Upload image file to Meta, return image_hash string or {'error': ...}."""
    image_path = Path(image_path)
    if not image_path.exists():
        return {"error": f"Image not found: {image_path}"}

    boundary = "----SPEKGEN" + hashlib.md5(image_path.name.encode()).hexdigest()[:12]
    ctype = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"

    body = b""
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="access_token"\r\n\r\n'
    body += token.encode() + b"\r\n"
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="filename"; filename="{image_path.name}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += image_path.read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{META_BASE_URL}/{ad_account}/adimages",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            images = result.get("images", {})
            if not images:
                return {"error": "No images returned", "raw": result}
            first = next(iter(images.values()))
            return first["hash"]
    except urllib.error.HTTPError as e:
        try:
            return {"error": json.loads(e.read())}
        except Exception:
            return {"error": {"message": str(e), "code": e.code}}


# ──────────────────────────────────────────────────────────────────────────
# Creative builders — the canonical patterns
# ──────────────────────────────────────────────────────────────────────────

def build_static_creative(page_id, ig_user_id, data):
    """
    Build object_story_spec for static single image ad.
    RULE: instagram_user_id INSIDE object_story_spec (never top-level only).
    """
    oss = {
        "page_id": page_id,
        "instagram_user_id": ig_user_id,  # CRITICAL: inside OSS
        "link_data": {
            "link": data["landing_url"],
            "message": data["copy"],
            "name": data.get("headline", "")[:255],
            "description": data.get("description", "")[:255],
            "image_hash": data["image_hash"],
            "call_to_action": {
                "type": data.get("cta_type", "SHOP_NOW"),
                "value": {"link": data["landing_url"]},
            },
        },
    }
    if data.get("image_hash_9x16"):
        oss["instagram_story_attachment"] = {
            "link_data": {
                "link": data["landing_url"],
                "image_hash": data["image_hash_9x16"],
                "call_to_action": {
                    "type": data.get("cta_type", "SHOP_NOW"),
                    "value": {"link": data["landing_url"]},
                },
            }
        }
    return oss


def build_carousel_creative(page_id, ig_user_id, data):
    """Build object_story_spec for carousel ad."""
    oss = {
        "page_id": page_id,
        "instagram_user_id": ig_user_id,
        "link_data": {
            "link": data["landing_url"],
            "message": data["copy"],
            "child_attachments": data["child_attachments"],
            "multi_share_end_card": data.get("multi_share_end_card", True),
            "multi_share_optimized": True,
        },
    }
    if data.get("child_attachments_9x16"):
        oss["instagram_story_attachment"] = {
            "link_data": {
                "link": data["landing_url"],
                "child_attachments": data["child_attachments_9x16"],
                "multi_share_end_card": False,
                "multi_share_optimized": True,
            }
        }
    return oss


def build_dynamic_creative_specs(page_id, ig_user_id, data):
    """
    Build (object_story_spec, asset_feed_spec) for Dynamic Creative ad.
    CONSTRAINTS:
      - Only 1 ad per ad set with dynamic creative
      - asset_feed_spec must have ad_formats=["SINGLE_IMAGE"]
    """
    oss = {
        "page_id": page_id,
        "instagram_user_id": ig_user_id,
    }
    afs = {
        "ad_formats": ["SINGLE_IMAGE"],  # REQUIRED
        "images": [{"hash": h} for h in data["image_hashes"]],
        "bodies": [{"text": b} for b in data["bodies"]],
        "titles": [{"text": t} for t in data["titles"]],
        "descriptions": [{"text": d} for d in data.get("descriptions", [""])],
        "link_urls": [{"website_url": data["landing_url"]}],
        "call_to_action_types": [data.get("cta_type", "SHOP_NOW")],
    }
    return oss, afs


# ──────────────────────────────────────────────────────────────────────────
# Creative creation
# ──────────────────────────────────────────────────────────────────────────

DEFAULT_URL_TAGS = (
    "utm_source=meta"
    "&utm_medium=paid_social"
    "&utm_campaign={{campaign.name}}"
    "&utm_content={{ad.name}}"
    "&utm_term={{adset.name}}"
)


def create_creative(token, ad_account, name, object_story_spec,
                    asset_feed_spec=None, url_tags=None):
    """Create adcreative. Returns dict with id or error."""
    params = {
        "name": name,
        "object_story_spec": object_story_spec,
    }
    if asset_feed_spec:
        params["asset_feed_spec"] = asset_feed_spec
    if url_tags:
        params["url_tags"] = url_tags
    return api_post(f"{ad_account}/adcreatives", token, params)


def verify_creative_ig(token, creative_id):
    """
    Verify a creative has Instagram correctly configured.
    Returns dict with status and details.
    """
    result = api_get(
        creative_id,
        token,
        {
            "fields": "id,name,object_story_spec{instagram_user_id,page_id},"
                      "instagram_user_id,url_tags,effective_instagram_media_id,"
                      "asset_feed_spec{ad_formats}"
        },
    )
    if "error" in result:
        return {"ok": False, "error": result["error"]}

    oss = result.get("object_story_spec", {})
    oss_ig = oss.get("instagram_user_id") if isinstance(oss, dict) else None
    top_ig = result.get("instagram_user_id")
    has_url_tags = bool(result.get("url_tags"))
    is_dc = "asset_feed_spec" in result

    issues = []
    if not oss_ig:
        issues.append("MISSING instagram_user_id inside object_story_spec "
                      "(THIS is why UI dropdown shows empty)")
    if not has_url_tags:
        issues.append("Missing url_tags (UTMs)")

    return {
        "ok": not issues,
        "creative_id": creative_id,
        "is_dynamic_creative": is_dc,
        "oss_ig": oss_ig,
        "top_ig": top_ig,
        "has_url_tags": has_url_tags,
        "url_tags": result.get("url_tags"),
        "effective_instagram_media_id": result.get("effective_instagram_media_id"),
        "issues": issues,
    }


# ──────────────────────────────────────────────────────────────────────────
# Campaign / Ad Set / Ad creation
# ──────────────────────────────────────────────────────────────────────────

def create_campaign(token, ad_account, name, objective, status="PAUSED",
                    daily_budget_cents=None, buying_type="AUCTION",
                    **kwargs):
    """
    Create campaign with CBO optional.
    objective examples: OUTCOME_SALES, OUTCOME_TRAFFIC, OUTCOME_AWARENESS
    daily_budget_cents: 18000 = $180 MXN if ad_account is in MXN
    """
    params = {
        "name": name,
        "objective": objective,
        "status": status,
        "buying_type": buying_type,
        "special_ad_categories": [],
    }
    if daily_budget_cents:
        params["daily_budget"] = daily_budget_cents
        params["bid_strategy"] = "LOWEST_COST_WITHOUT_CAP"
    params.update(kwargs)
    return api_post(f"{ad_account}/campaigns", token, params)


def build_advantage_targeting(geo_locations, age_min=18, age_max=65, genders=None):
    """
    Build targeting spec with Advantage+ audience enabled.
    CRITICAL: age_min must be <= 25 for Advantage+.
    """
    if age_min > 25:
        age_min = 25  # auto-correct
    t = {
        "geo_locations": geo_locations,
        "age_min": age_min,
        "age_max": age_max,
        "targeting_automation": {"advantage_audience": 1},  # REQUIRED
    }
    if genders:
        t["genders"] = genders
    return t


def create_adset(token, ad_account, params):
    """
    Create ad set.
    `params` expected keys:
      name, campaign_id, optimization_goal, billing_event, status,
      targeting, start_time, daily_budget (optional if CBO),
      promoted_object (for conversion — pixel + event),
      attribution_spec (optional), is_dynamic_creative (optional bool)
    """
    p = dict(params)
    p.setdefault("billing_event", "IMPRESSIONS")
    return api_post(f"{ad_account}/adsets", token, p)


def create_ad(token, ad_account, name, adset_id, creative_id, status="PAUSED"):
    """Create ad. Does NOT accept tracking_specs — pixel is on adset."""
    return api_post(
        f"{ad_account}/ads",
        token,
        {
            "name": name,
            "adset_id": adset_id,
            "creative": {"creative_id": creative_id},
            "status": status,
        },
    )


# ──────────────────────────────────────────────────────────────────────────
# Fix / repair helpers
# ──────────────────────────────────────────────────────────────────────────

def fix_creative_ig(token, ad_account, ad_id, ig_user_id, page_id,
                    url_tags=None):
    """
    Fix an ad whose creative has wrong IG structure.
    Strategy: fetch current creative, rebuild object_story_spec with
    instagram_user_id INSIDE, create new creative, point ad to it.
    """
    # 1. Get current ad + creative
    ad = api_get(ad_id, token, {"fields": "creative{id}"})
    if "error" in ad:
        return {"error": ad["error"]}
    old_creative_id = ad["creative"]["id"]

    # 2. Get full creative structure
    old = api_get(
        old_creative_id,
        token,
        {"fields": "name,object_story_spec,asset_feed_spec"},
    )
    if "error" in old:
        return {"error": old["error"]}

    # 3. Rebuild OSS with IG inside
    oss = dict(old.get("object_story_spec", {}))
    if page_id:
        oss["page_id"] = page_id
    oss["instagram_user_id"] = ig_user_id
    # Strip read-only fields
    for k in ("id", "effective_instagram_media_id",
              "effective_instagram_story_id", "effective_object_story_id"):
        oss.pop(k, None)

    # 4. Create new creative
    new_params = {
        "name": old.get("name", "fixed") + " [IG-FIX]",
        "object_story_spec": oss,
    }
    if url_tags:
        new_params["url_tags"] = url_tags
    if "asset_feed_spec" in old:
        new_params["asset_feed_spec"] = old["asset_feed_spec"]

    new = api_post(f"{ad_account}/adcreatives", token, new_params)
    if "error" in new:
        return {"error": new["error"]}
    new_creative_id = new["id"]

    # 5. Point ad to new creative
    update = api_post(
        ad_id,
        token,
        {"creative": {"creative_id": new_creative_id}},
    )
    if "error" in update:
        return {"error": update["error"]}

    return {
        "ok": True,
        "ad_id": ad_id,
        "old_creative": old_creative_id,
        "new_creative": new_creative_id,
    }
