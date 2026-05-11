#!/usr/bin/env python3
"""
generate_batch_log.py — Genera BATCH_LOG.md programáticamente desde batch.json.

Genera bloques A (pre-producción) / B (producción + scoring) / C (post-launch)
para cada ad. Source of truth para learning loop cross-batch.

Uso:
    # Generar bloque A solo (post-init batch, antes de generación)
    python3 generate_batch_log.py {BATCH_DIR} --block A

    # Generar bloques A+B (post-producción Web UI, pre-upload)
    python3 generate_batch_log.py {BATCH_DIR} --block AB

    # Generar bloques A+B+C completos (post-upload)
    python3 generate_batch_log.py {BATCH_DIR} --block ABC

    # Override path de salida
    python3 generate_batch_log.py {BATCH_DIR} --block ABC --out {PATH}

Default output path:
    SPK - MEDIA BUYING OPS/LOGS/{CLIENT}/BATCH_LOG.md

Modo:
  --regenerate (default): rewrite full BATCH_LOG.md
  --append: append solo nuevas entries (TBD, future)
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

LOGS_BASE = Path("/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/SPK - SPEKGEN AGENCY/SPK - MEDIA BUYING OPS/LOGS")

MAGIC_WORDS = [
    'subsurface scattering', 'catchlights', 'ambient occlusion',
    'contact shadows', 'micro-pores', 'individual fur', 'film grain',
    'chromatic aberration', 'Hasselblad', 'Sony', 'Canon',
    '4K native', 'Identity Lock', 'NEGATIVE',
]

AD_ACCOUNTS = {
    "LF": "542994632175434",
    "HC": "TBD",
    "GR": "TBD",
    "MG": "TBD",
}


def meta_link(client, ad_id):
    acct = AD_ACCOUNTS.get(client, "")
    return f"https://adsmanager.facebook.com/adsmanager/manage/ads/edit?act={acct}&selected_ad_ids={ad_id}"


def detect_magic_words(prompt):
    return [w for w in MAGIC_WORDS if w.lower() in (prompt or "").lower()]


def render_block_a(entry):
    """Bloque A — Pre-producción (siempre disponible desde init)."""
    out = ["### A. PRE-PRODUCCIÓN\n"]
    out.append(f"- **Concept angle:** {entry.get('concept_angle', '?')}")
    out.append(f"- **Entity ID signature:** `{entry.get('entity_id_signature', '?')}`")
    out.append(f"- **Hook on image:** \"{entry.get('hook_text_on_image', '?')}\"")
    out.append(f"- **Aspect ratio:** {entry.get('aspect_ratio', '4:5')}")
    magic = detect_magic_words(entry.get('gemini_prompt', ''))
    out.append(f"- **Magic words:** {', '.join(magic) if magic else '(none — REVISAR)'}")
    out.append(f"- **Attachments:**")
    for a in entry.get('extra_attachments', []):
        out.append(f"  - `{a}`")
    out.append(f"- **Expected outcome:** {entry.get('expected_outcome', '?')}")
    ac = entry.get('ad_copy', {})
    out.append(f"- **Ad copy:**")
    out.append(f"  - Headline: `{ac.get('headline', '?')}`")
    out.append(f"  - Description: `{ac.get('description', '?')}`")
    out.append(f"  - CTA: `{ac.get('cta_type', '?')}`  ·  Landing: `{ac.get('landing_url', '?')}`")
    if entry.get('notes'):
        out.append(f"- **Notas:** {entry['notes']}")
    out.append(f"\n<details><summary>Prompt SCALIST completo</summary>\n")
    out.append("```")
    out.append(entry.get('gemini_prompt', '(no prompt)'))
    out.append("```")
    out.append("</details>\n")
    return "\n".join(out)


def render_block_b(entry):
    """Bloque B — Producción Web UI (iter + score)."""
    out = ["### B. PRODUCCIÓN (Web UI Gemini)\n", "```"]

    iter_winner = entry.get('iter_winner') or '?'
    score = entry.get('claude_score') or {}
    if isinstance(score, dict) and score.get('avg'):
        out.append(f"STATUS: COMPLETED")
        out.append(f"Iter winner: {iter_winner}")
        scores_str = f"{score.get('tex','?')}/{score.get('lit','?')}/{score.get('ana','?')}/{score.get('typ','?')}/{score.get('coh','?')}"
        out.append(f"Score (texture/lighting/anatomy/typography/cohesion): {scores_str}  →  promedio: {score.get('avg','?')}/10")
        out.append(f"Source: {score.get('source', 'Claude visual scoring')}")
        if score.get('note'):
            out.append(f"Note: {score['note']}")
    elif entry.get('final_image_path'):
        out.append(f"STATUS: COMPLETED (sin score dictado)")
        out.append(f"Iter winner: {iter_winner}")
        out.append(f"Score: pendiente — Gibran puede dictar para appendear")
    else:
        out.append(f"STATUS: PENDING")
        out.append(f"Iter winner: -")
        out.append(f"Score: -")

    out.append(f"Imagen path: {entry.get('final_image_path', '-')}")
    out.append("```\n")
    return "\n".join(out)


def render_block_c(entry, client):
    """Bloque C — Post-launch (upload + métricas 72h/7d)."""
    out = ["### C. POST-LAUNCH\n", "```"]
    ad_id = entry.get('meta_ad_id')
    if ad_id:
        out.append(f"Meta ad_id:       {ad_id}")
        out.append(f"Meta creative_id: {entry.get('meta_creative_id', '?')}")
        out.append(f"Meta image_hash:  {entry.get('meta_image_hash', '?')}")
        out.append(f"Ads Manager:      {meta_link(client, ad_id)}")
        out.append(f"Upload date:      {entry.get('upload_date', 'TBD')}")
        out.append(f"Initial status:   {entry.get('initial_status', 'PAUSED → ACTIVE')}")
    else:
        out.append(f"STATUS: NOT UPLOADED YET")

    out.append("")
    metrics_72h = entry.get('metrics_72h') or {}
    metrics_7d = entry.get('metrics_7d') or {}
    if metrics_72h:
        m = metrics_72h
        out.append(f"72h:  spend ${m.get('spend',0):.0f} · impr {m.get('impr',0)} · freq {m.get('freq',0):.2f} · hook {m.get('hook',0)*100:.1f}% · hold {m.get('hold',0)*100:.1f}% · CTR {m.get('ctr',0)*100:.2f}% · CPM ${m.get('cpm',0):.0f} · purch {m.get('purch',0)} · ROAS {m.get('roas',0):.2f}x")
    else:
        out.append(f"72h:  PENDING")
    if metrics_7d:
        m = metrics_7d
        out.append(f"7d:   spend ${m.get('spend',0):.0f} · impr {m.get('impr',0)} · freq {m.get('freq',0):.2f} · hook {m.get('hook',0)*100:.1f}% · hold {m.get('hold',0)*100:.1f}% · CTR {m.get('ctr',0)*100:.2f}% · CPM ${m.get('cpm',0):.0f} · purch {m.get('purch',0)} · ROAS {m.get('roas',0):.2f}x")
    else:
        out.append(f"7d:   PENDING")
    out.append("")
    out.append(f"Decisión 7d: {entry.get('decision_7d', 'PENDING')}")
    out.append("```\n")
    return "\n".join(out)


def render_dropped(entry):
    """Render entries with status=DROPPED (no blocks A/B/C, just reason)."""
    return f"**Status:** ❌ **DROPPED**\n\n**Reason:** {entry.get('notes', '-')}\n\n**Bucket impact:** Concept rechazado, slot del bucket queda vacío hasta próximo batch.\n"


def render_batch_log(batch, blocks="ABC"):
    """Generate full BATCH_LOG.md content."""
    out = ["# LF — BATCH LOG\n",
           "> Cada batch creativo producido. Una entrada por ad.",
           "> Append-only. Bloques A (pre), B (producción), C (post-launch).",
           "> Generado por `factory-batch/scripts/generate_batch_log.py`.\n",
           "---\n"]

    out.append(f"# BATCH `{batch.get('batch_id', '?')}`\n")
    out.append(f"**Created:** {batch.get('created', '?')}  ·  **Type:** {batch.get('type', '?')}  ·  **Client:** {batch.get('client', '?')}")
    out.append(f"**Model:** `{batch.get('model_used', '?')}`")
    if batch.get('compliance_check'):
        out.append(f"**Compliance:** {', '.join(batch['compliance_check'])}")
    out.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Summary stats
    entries = batch.get('entries', [])
    by_status = {}
    for e in entries:
        s = e.get('status', 'UNKNOWN')
        by_status[s] = by_status.get(s, 0) + 1
    summary = " · ".join(f"{n} {s}" for s, n in sorted(by_status.items()))
    out.append(f"**Summary:** {len(entries)} ads total — {summary}\n")
    out.append("---\n")

    client = batch.get('client', 'LF')
    for entry in entries:
        code = entry.get('ad_code', '?')
        out.append(f"## {code}\n")
        out.append(f"**Bucket:** `{entry.get('format', '?')}`  ·  **Producto:** {entry.get('product', '?')}  ·  **Destination:** {entry.get('destination_adset', '?')}\n")

        if entry.get('status') == 'DROPPED':
            out.append(render_dropped(entry))
            out.append("---\n")
            continue

        if "A" in blocks:
            out.append(render_block_a(entry))
        if "B" in blocks:
            out.append(render_block_b(entry))
        if "C" in blocks:
            out.append(render_block_c(entry, client))
        out.append("---\n")

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    ap.add_argument("--block", default="ABC", choices=["A", "AB", "ABC"])
    ap.add_argument("--out", help="Override output path (default: LOGS/{CLIENT}/BATCH_LOG.md)")
    ap.add_argument("--print-only", action="store_true", help="Print to stdout, no file write")
    args = ap.parse_args()

    batch_dir = Path(args.batch_dir).expanduser().resolve()
    json_path = batch_dir / "batch.json"
    if not json_path.exists():
        print(f"❌ No batch.json en {batch_dir}", file=sys.stderr)
        sys.exit(1)

    batch = json.loads(json_path.read_text(encoding="utf-8"))
    client = batch.get('client', 'LF')

    content = render_batch_log(batch, blocks=args.block)

    if args.print_only:
        print(content)
        return

    out_path = Path(args.out) if args.out else (LOGS_BASE / client / "BATCH_LOG.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"✅ BATCH_LOG.md generado ({len(content)} chars, blocks={args.block})")
    print(f"   → {out_path}")


if __name__ == "__main__":
    main()
