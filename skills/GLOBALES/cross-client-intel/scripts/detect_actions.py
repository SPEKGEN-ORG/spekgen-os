#!/usr/bin/env python3
"""
detect_actions.py — Applies business rules to the cross-client pull to derive:
  - pause_list: ads that should be paused (CPA > price - 150, or spend > 100 with 0 buys)
  - winners: ads with ROAS >= 2 AND spend >= 50 AND purchases >= 1
  - replication_plan: for each winner format, which (client, product) gaps to fill

Pure function — no I/O, no Meta API calls. Takes dict, returns dict.
"""
from __future__ import annotations
import copy

# CPA max by (client, product key). Fallback 200 MXN.
CPA_MAX = {
    ("LF", "METAFIT"): 348,
    ("LF", "OMEGA3"): 240,
    ("LF", "OMEGA"): 240,
    ("LF", "CITRATO_MG"): 160,
    ("LF", "CITMG"): 160,
    ("LF", "CITRATO_POTASIO"): 160,
    ("LF", "CITPT"): 160,
    ("LF", "KIT"): 749,
    ("LF", "COLAGENO"): 240,
    ("LF", "CREATINA"): 240,
    ("LF", "VITAMIN"): 200,
    ("HC", "ARTRIDOG"): 200,
    ("HC", "DOGRELAX"): 200,
    ("HC", "GASTRODOG"): 200,
    ("HC", "OMEGADOG"): 230,
    ("GR", "ARTRIX"): 260,
    ("GR", "GXAMIN"): 260,
    ("GR", "HORMO"): 500,
    ("GR", "HORMO_MEN"): 500,
    ("GR", "COLAGENO"): 240,
    ("GR", "BELLSAN"): 170,
    ("GR", "GAXALIV"): 260,
    ("GR", "PROTOCOLO"): 1050,
}
DEFAULT_CPA_MAX = 200

# Minimum spend to trust a 0-purchases signal as "kill"
HARD_KILL_ZERO_SPEND = 100

# Winner thresholds
WINNER_MIN_SPEND = 50.0
WINNER_MIN_ROAS = 2.0
WINNER_MIN_PURCHASES = 1


def cpa_max_for(client: str, product: str) -> int:
    return CPA_MAX.get((client, product), DEFAULT_CPA_MAX)


def detect_pause_candidates(results: dict) -> list[dict]:
    out = []
    for client_code, bundle in results.items():
        for ad in bundle.get("ads", []):
            spend = float(ad.get("spend") or 0)
            purchases = int(ad.get("purchases") or 0)
            product = ad.get("product") or "OTHER"
            cpa_max = cpa_max_for(client_code, product)

            reason = None
            severity = None
            roas = float(ad.get("roas") or 0)
            # Override: si el ad tiene ROAS >= 2, NO pausar aunque CPA exceda max.
            # ROAS es la metrica ultima — CPA max es solo un proxy.
            if roas >= 2.0:
                pass  # keep — rentable
            elif purchases == 0 and spend >= HARD_KILL_ZERO_SPEND:
                reason = f"spend ${spend:.0f} con 0 compras en 14d"
                severity = "kill_zero"
            elif purchases > 0:
                cpa = spend / purchases
                if cpa > cpa_max:
                    reason = f"CPA real ${cpa:.0f} > max ${cpa_max} ({product}) y ROAS {roas:.2f}x < 2"
                    severity = "kill_over_cpa"

            if reason:
                out.append({
                    "client": client_code,
                    "ad_id": ad.get("ad_id"),
                    "ad_name": ad.get("ad_name"),
                    "product": product,
                    "format": ad.get("format"),
                    "spend": round(spend, 2),
                    "purchases": purchases,
                    "cpa": round(spend / purchases, 2) if purchases > 0 else None,
                    "cpa_max": cpa_max,
                    "roas": round(float(ad.get("roas") or 0), 2),
                    "reason": reason,
                    "severity": severity,
                })
    # Order: biggest spend leaks first
    out.sort(key=lambda x: -x["spend"])
    return out


def detect_winners(results: dict) -> list[dict]:
    out = []
    for client_code, bundle in results.items():
        for ad in bundle.get("ads", []):
            spend = float(ad.get("spend") or 0)
            purchases = int(ad.get("purchases") or 0)
            roas = float(ad.get("roas") or 0)
            if spend >= WINNER_MIN_SPEND and roas >= WINNER_MIN_ROAS and purchases >= WINNER_MIN_PURCHASES:
                out.append({
                    "client": client_code,
                    "ad_id": ad.get("ad_id"),
                    "ad_name": ad.get("ad_name"),
                    "product": ad.get("product"),
                    "format": ad.get("format"),
                    "spend": round(spend, 2),
                    "purchases": purchases,
                    "revenue": round(float(ad.get("purchase_value") or 0), 2),
                    "roas": round(roas, 2),
                    "cpa": round(spend / purchases, 2),
                })
    out.sort(key=lambda x: -x["roas"])
    return out


def build_replication_plan(results: dict, winners: list[dict]) -> list[dict]:
    """For each winner format in client X, find other clients where that format
    has spend < 30 MXN OR ads_count < 2. Emit replicate tasks."""
    # Coverage map: (client, format) -> spend, ads_count
    coverage = {}
    for client_code, bundle in results.items():
        for fmt, stats in bundle.get("by_format", {}).items():
            coverage[(client_code, fmt)] = {
                "spend": stats.get("spend", 0),
                "ads_count": stats.get("ads_count", 0),
            }

    all_clients = list(results.keys())
    plan = []
    seen = set()
    for w in winners:
        src = w["client"]
        fmt = w["format"]
        if fmt in ("UNCATEGORIZED", "PRODUCT_FOCUS"):
            continue
        for tgt in all_clients:
            if tgt == src:
                continue
            key = (src, tgt, fmt)
            if key in seen:
                continue
            cov = coverage.get((tgt, fmt), {"spend": 0, "ads_count": 0})
            if cov["spend"] < 30 or cov["ads_count"] < 2:
                plan.append({
                    "source_client": src,
                    "target_client": tgt,
                    "format": fmt,
                    "source_ad": w["ad_name"],
                    "source_product": w["product"],
                    "source_roas": w["roas"],
                    "source_spend": w["spend"],
                    "target_coverage_spend": cov["spend"],
                    "target_coverage_count": cov["ads_count"],
                    "suggestion": (
                        f"Crear {fmt} en {tgt} basado en {w['ad_name']} "
                        f"(ROAS {w['roas']}x con ${w['spend']:.0f} spend). "
                        f"Hoy {tgt} tiene solo ${cov['spend']:.0f} y {cov['ads_count']} ads de {fmt}."
                    ),
                })
                seen.add(key)
    # Dedupe by (target, format) keeping highest source_roas
    dedup = {}
    for p in plan:
        k = (p["target_client"], p["format"])
        if k not in dedup or p["source_roas"] > dedup[k]["source_roas"]:
            dedup[k] = p
    return sorted(dedup.values(), key=lambda x: -x["source_roas"])


def detect_watchlist(results: dict, winners: list[dict], pauses: list[dict]) -> list[str]:
    out = []
    # Winners with low spend deserve scaling test
    for w in winners:
        if w["spend"] < 100:
            out.append(
                f"{w['client']} — {w['ad_name']} tiene ROAS {w['roas']}x con solo "
                f"${w['spend']:.0f} spend. Probar escalar a 3x budget y medir si sostiene."
            )
    # Clients with 0-1 conversions
    for client, bundle in results.items():
        p = bundle.get("account", {}).get("purchases", 0)
        s = bundle.get("account", {}).get("spend", 0)
        if p <= 1 and s > 500:
            out.append(
                f"{client} — solo {p} compra(s) con ${s:.0f} spend en 14d. "
                f"Revisar funnel (landing, pixel, checkout) ademas de creative."
            )
    # Formats with high spend 0 ROAS
    for client, bundle in results.items():
        for fmt, st in bundle.get("by_format", {}).items():
            if st.get("spend", 0) > 300 and st.get("roas", 0) == 0:
                out.append(
                    f"{client} — formato {fmt} quemo ${st['spend']:.0f} con ROAS 0. "
                    f"Dejar de producir este formato hasta entender por que falla."
                )
    return out


def run(results: dict) -> dict:
    """Main entry: takes the cross_client_pull.py json output, returns analysis."""
    pauses = detect_pause_candidates(results)
    winners = detect_winners(results)
    plan = build_replication_plan(results, winners)
    watchlist = detect_watchlist(results, winners, pauses)
    return {
        "pauses": pauses,
        "winners": winners,
        "replication_plan": plan,
        "watchlist": watchlist,
    }


if __name__ == "__main__":
    import json
    import sys
    data = json.load(sys.stdin)
    print(json.dumps(run(data), indent=2, default=str))
