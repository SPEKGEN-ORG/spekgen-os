"""F24 Shopify Admin API client.

Reusable across all F24 PDP scripts. Loads .env from the F24 client root,
handles OAuth client-credentials token (24h TTL, cached in logs/token.json),
exposes REST + GraphQL helpers, and Asset / Files / Metafields utilities.

Token is short-lived: re-mint automatically when expired.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

THIS_DIR = Path(__file__).resolve().parent
LIVE_BUILD = THIS_DIR.parent
WEBSITE_DIR = LIVE_BUILD.parent
F24_ROOT = WEBSITE_DIR.parent
ENV_PATH = F24_ROOT / ".env"
TOKEN_CACHE = LIVE_BUILD / "logs" / "token.json"

load_dotenv(ENV_PATH)

SHOP = os.environ["SHOPIFY_SHOP"].strip()
CLIENT_ID = os.environ["SHOPIFY_CLIENT_ID"].strip()
CLIENT_SECRET = os.environ["SHOPIFY_CLIENT_SECRET"].strip()
API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2024-10").strip()
THEME_ID = os.environ.get("SHOPIFY_THEME_ID", "").strip()
PRIMARY_DOMAIN = os.environ.get("SHOPIFY_PRIMARY_DOMAIN", "").strip()

BASE = f"https://{SHOP}/admin/api/{API_VERSION}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _load_cached_token() -> str | None:
    if not TOKEN_CACHE.exists():
        return None
    try:
        data = json.loads(TOKEN_CACHE.read_text())
        exp = datetime.fromisoformat(data["expires_at"])
        if exp > _now_utc() + timedelta(minutes=5):
            return data["access_token"]
    except Exception:
        return None
    return None


def _save_token(access_token: str, expires_in: int) -> None:
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE.write_text(json.dumps({
        "access_token": access_token,
        "expires_at": (_now_utc() + timedelta(seconds=expires_in)).isoformat(),
        "minted_at": _now_utc().isoformat(),
    }, indent=2))


def get_token(force_refresh: bool = False) -> str:
    if not force_refresh:
        cached = _load_cached_token()
        if cached:
            return cached
    r = requests.post(
        f"https://{SHOP}/admin/oauth/access_token",
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    token = data["access_token"]
    _save_token(token, data.get("expires_in", 86400))
    return token


def _headers(content_type: str = "application/json") -> dict[str, str]:
    return {
        "X-Shopify-Access-Token": get_token(),
        "Content-Type": content_type,
        "Accept": "application/json",
    }


def rest(method: str, path: str, payload: dict | None = None,
         params: dict | None = None, retries: int = 2) -> dict:
    """REST call. Path is relative to /admin/api/{ver}/, e.g. 'products.json'."""
    url = f"{BASE}/{path.lstrip('/')}"
    last_err = None
    for attempt in range(retries + 1):
        r = requests.request(
            method, url,
            headers=_headers(),
            json=payload if payload is not None else None,
            params=params,
            timeout=60,
        )
        if r.status_code == 401 and attempt == 0:
            get_token(force_refresh=True)
            continue
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", "2")))
            continue
        if r.status_code >= 400:
            last_err = f"{r.status_code} {r.text[:600]}"
            if r.status_code >= 500 and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError(f"Shopify REST error {method} {path}: {last_err}")
        return r.json() if r.text else {}
    raise RuntimeError(f"Shopify REST exhausted retries {method} {path}: {last_err}")


def graphql(query: str, variables: dict | None = None) -> dict:
    url = f"{BASE}/graphql.json"
    for attempt in range(3):
        r = requests.post(
            url,
            headers=_headers(),
            json={"query": query, "variables": variables or {}},
            timeout=60,
        )
        if r.status_code == 401 and attempt == 0:
            get_token(force_refresh=True)
            continue
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", "2")))
            continue
        r.raise_for_status()
        data = r.json()
        if data.get("errors"):
            raise RuntimeError(f"GraphQL errors: {json.dumps(data['errors'])[:800]}")
        return data["data"]
    raise RuntimeError("GraphQL exhausted retries")


def upload_asset(theme_id: str | int, key: str, content: str | bytes) -> dict:
    """PUT an asset (liquid section, json template, css, js) to a theme."""
    payload: dict[str, Any] = {"asset": {"key": key}}
    if isinstance(content, bytes):
        import base64
        payload["asset"]["attachment"] = base64.b64encode(content).decode("ascii")
    else:
        payload["asset"]["value"] = content
    return rest("PUT", f"themes/{theme_id}/assets.json", payload=payload)


def get_asset(theme_id: str | int, key: str) -> dict:
    return rest("GET", f"themes/{theme_id}/assets.json",
                params={"asset[key]": key})


def list_assets(theme_id: str | int) -> list[dict]:
    return rest("GET", f"themes/{theme_id}/assets.json").get("assets", [])


def upload_image_via_graphql(local_path: Path, alt: str = "") -> str:
    """Upload an image to Shopify Files and return its GraphQL Files API URL.

    Returns the CDN URL ready to be referenced from product media or theme.
    """
    if not local_path.exists():
        raise FileNotFoundError(local_path)
    filename = local_path.name
    mime = "image/jpeg" if filename.lower().endswith((".jpg", ".jpeg")) else \
           "image/png" if filename.lower().endswith(".png") else \
           "image/webp" if filename.lower().endswith(".webp") else "image/*"
    size = local_path.stat().st_size
    staged = graphql(
        """
        mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
          stagedUploadsCreate(input: $input) {
            stagedTargets { url resourceUrl parameters { name value } }
            userErrors { field message }
          }
        }
        """,
        variables={"input": [{
            "filename": filename, "mimeType": mime, "resource": "FILE",
            "fileSize": str(size), "httpMethod": "POST",
        }]},
    )["stagedUploadsCreate"]
    if staged["userErrors"]:
        raise RuntimeError(f"stagedUploadsCreate errors: {staged['userErrors']}")
    target = staged["stagedTargets"][0]

    form_data = [(p["name"], p["value"]) for p in target["parameters"]]
    with local_path.open("rb") as fh:
        files = {"file": (filename, fh, mime)}
        up = requests.post(target["url"], data=form_data, files=files, timeout=180)
        up.raise_for_status()

    file_create = graphql(
        """
        mutation fileCreate($files: [FileCreateInput!]!) {
          fileCreate(files: $files) {
            files { id alt preview { image { url } } ... on MediaImage { image { url } } }
            userErrors { field message }
          }
        }
        """,
        variables={"files": [{
            "originalSource": target["resourceUrl"],
            "contentType": "IMAGE",
            "alt": alt or filename,
        }]},
    )["fileCreate"]
    if file_create["userErrors"]:
        raise RuntimeError(f"fileCreate errors: {file_create['userErrors']}")
    f = file_create["files"][0]
    url = (f.get("image") or {}).get("url") or (f.get("preview") or {}).get("image", {}).get("url")
    return url or f["id"]


def attach_image_to_product(product_id: int, image_src: str, alt: str = "",
                            position: int | None = None) -> dict:
    payload = {"image": {"src": image_src, "alt": alt}}
    if position:
        payload["image"]["position"] = position
    return rest("POST", f"products/{product_id}/images.json", payload=payload)


def set_metafield(owner_id: int, owner_resource: str, namespace: str,
                  key: str, type_: str, value: Any) -> dict:
    """REST metafields are scoped by owner via resource path."""
    payload = {"metafield": {
        "namespace": namespace,
        "key": key,
        "type": type_,
        "value": value if isinstance(value, str) else json.dumps(value),
    }}
    path = f"{owner_resource}/{owner_id}/metafields.json"
    return rest("POST", path, payload=payload)


def ping() -> dict:
    return rest("GET", "shop.json").get("shop", {})


if __name__ == "__main__":
    shop = ping()
    print(json.dumps({
        "shop": shop.get("myshopify_domain"),
        "name": shop.get("name"),
        "primary_domain": shop.get("primary_domain", {}).get("host"),
        "theme_id_env": THEME_ID,
        "api_version": API_VERSION,
    }, indent=2))
