#!/usr/bin/env python3
"""
serve_dashboard.py — Sirve dashboard.html del batch en :8767 con auto-regen on access.

Cada GET regenera el dashboard (sync attachments + detect outputs) antes de servir.
Esto significa: descargás un PNG → recargás browser → status flip a ✓ COMPLETADO.

POST /__update_score actualiza el score del prompt en batch.json (escrito por el JS del dashboard).

Uso:
    python3 serve_dashboard.py {batch_dir}
    python3 serve_dashboard.py {batch_dir} --port 8767
"""
import argparse
import json
import sys
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
GENERATE_DASHBOARD = SCRIPT_DIR / "generate_dashboard.py"


class BatchHandler(SimpleHTTPRequestHandler):
    batch_dir: Path = None

    def do_GET(self):
        # Regenerate dashboard on every GET to root or dashboard.html
        path = urlparse(self.path).path
        if path in ("/", "/dashboard.html"):
            try:
                subprocess.run(
                    ["/usr/bin/python3", str(GENERATE_DASHBOARD), str(self.batch_dir)],
                    check=True, capture_output=True, timeout=10
                )
            except subprocess.CalledProcessError as e:
                self.send_error(500, f"generate_dashboard failed: {e.stderr.decode()[:300]}")
                return
            if path == "/":
                self.path = "/dashboard.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/__update_score":
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode())
            num = data.get("num")
            score = data.get("score", "").strip() or None

            bj = self.batch_dir / "batch.json"
            batch = json.loads(bj.read_text(encoding="utf-8"))
            for pr in batch["prompts"]:
                if pr["num"] == num:
                    pr["score"] = score
                    break
            bj.write_text(json.dumps(batch, indent=2, ensure_ascii=False), encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return
        self.send_error(404)

    def log_message(self, fmt, *args):
        # Quiet output — only errors
        if "error" in (fmt % args).lower():
            super().log_message(fmt, *args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    batch_dir = Path(args.batch_dir).expanduser().resolve()
    if not (batch_dir / "batch.json").exists():
        sys.exit(f"❌ batch.json no encontrado en {batch_dir}")

    BatchHandler.batch_dir = batch_dir

    import os
    os.chdir(batch_dir)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), BatchHandler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"🌀 Soul Prep Dashboard sirviendo en {url}")
    print(f"   Batch: {batch_dir}")
    print(f"   Ctrl+C para detener.")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server detenido.")


if __name__ == "__main__":
    main()
