#!/usr/bin/env python3
"""Build the F24 follow-up cron (scenario 5278490) blueprint.

SOURCE OF TRUTH = f24_followup_blueprint.template.json (key-free; the GHL PIT token
is injected at build time). This replaced the old *parametric* generator on
2026-07-05 because the live scenario had diverged from it and the old generator
would have reverted prod:

  • Gibran (2026-06-29, "v3.4") hand-added `next_due_at` scheduling, a "due o sin
    agendar" filter (module 2), a reschedule route (module 50), and a janitor route
    (modules 100-103); interval 600 → 28800 (8h).
  • Pedro (2026-07-05) cost-optimized: removed the janitor route (redundant with the
    standalone janitor scenario 5528009, which does it server-side via
    contacts/search?tags=bot-pausado) and guarded module 2's empty-branch with
    followup_stage < 6 so COMPLETED ladders (stage 6, next_due_at="") stop being
    reprocessed every run.

The template captures that exact live structure, so `build()` output == prod
(verified by diffing flow against the live blueprint). The old generative version
(NUDGES/STEP_GAP/etc. as Python knobs) lives in git history before this commit —
to change a nudge message or gap now, edit the IML strings in the template JSON.

LADDER (unchanged): 2 (2h text) → 3 (~22.5h text) → 4/5/6 (d3/d8/d18 via tag
f24-send-dN → GHL Workflow relay sends the Meta template). Main bot resets
followup_stage=0 on inbound → reactivation.

Run:  GHL_API_KEY=<pit-token> python build_f24_followup_blueprint.py
        → /tmp/f24_followup_bp.json   (token also read from clients/f24/.env if present)
Deploy: PATCH the JSON to scenario 5278490 (us2.make.com). No CI auto-deploys this.
"""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
F24_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
ENV_PATH = os.path.join(F24_ROOT, ".env")
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "f24_followup_blueprint.template.json")
OUTPUT_PATH = "/tmp/f24_followup_bp.json"

SCENARIO_ID = 5278490
INTERVAL_SECONDS = 28800  # 8h — matches live 5278490
TOKEN_PLACEHOLDER = "__GHL_TOKEN__"


def _read_env(path, key, default=""):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return default


def get_token():
    # env var wins (CI/local override); fall back to clients/f24/.env; else PENDING.
    return os.environ.get("GHL_API_KEY") or _read_env(ENV_PATH, "GHL_API_KEY", "__PENDING__")


def build():
    """Return (blueprint_dict, token). Injects the GHL token into the template and
    re-attaches scheduling + interface (stripped by Make's GET /blueprint)."""
    token = get_token()
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        raw = f.read()
    bp = json.loads(raw.replace(TOKEN_PLACEHOLDER, token))
    bp["scheduling"] = {"type": "indefinitely", "interval": INTERVAL_SECONDS}
    bp["interface"] = {"input": [], "output": []}
    return bp, token


if __name__ == "__main__":
    bp, token = build()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(bp, f, ensure_ascii=False, separators=(",", ":"))
    router = next(m for m in bp["flow"] if m.get("id") == 6)
    print(f"Output: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH)} bytes)")
    print(f"Scenario: {SCENARIO_ID} | interval: {bp['scheduling']['interval']}s | "
          f"router routes: {len(router['routes'])} (expect 4, janitor removed)")
    print(f"GHL token: {'OK' if not token.startswith('__PENDING') else 'PENDIENTE (no GHL_API_KEY / .env)'}")
