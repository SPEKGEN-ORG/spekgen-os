#!/usr/bin/env python3
"""
run_cloud.py — Variante de run.py para ejecutar en GitHub Actions / cloud.
En vez de leer .env locales, lee tokens + ad_account_ids desde variables de
entorno inyectadas por el workflow. No abre archivos al terminar.

Genera HTML + PDF + actions.json en --out-dir.

ENV necesarios:
  META_TOKEN               (fallback si no hay token especifico)
  META_TOKEN_GR / _HC / _LF  (tokens por cuenta, override)
  META_AD_ACCOUNT_GR / _HC / _LF
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
import urllib.request
import urllib.error

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import detect_actions  # noqa: E402
import render_report  # noqa: E402

API = "https://graph.facebook.com/v21.0"

CLIENTS = ("GR", "HC", "LF")


def get_token(client: str) -> str | None:
    specific = os.environ.get(f"META_TOKEN_{client}")
    if specific:
        return specific
    return os.environ.get("META_TOKEN")


def get_account(client: str) -> str | None:
    return os.environ.get(f"META_AD_ACCOUNT_{client}")


def http_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "spekgen-xclient-cloud/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()}") from None


def pull_insights(act_id: str, token: str, days: int) -> list:
    act = act_id if act_id.startswith("act_") else f"act_{act_id}"
    until = datetime.utcnow().date()
    since = until - timedelta(days=days)
    params = {
        "access_token": token,
        "level": "ad",
        "time_range": json.dumps({"since": since.isoformat(), "until": until.isoformat()}),
        "fields": "ad_id,ad_name,campaign_name,adset_name,spend,impressions,reach,clicks,ctr,cpm,cpc,frequency,actions,action_values",
        "limit": 500,
    }
    url = f"{API}/{act}/insights?{urlencode(params)}"
    rows = []
    while url:
        data = http_get(url)
        rows.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--out-dir", type=str, required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Reuse the analyze_client function from the local pull script logic.
    # We inline it here to keep cloud self-contained without cross-Drive imports.
    # Copy of cross_client_pull.py logic (condensed):
    import re
    import statistics  # noqa: F401

    FORMAT_KEYWORDS = {
        "ORGANIC_BOOST": ["ORG_", "_ORG_"],
        "OFFER": ["OFFER", "OFERTA", "PROMO", "DESCUENTO", "DEAL", "2PACK", "KIT_OFFER"],
        "UGC_PERSONA": ["LUPITA", "UGC", "SELFIE", "PERSONA_", "TESTIMONIAL_UGC"],
        "PROBLEM_SOLUTION_SHORT": ["-PS-", "_PS_", "HC-AD-PS"],
        "TESTIMONIO": ["TESTIMONIO", "TESTIMONIAL", "REVIEW", "RESENA"],
        "PROBLEM_SOLUTION": ["PROBLEM_SOLUTION", "PROBLEM", "SYMPTOM", "SINTOMA", "PAIN"],
        "BENEFITS": ["BENEFIT", "BENEFICIO", "ICONBAR", "ICON_BAR"],
        "SCIENCE": ["SCIENCE", "CIENCIA", "STUDY", "ESTUDIO", "CLINICAL", "SABIAS_QUE", "SABIASQUE", "DID_YOU_KNOW"],
        "BILLBOARD": ["BILLBOARD", "BOFU"],
        "CAROUSEL": ["CARRUSEL", "CAROUSEL", "CARRUS", "PERCEPCION"],
        "BEFORE_AFTER": ["BEFORE", "ANTES", "AFTER", "DESPUES", "TRANSFORM"],
        "AUTHORITY": ["AUTHORITY", "EXPERT", "DOCTOR", "VETERINARIO", "MV_"],
        "SCROLL_STOP": ["SCROLL_STOP", "HOOK_", "REVEAL", "TEAR", "SCROLL"],
        "PROTOCOLO": ["PROTOCOLO", "PROTOCOL"],
        "EDITORIAL": ["EDITORIAL", "LINES"],
        "COLLECTION": ["COLLECTION", "KIT", "PACK"],
    }

    PRODUCTS = {
        "GR": ["PROTOCOLO", "GAXALIV", "BELLSAN", "COLAGENO", "GXAMIN", "HORMO_MEN", "HORMO", "ARTRIX"],
        "HC": ["GASTRODOG", "DOGRELAX", "ARTRIDOG", "OMEGADOG"],
        "LF": ["OMEGA3", "OMEGA", "METAFIT", "CITRATO_MG", "CITMG", "CITRATO_POTASIO", "CITPT", "KIT", "COLAGENO", "CREATINA", "VITAMIN"],
    }

    def tag_format(name: str, client: str) -> str:
        up = name.upper()
        for fmt, kws in FORMAT_KEYWORDS.items():
            for k in kws:
                if k in up:
                    return "PROBLEM_SOLUTION" if fmt == "PROBLEM_SOLUTION_SHORT" else fmt
        if client == "GR" and re.match(r"^GR-AD-\d+_", up):
            return "PRODUCT_FOCUS"
        return "UNCATEGORIZED"

    def tag_product(name: str, client: str) -> str:
        up = name.upper()
        for p in PRODUCTS.get(client, []):
            if p in up:
                return p
        return "OTHER"

    def safe_float(v, d=0.0):
        try:
            return float(v)
        except (TypeError, ValueError):
            return d

    def extract_purchases(row):
        p = 0
        v = 0.0
        for a in row.get("actions") or []:
            if a.get("action_type") in ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"):
                p = max(p, int(float(a.get("value", 0))))
        for a in row.get("action_values") or []:
            if a.get("action_type") in ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"):
                v = max(v, float(a.get("value", 0)))
        return p, v

    def analyze(client_code: str, rows: list) -> dict:
        parsed = []
        for r in rows:
            name = r.get("ad_name", "")
            spend = safe_float(r.get("spend"))
            imp = int(safe_float(r.get("impressions")))
            clk = int(safe_float(r.get("clicks")))
            pu, va = extract_purchases(r)
            parsed.append({
                "ad_id": r.get("ad_id"),
                "ad_name": name,
                "campaign": r.get("campaign_name", ""),
                "product": tag_product(name, client_code),
                "format": tag_format(name, client_code),
                "spend": spend,
                "impressions": imp,
                "clicks": clk,
                "ctr": safe_float(r.get("ctr")),
                "cpm": safe_float(r.get("cpm")),
                "cpc": safe_float(r.get("cpc")),
                "frequency": safe_float(r.get("frequency")),
                "purchases": pu,
                "purchase_value": va,
                "cpa": (spend / pu) if pu > 0 else None,
                "roas": (va / spend) if spend > 0 else 0.0,
            })
        active = [p for p in parsed if p["spend"] > 0]
        total_s = sum(p["spend"] for p in active)
        total_p = sum(p["purchases"] for p in active)
        total_v = sum(p["purchase_value"] for p in active)
        total_i = sum(p["impressions"] for p in active)
        total_c = sum(p["clicks"] for p in active)
        account_ctr = (total_c / total_i * 100) if total_i > 0 else 0
        by_format = {}
        for p in active:
            by_format.setdefault(p["format"], []).append(p)
        format_stats = {}
        for fmt, ads in by_format.items():
            s = sum(a["spend"] for a in ads)
            pu = sum(a["purchases"] for a in ads)
            va = sum(a["purchase_value"] for a in ads)
            imp = sum(a["impressions"] for a in ads)
            clk = sum(a["clicks"] for a in ads)
            format_stats[fmt] = {
                "ads_count": len(ads),
                "spend": round(s, 2),
                "purchases": pu,
                "revenue": round(va, 2),
                "ctr": round((clk / imp * 100), 3) if imp > 0 else 0,
                "cpa": round(s / pu, 2) if pu > 0 else None,
                "roas": round(va / s, 2) if s > 0 else 0,
            }
        return {
            "client": client_code,
            "ads_total": len(parsed),
            "ads_active": len(active),
            "account": {
                "spend": round(total_s, 2),
                "purchases": total_p,
                "revenue": round(total_v, 2),
                "ctr": round(account_ctr, 3),
                "cpa": round(total_s / total_p, 2) if total_p > 0 else None,
                "roas": round(total_v / total_s, 2) if total_s > 0 else 0,
            },
            "by_format": format_stats,
            "ads": active,
        }

    # Run the pull for each client
    results = {}
    for code in CLIENTS:
        tok = get_token(code)
        act = get_account(code)
        if not (tok and act):
            print(f"[{code}] MISSING secret META_TOKEN_{code} or META_AD_ACCOUNT_{code} — skipping", file=sys.stderr)
            continue
        print(f"[{code}] pulling last {args.days}d...", file=sys.stderr)
        try:
            rows = pull_insights(act, tok, args.days)
            results[code] = analyze(code, rows)
            print(f"[{code}] {len(rows)} rows, ${results[code]['account']['spend']:.0f} spend", file=sys.stderr)
        except Exception as e:
            print(f"[{code}] ERROR: {e}", file=sys.stderr)

    if not results:
        print("ERROR: no se obtuvo data de ningun cliente. Revisar secrets.", file=sys.stderr)
        sys.exit(1)

    # Save raw + actions
    (out_dir / f"pull_{datetime.now().strftime('%Y%m%d_%H%M')}.json").write_text(
        json.dumps(results, indent=2, default=str)
    )
    actions = detect_actions.run(results)
    (out_dir / f"actions_{datetime.now().strftime('%Y%m%d_%H%M')}.json").write_text(
        json.dumps(actions, indent=2, default=str)
    )
    (out_dir / f"pause_plan_{date_str}.json").write_text(json.dumps({
        "generated_at": datetime.now().isoformat(),
        "pauses": actions["pauses"],
    }, indent=2, default=str))

    # Render HTML + PDF
    h, p = render_report.render(results, actions, out_dir, date_str, days=args.days)
    print(f"HTML: {h}")
    print(f"PDF:  {p}")
    print(f"Pauses: {len(actions['pauses'])}, Winners: {len(actions['winners'])}, Plan: {len(actions['replication_plan'])}")


if __name__ == "__main__":
    main()
