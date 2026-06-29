"""Carga de secretos: variable de entorno primero (GH Actions), fallback a .env del Drive (local).
NUNCA loguea valores."""
import os
import functools

DRIVE = os.environ.get(
    "SPEKGEN_DRIVE",
    "/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL",
)


@functools.lru_cache(maxsize=None)
def _read_drive_env(rel_path):
    path = os.path.join(DRIVE, rel_path)
    out = {}
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def get(env_name, drive_env=None, key=None, required=True, default=None):
    """env var -> .env del Drive -> default."""
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    if drive_env and key:
        val = _read_drive_env(drive_env).get(key)
        if val:
            return val
    if required and default is None:
        raise RuntimeError(f"Secreto faltante: {env_name} (o {drive_env}:{key})")
    return default


def meta_token(token_ref_cfg):
    """token_ref_cfg = {'env':..,'drive_env':..,'key':..} de clients.json."""
    return get(token_ref_cfg["env"], token_ref_cfg.get("drive_env"), token_ref_cfg.get("key"))


def supabase():
    url = get("SUPABASE_URL", "SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/.env", "NEXT_PUBLIC_SUPABASE_URL")
    key = get("SUPABASE_SERVICE_ROLE_KEY", "SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/.env", "SUPABASE_SERVICE_ROLE_KEY")
    return url.rstrip("/"), key


def gmail_app_password():
    return get("SPEKGEN_GMAIL_APP_PASSWORD", "SPK - SPEKGEN AGENCY/.env", "SPEKGEN_GMAIL_APP_PASSWORD")


def anthropic_key():
    return get("ANTHROPIC_API_KEY", "SPK - SPEKGEN AGENCY/.env", "ANTHROPIC_API_KEY", required=False)
