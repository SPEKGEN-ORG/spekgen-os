#!/usr/bin/env python3
"""
pull_meta_metrics.py — LF Meta Ads metrics pull script

Usage:
  python3 pull_meta_metrics.py --days 3 --batch BATCH_LF_2026-05-05-v1
  python3 pull_meta_metrics.py --days 7 --all-active
  python3 pull_meta_metrics.py --account-summary --days 7
  python3 pull_meta_metrics.py --days 7 --ad-ids 120244843921000731,120244843922340731

Output:
  --batch / --all-active / --ad-ids: per-ad table (json + markdown)
  --account-summary: cuenta-nivel snapshot

Required env (loaded from LF/.env):
  META_ACCESS_TOKEN
"""
import argparse, json, os, sys, requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

LF_ENV = "/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/LF - LO FITNESS/.env"
load_dotenv(LF_ENV)

API = "v21.0"
TOKEN = os.environ.get("META_ACCESS_TOKEN")
AD_ACCOUNT = "act_542994632175434"

if not TOKEN:
    sys.exit("META_ACCESS_TOKEN missing in LF .env")

# LF calibration thresholds (from LOGS/LF/CALIBRATION.md)
LF_THRESHOLDS = {
    "aov_30d": 1230,
    "breakeven_cpa": 578,
    "breakeven_roas": 2.13,
    "cpa_target": 700,
    "roas_target": 2.5,
    "hook_min": 0.20,   # 20%
    "hold_min": 0.15,
    "ctr_min": 0.02,
    "freq_max_7d": 2.5,
    "cpmr_max": 340,
}

INSIGHTS_FIELDS = [
    "ad_id", "ad_name", "adset_name", "campaign_name",
    "spend", "impressions", "reach", "frequency",
    "clicks", "ctr", "cpm",
    "actions",  # includes purchases, video_view (3s/15s)
    "video_play_actions",  # alternative for video metrics
    "video_3_sec_watched_actions",
    "video_15_sec_watched_actions",
    "purchase_roas",
]

def get_insights(level, since, until, ad_ids=None):
    """Get insights from Meta API. level=ad|account."""
    url = f"https://graph.facebook.com/{API}/{AD_ACCOUNT}/insights"
    params = {
        "fields": ",".join(INSIGHTS_FIELDS) if level == "ad" else "spend,impressions,frequency,clicks,ctr,cpm,actions,purchase_roas",
        "level": level,
        "time_range": json.dumps({"since": since, "until": until}),
        "access_token": TOKEN,
        "limit": 500,
    }
    if level == "ad" and ad_ids:
        params["filtering"] = json.dumps([{"field": "ad.id", "operator": "IN", "value": ad_ids}])
    r = requests.get(url, params=params)
    if not r.ok:
        print("API ERROR:", r.text)
        r.raise_for_status()
    return r.json().get("data", [])

def parse_actions(actions_list, action_type):
    """Find a specific action_type in the actions array."""
    if not actions_list:
        return 0
    for a in actions_list:
        if a.get("action_type") == action_type:
            return float(a.get("value", 0))
    return 0

def evaluate_layer1(ad):
    """Apply LF Layer 1 thresholds. Returns (verdict, reasons)."""
    impressions = float(ad.get("impressions", 0))
    if impressions < 1000:
        return "INSUFFICIENT_DATA", ["<1000 impressions"]
    actions = ad.get("actions", [])
    video_3s = parse_actions(ad.get("video_3_sec_watched_actions") or actions, "video_view")
    if not video_3s:
        video_3s = parse_actions(actions, "video_view")
    hook_rate = video_3s / impressions if impressions else 0
    ctr = float(ad.get("ctr", 0)) / 100  # Meta returns CTR as %
    freq = float(ad.get("frequency", 0))
    cpm = float(ad.get("cpm", 0))
    purchases = parse_actions(actions, "purchase") or parse_actions(actions, "omni_purchase")
    spend = float(ad.get("spend", 0))
    roas_arr = ad.get("purchase_roas", [])
    roas = float(roas_arr[0]["value"]) if roas_arr else 0
    cpa = (spend / purchases) if purchases else 9999

    fails = []
    if hook_rate < LF_THRESHOLDS["hook_min"]:
        fails.append(f"hook {hook_rate*100:.1f}% <20%")
    if ctr < LF_THRESHOLDS["ctr_min"]:
        fails.append(f"ctr {ctr*100:.2f}% <2%")
    if freq > LF_THRESHOLDS["freq_max_7d"]:
        fails.append(f"freq {freq:.2f} >2.5")
    if cpm > LF_THRESHOLDS["cpmr_max"]:
        fails.append(f"cpm ${cpm:.0f} >$340")

    if not fails:
        verdict = "OK_CONTINUAR"
    elif len(fails) >= 3:
        verdict = "FALLA_TERMINAL"
    else:
        verdict = "FALLA_PARCIAL"

    return verdict, {
        "hook_rate": hook_rate,
        "ctr": ctr,
        "freq": freq,
        "cpm": cpm,
        "spend": spend,
        "purchases": purchases,
        "roas": roas,
        "cpa": cpa,
        "fails": fails,
    }

def fmt_table(rows):
    """Markdown table."""
    if not rows:
        return "(no data)"
    headers = ["ad_code", "spend", "impr", "freq", "hook%", "ctr%", "cpm", "purch", "roas", "cpa", "verdict"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"]*len(headers)) + "|"]
    for r in rows:
        m = r["metrics"]
        lines.append(f"| {r['ad_name']} | ${m['spend']:.0f} | {int(float(r.get('impressions', 0))):,} | {m['freq']:.2f} | {m['hook_rate']*100:.1f}% | {m['ctr']*100:.2f}% | ${m['cpm']:.0f} | {int(m['purchases'])} | {m['roas']:.2f}x | ${m['cpa']:.0f} | {r['verdict']} |")
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=3)
    p.add_argument("--batch", help="Batch ID (reads ads from batch.json)")
    p.add_argument("--all-active", action="store_true")
    p.add_argument("--ad-ids", help="comma-separated ad_ids")
    p.add_argument("--account-summary", action="store_true")
    p.add_argument("--out-dir", default="/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/SPK - SPEKGEN AGENCY/SPK - MEDIA BUYING OPS/LOGS/LF/PULLS")
    args = p.parse_args()

    until = datetime.now().strftime("%Y-%m-%d")
    since = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    if args.account_summary:
        data = get_insights("account", since, until)
        print(f"\n=== LF ACCOUNT {args.days}d ({since} → {until}) ===")
        if not data:
            print("(no data)")
            return
        d = data[0]
        spend = float(d.get("spend", 0))
        roas = float(d.get("purchase_roas", [{}])[0].get("value", 0)) if d.get("purchase_roas") else 0
        purchases = parse_actions(d.get("actions", []), "purchase") or parse_actions(d.get("actions", []), "omni_purchase")
        cpa = spend / purchases if purchases else 0
        freq = float(d.get("frequency", 0))
        cpm = float(d.get("cpm", 0))
        print(f"  spend:     ${spend:,.2f}")
        print(f"  purchases: {int(purchases)}")
        print(f"  ROAS:      {roas:.2f}x   (target {LF_THRESHOLDS['roas_target']:.2f}x)  {'🟢' if roas >= LF_THRESHOLDS['roas_target'] else '🟡' if roas >= LF_THRESHOLDS['breakeven_roas'] else '🔴'}")
        print(f"  CPA:       ${cpa:,.0f}    (target ${LF_THRESHOLDS['cpa_target']})  {'🟢' if cpa <= LF_THRESHOLDS['cpa_target'] else '🟡' if cpa <= LF_THRESHOLDS['cpa_target']*1.25 else '🔴'}")
        print(f"  Frequency: {freq:.2f}    (max {LF_THRESHOLDS['freq_max_7d']})  {'🟢' if freq < LF_THRESHOLDS['freq_max_7d'] else '🔴'}")
        print(f"  CPM:       ${cpm:.0f}     (max ${LF_THRESHOLDS['cpmr_max']})  {'🟢' if cpm <= LF_THRESHOLDS['cpmr_max'] else '🔴'}")
        out = {"window_days": args.days, "since": since, "until": until,
               "spend": spend, "purchases": purchases, "roas": roas, "cpa": cpa,
               "frequency": freq, "cpm": cpm}
        ts = datetime.now().strftime("%Y-%m-%d_%H%M")
        out_path = Path(args.out_dir) / f"account_{args.days}d_{ts}.json"
        out_path.write_text(json.dumps(out, indent=2))
        print(f"\nSaved: {out_path}")
        return

    # Per-ad
    ad_ids = None
    if args.ad_ids:
        ad_ids = args.ad_ids.split(",")
    elif args.batch:
        # Find batch.json
        # convention: SPK - 15. FACTORY/ads/LF/YYYY-MM/{batch_id}/batch.json
        batch_dir = None
        factory = Path("/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/SPK - SPEKGEN AGENCY/SPK - 15. FACTORY/ads/LF")
        for monthdir in factory.iterdir():
            cand = monthdir / args.batch
            if cand.exists():
                batch_dir = cand
                break
        if not batch_dir:
            sys.exit(f"Batch not found: {args.batch}")
        batch = json.load(open(batch_dir / "batch.json"))
        ad_ids = [e["meta_ad_id"] for e in batch["entries"] if e.get("meta_ad_id")]

    data = get_insights("ad", since, until, ad_ids=ad_ids)
    rows = []
    for ad in data:
        verdict, metrics = evaluate_layer1(ad)
        rows.append({
            "ad_id": ad.get("ad_id"),
            "ad_name": ad.get("ad_name"),
            "impressions": ad.get("impressions"),
            "verdict": verdict,
            "metrics": metrics,
        })

    print(f"\n=== LF PER-AD {args.days}d ({since} → {until}) ===\n")
    print(fmt_table(rows))

    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    label = args.batch or "all_active"
    out_path = Path(args.out_dir) / f"{label}_{args.days}d_{ts}.json"
    md_path  = Path(args.out_dir) / f"{label}_{args.days}d_{ts}.md"
    out_path.write_text(json.dumps(rows, indent=2))
    md_path.write_text(f"# LF Pull {args.days}d — {label}\n\n{since} → {until}\n\n{fmt_table(rows)}\n")
    print(f"\nSaved: {out_path}\n       {md_path}")

if __name__ == "__main__":
    main()
