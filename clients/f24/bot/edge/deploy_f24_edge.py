#!/usr/bin/env python3
"""Deploy F24 edge functions a Supabase (proyecto wjlwpfaogjpeqgyxxnwa, compartido con HC)
vía Management API. Mismo patrón que el deploy_edge.py de HC. NO contiene secretos: lee el
Supabase Personal Access Token del entorno o del .env de F24.

Token (una vez): https://supabase.com/dashboard/account/tokens → Generate → SUPABASE_ACCESS_TOKEN.

Uso:
    SUPABASE_ACCESS_TOKEN=sbp_xxx python edge/deploy_f24_edge.py
    # o con el token en clients/f24/.env:
    python edge/deploy_f24_edge.py
    python edge/deploy_f24_edge.py --only f24-order-paid   # deploya una sola

Antes de re-deployar una función EXISTENTE, baja la versión LIVE y avisa si difiere del disco
(SOP: la versión deployada es la fuente de verdad). Aborta el overwrite si hay drift salvo --force.
"""
import os, sys, json, uuid, urllib.request, urllib.error
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
F24_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # edge -> bot -> clients/f24
PROJECT_REF = "wjlwpfaogjpeqgyxxnwa"
FUNCTIONS = ["f24-mp-webhook", "f24-order-paid"]  # las 2 que toca este cambio
API = "https://api.supabase.com"


def load_env_token():
    tok = os.environ.get("SUPABASE_ACCESS_TOKEN")
    if tok:
        return tok
    envp = os.path.join(F24_ROOT, ".env")
    if os.path.exists(envp):
        for line in open(envp, encoding="utf-8"):
            line = line.strip()
            if line.startswith("SUPABASE_ACCESS_TOKEN=") and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


TOKEN = load_env_token()
if not TOKEN:
    raise SystemExit("FALTA SUPABASE_ACCESS_TOKEN (env o clients/f24/.env). "
                     "Genera un PAT en supabase.com/dashboard/account/tokens.")
H = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "SpekgenDeploy/1.0 (+curl/8.4)", "Accept": "application/json"}


def api_get_bytes(path):
    req = urllib.request.Request(API + path, headers=H)
    with urllib.request.urlopen(req) as r:
        return r.read()


def live_body(slug):
    """Baja el source LIVE de la función (o None si no existe / no se puede).
    El endpoint /body puede devolver un bundle eszip binario; en ese caso el decode
    falla y devolvemos el texto con reemplazos (el caller detecta que no es texto)."""
    try:
        raw = api_get_bytes(f"/v1/projects/{PROJECT_REF}/functions/{slug}/body")
        return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"  ⚠ no se pudo bajar el body live de {slug}: {e.code}")
        return None


def deploy(slug, force=False):
    fdir = os.path.join(HERE, slug)
    entry = os.path.join(fdir, "index.ts")
    if not os.path.exists(entry):
        print(f"  ✗ {slug}: no existe {entry}"); return False
    local = open(entry, encoding="utf-8").read()

    # SOP: la versión LIVE es la fuente de verdad. Antes de overwrite, baja el body live y compara.
    live = live_body(slug)
    if live is not None and live.strip():
        # Si el body no es texto legible (p.ej. eszip/binario), no podemos comparar → avisa y sigue.
        printable = sum(c.isprintable() or c in "\r\n\t" for c in live) / max(1, len(live))
        if printable < 0.85:
            print(f"  ⚠ {slug}: el body live no es texto plano ({printable:.0%} legible) — no se puede diffear; revisa en el dashboard antes de confiar.")
        else:
            ratio = SequenceMatcher(None, live, local).ratio()
            if ratio < 0.6 and not force:
                print(f"  ⚠ DRIFT en {slug}: similitud live↔disco = {ratio:.0%} (baja). Alguien pudo cambiar la función en vivo.")
                print(f"    live_len={len(live)} disk_len={len(local)}. Revisa y re-corre con --force si tu disco es lo correcto.")
                return False
            print(f"  · {slug}: similitud live↔disco {ratio:.0%} (ok, tu edición evoluciona la versión live)")

    boundary = "----f24deploy" + uuid.uuid4().hex
    parts = []

    def add(name, value, filename=None, ctype=None):
        head = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
        if filename:
            head += f'; filename="{filename}"'
        head += "\r\n"
        if ctype:
            head += f"Content-Type: {ctype}\r\n"
        head += "\r\n"
        parts.append(head.encode() + (value if isinstance(value, bytes) else value.encode()) + b"\r\n")

    add("metadata", json.dumps({"name": slug, "entrypoint_path": "index.ts", "verify_jwt": False}), ctype="application/json")
    add("file", local.encode(), filename="index.ts", ctype="application/typescript")
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()

    url = f"{API}/v1/projects/{PROJECT_REF}/functions/deploy?slug={slug}"
    req = urllib.request.Request(url, data=body, method="POST",
                                headers={**H, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        out = json.load(urllib.request.urlopen(req))
        print(f"  ✅ {slug} · version {out.get('version')} · status {out.get('status')}")
        return True
    except urllib.error.HTTPError as e:
        print(f"  ❌ {slug} FALLÓ {e.code}: {e.read().decode()[:400]}")
        return False


def main():
    force = "--force" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    targets = [only] if only else FUNCTIONS
    print(f"Deploy a Supabase {PROJECT_REF}: {', '.join(targets)}")
    okc = 0
    for slug in targets:
        if deploy(slug, force=force):
            okc += 1
    print(f"Listo: {okc}/{len(targets)} deployadas.")
    sys.exit(0 if okc == len(targets) else 1)


if __name__ == "__main__":
    main()
