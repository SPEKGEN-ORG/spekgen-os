#!/usr/bin/env python3
"""
serve_dashboard.py — Levanta http.server local en el BATCH dir.

Necesario porque el dashboard usa fetch('ads_batch.json') — no funciona
via file:// por CORS. Puerto default 8766.

NOTA: 8765 está reservado para SPEKGEN Operations Hub (permanente, siempre
corriendo desde el Dock). Factory usa 8766 para evitar colisión. Ver
SPK - SPEKGEN AGENCY/_PORTS_REGISTRY.md.

Uso:
    python3 serve_dashboard.py {PATH_BATCH_DIR}
    python3 serve_dashboard.py --port 8767 {PATH_BATCH_DIR}

Abre http://localhost:8766/ads_batch.html en el navegador.
"""
import argparse
import http.server
import os
import socketserver
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir", help="Path a BATCH_{fecha}-v{N}")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    batch = Path(args.batch_dir).expanduser().resolve()
    # Buscar dashboard: primero dashboard.html (nuevo), fallback ads_batch.html (legacy v4.1)
    html_file = None
    for candidate in ("dashboard.html", "ads_batch.html"):
        if (batch / candidate).exists():
            html_file = candidate
            break
    if html_file is None:
        print(f"[serve] ERROR: no se encontro dashboard.html ni ads_batch.html en {batch}", file=sys.stderr)
        sys.exit(1)

    os.chdir(batch)
    url = f"http://localhost:{args.port}/{html_file}"

    if not args.no_open:
        try:
            subprocess.Popen(["open", url])
        except FileNotFoundError:
            pass

    Handler = http.server.SimpleHTTPRequestHandler
    # ReuseAddr evita "address already in use" tras cerrar rapido
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", args.port), Handler) as httpd:
        print(f"[serve] {batch}")
        print(f"[serve] -> {url}")
        print("[serve] Ctrl+C para parar")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[serve] bye")


if __name__ == "__main__":
    main()
