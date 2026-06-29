"""Cola social_inbox en Supabase via REST (PostgREST). Service role key (bypassa RLS)."""
import json
import urllib.request
import urllib.parse
import urllib.error

from . import secrets

TABLE = "social_inbox"


def _headers(key, extra=None):
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _req(method, url, key, body=None, extra_headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, method=method, data=data, headers=_headers(key, extra_headers))
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else []
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase {e.code}: {e.read().decode('utf-8','replace')[:300]}")


def _normalize(rows):
    """PostgREST exige que TODOS los objetos del bulk tengan el mismo set de llaves."""
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())
    return [{k: r.get(k) for k in all_keys} for r in rows]


def upsert(rows):
    """Inserta/actualiza por external_id. No pisa status/draft existentes (ignore-duplicates)."""
    if not rows:
        return 0
    rows = _normalize(rows)
    url_base, key = secrets.supabase()
    url = f"{url_base}/rest/v1/{TABLE}?on_conflict=external_id"
    # merge-duplicates re-escribiria; usamos ignore-duplicates para NO resucitar items ya gestionados
    extra = {"Prefer": "resolution=ignore-duplicates,return=representation"}
    res = _req("POST", url, key, body=rows, extra_headers=extra)
    return len(res) if isinstance(res, list) else 0


def fetch(status=None, client=None, select="*", order="age_days.desc.nullslast", limit=500):
    url_base, key = secrets.supabase()
    params = {"select": select, "limit": str(limit), "order": order}
    if status:
        params["status"] = f"eq.{status}"
    if client:
        params["client"] = f"eq.{client}"
    url = f"{url_base}/rest/v1/{TABLE}?{urllib.parse.urlencode(params)}"
    return _req("GET", url, key)


def get_secret(key):
    url_base, sb_key = secrets.supabase()
    url = f"{url_base}/rest/v1/social_secrets?key=eq.{urllib.parse.quote(key)}&select=value"
    rows = _req("GET", url, sb_key)
    return rows[0]["value"] if rows else None


def update(external_id, fields):
    url_base, key = secrets.supabase()
    url = f"{url_base}/rest/v1/{TABLE}?external_id=eq.{urllib.parse.quote(external_id)}"
    extra = {"Prefer": "return=representation"}
    return _req("PATCH", url, key, body=fields, extra_headers=extra)
