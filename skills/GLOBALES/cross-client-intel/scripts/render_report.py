#!/usr/bin/env python3
"""
render_report.py — Reads cross-client pull JSON + detected actions, renders
HTML from the template, and converts to PDF via Playwright screenshot + img2pdf.

Usage (programmatic):
    from render_report import render
    html_path, pdf_path = render(pull_data, actions, out_dir, date_str, days=14)

Or CLI:
    python3 render_report.py <pull.json> <actions.json> <out_dir> [days]
"""
from __future__ import annotations
import html
import json
import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE_PATH = HERE / "templates" / "report.html.tmpl"

CLIENT_FULL = {"LF": "LO FITNESS", "GR": "GREENRAY", "HC": "HEALTHY CHUCHOS"}
CLIENT_PILL = {"LF": "pill-lf", "GR": "pill-gr", "HC": "pill-hc"}


def esc(v) -> str:
    return html.escape(str(v), quote=True)


def build_snapshot_stats(pull: dict) -> str:
    blocks = []
    total_spend = 0.0
    total_purch = 0
    total_rev = 0.0
    # Fixed client order (LF first — anchor)
    for code in ("LF", "GR", "HC"):
        if code not in pull:
            continue
        acc = pull[code].get("account", {})
        spend = float(acc.get("spend", 0) or 0)
        purch = int(acc.get("purchases", 0) or 0)
        rev = float(acc.get("revenue", 0) or 0)
        roas = acc.get("roas", 0) or 0
        total_spend += spend
        total_purch += purch
        total_rev += rev
        blocks.append(
            f'<div class="big-stat"><div class="label">{esc(CLIENT_FULL[code])}</div>'
            f'<div class="val">${spend:,.0f}</div>'
            f'<div class="sub">{purch} compras · ROAS {roas:.2f}</div></div>'
        )
    net_roas = (total_rev / total_spend) if total_spend else 0
    blocks.append(
        f'<div class="big-stat"><div class="label">TOTAL RED</div>'
        f'<div class="val">${total_spend:,.0f}</div>'
        f'<div class="sub">{total_purch} compras · ROAS {net_roas:.2f}</div></div>'
    )
    return "".join(blocks)


def build_network_read(pull: dict) -> str:
    total_spend = sum(float(pull[c].get("account", {}).get("spend", 0) or 0) for c in pull)
    total_rev = sum(float(pull[c].get("account", {}).get("revenue", 0) or 0) for c in pull)
    net_roas = (total_rev / total_spend) if total_spend else 0
    verdict = "rentable" if net_roas >= 2 else ("apenas rentable" if net_roas >= 1.5 else "por debajo de break-even ajustado")
    return f"<strong>Lectura red:</strong> ROAS consolidado {net_roas:.2f}x sobre ${total_spend:,.0f} spend — {verdict}. Revisar secciones 2 (leaks) y 4 (replicaciones) para subir el ROAS en la proxima ventana."


def build_pause_table(pauses: list) -> tuple[str, float]:
    if not pauses:
        return '<div class="empty">No se detectaron ads para pausar en esta ventana.</div>', 0.0
    total = 0.0
    rows = []
    for p in pauses:
        pill = CLIENT_PILL.get(p["client"], "")
        total += p["spend"]
        cpa_cell = f'${p["cpa"]:.0f}' if p.get("cpa") else "—"
        rows.append(
            f'<tr>'
            f'<td><span class="pill {pill}">{esc(p["client"])}</span></td>'
            f'<td><strong>{esc(p["ad_name"])}</strong></td>'
            f'<td>{esc(p.get("product") or "—")}</td>'
            f'<td>{esc(p.get("format") or "—")}</td>'
            f'<td class="num">${p["cpa_max"]}</td>'
            f'<td class="num kill">${p["spend"]:.0f}</td>'
            f'<td class="num">{p["purchases"]}</td>'
            f'<td class="num kill">{cpa_cell}</td>'
            f'<td class="kill">{esc(p["reason"])}</td>'
            f'</tr>'
        )
    table = (
        '<table><thead><tr>'
        '<th>Cliente</th><th>Ad</th><th>Producto</th><th>Formato</th>'
        '<th class="num">CPA max</th><th class="num">Spend</th><th class="num">Compras</th>'
        '<th class="num">CPA real</th><th>Razon</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
    )
    return table, total


def build_winners_table(winners: list) -> str:
    if not winners:
        return '<div class="empty">No hay winners claros en la ventana. Revisar si la red tiene spend suficiente.</div>'
    rows = []
    for w in winners:
        pill = CLIENT_PILL.get(w["client"], "")
        rows.append(
            f'<tr>'
            f'<td><span class="pill {pill}">{esc(w["client"])}</span></td>'
            f'<td><strong>{esc(w["ad_name"])}</strong></td>'
            f'<td>{esc(w.get("product") or "—")}</td>'
            f'<td>{esc(w.get("format") or "—")}</td>'
            f'<td class="num">${w["spend"]:.0f}</td>'
            f'<td class="num">{w["purchases"]}</td>'
            f'<td class="num">${w["cpa"]:.0f}</td>'
            f'<td class="num win">{w["roas"]:.2f}x</td>'
            f'<td class="num">${w["revenue"]:.0f}</td>'
            f'</tr>'
        )
    return (
        '<table><thead><tr>'
        '<th>Cliente</th><th>Ad</th><th>Producto</th><th>Formato</th>'
        '<th class="num">Spend</th><th class="num">Compras</th>'
        '<th class="num">CPA</th><th class="num">ROAS</th><th class="num">Revenue</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
    )


def build_replication_boxes(plan: list) -> str:
    if not plan:
        return '<div class="empty">No se detectaron oportunidades claras de replicacion en esta ventana.</div>'
    # Group by source -> target
    grouped = {}
    for p in plan:
        key = (p["source_client"], p["target_client"])
        grouped.setdefault(key, []).append(p)
    boxes = []
    for (src, tgt), items in sorted(grouped.items()):
        lis = "".join(
            f'<li><strong>{esc(it["format"])}</strong> — {esc(it["suggestion"])}</li>'
            for it in items
        )
        boxes.append(
            f'<div class="action-box">'
            f'<h4>{esc(src)} -> {esc(tgt)} (replicar a {esc(CLIENT_FULL.get(tgt, tgt))})</h4>'
            f'<ul>{lis}</ul></div>'
        )
    return "".join(boxes)


def build_watchlist(watch: list) -> str:
    if not watch:
        return '<div class="empty">Sin senales criticas que vigilar en el siguiente pull.</div>'
    items = "".join(f'<li>{esc(w)}</li>' for w in watch)
    return f'<ul>{items}</ul>'


def build_format_tables(pull: dict) -> str:
    out = []
    for code in ("LF", "GR", "HC"):
        if code not in pull:
            continue
        by_fmt = pull[code].get("by_format", {})
        if not by_fmt:
            continue
        rows = []
        for fmt, st in sorted(by_fmt.items(), key=lambda kv: -(kv[1].get("spend") or 0)):
            roas = st.get("roas", 0) or 0
            roas_cls = "win" if roas >= 2 else ("kill" if roas < 0.5 and st.get("spend", 0) > 100 else "")
            cpa = st.get("cpa")
            cpa_cell = f'${cpa:.0f}' if cpa else "—"
            rows.append(
                f'<tr>'
                f'<td>{esc(fmt)}</td>'
                f'<td class="num">{st.get("ads_count", 0)}</td>'
                f'<td class="num">${st.get("spend", 0):.0f}</td>'
                f'<td class="num">{st.get("purchases", 0)}</td>'
                f'<td class="num">{cpa_cell}</td>'
                f'<td class="num {roas_cls}">{roas:.2f}x</td>'
                f'<td class="num">{st.get("ctr", 0):.2f}%</td>'
                f'</tr>'
            )
        out.append(
            f'<h3>{esc(CLIENT_FULL[code])}</h3>'
            f'<table><thead><tr>'
            f'<th>Formato</th><th class="num">Ads</th><th class="num">Spend</th>'
            f'<th class="num">Compras</th><th class="num">CPA</th>'
            f'<th class="num">ROAS</th><th class="num">CTR</th>'
            f'</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )
    return "".join(out) or '<div class="empty">Sin data de formatos.</div>'


def render_html(pull: dict, actions: dict, date_str: str, days: int, filename: str) -> str:
    tmpl = TEMPLATE_PATH.read_text()
    snapshot = build_snapshot_stats(pull)
    network = build_network_read(pull)
    pause_table, pause_total = build_pause_table(actions.get("pauses", []))
    winners_table = build_winners_table(actions.get("winners", []))
    rep_boxes = build_replication_boxes(actions.get("replication_plan", []))
    watchlist = build_watchlist(actions.get("watchlist", []))
    format_tables = build_format_tables(pull)

    replacements = {
        "__DATE__": date_str,
        "__DAYS__": str(days),
        "__SNAPSHOT_STATS__": snapshot,
        "__NETWORK_READ__": network,
        "__PAUSE_TABLE__": pause_table,
        "__PAUSE_TOTAL__": f"{pause_total:,.0f}",
        "__WINNERS_TABLE__": winners_table,
        "__REPLICATION_BOXES__": rep_boxes,
        "__WATCHLIST__": watchlist,
        "__FORMAT_TABLES__": format_tables,
        "__FILENAME__": filename,
    }
    out = tmpl
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def html_to_pdf(html_str: str, pdf_path: Path) -> None:
    """Screenshot full page at 2x, save as JPEG 85%, convert to 1-page PDF via img2pdf."""
    from playwright.sync_api import sync_playwright
    from PIL import Image
    import img2pdf
    import tempfile

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1200, "height": 800}, device_scale_factor=2)
        page = ctx.new_page()
        page.set_content(html_str, wait_until="domcontentloaded")
        page.wait_for_timeout(200)
        png_bytes = page.screenshot(full_page=True, type="png")
        browser.close()

    # Convert PNG -> JPEG 85% in-memory
    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.save(tf.name, "JPEG", quality=85)
        jpg_path = tf.name
    try:
        with open(pdf_path, "wb") as fp:
            fp.write(img2pdf.convert(jpg_path))
    finally:
        try:
            os.unlink(jpg_path)
        except OSError:
            pass


def render(pull: dict, actions: dict, out_dir: Path, date_str: str, days: int = 14) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    filename_base = f"CROSS_CLIENT_INSIGHTS_{date_str}"
    html_path = out_dir / f"{filename_base}.html"
    pdf_path = out_dir / f"{filename_base}.pdf"

    html_str = render_html(pull, actions, date_str, days, filename_base + ".pdf")
    html_path.write_text(html_str)
    html_to_pdf(html_str, pdf_path)
    return html_path, pdf_path


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: render_report.py <pull.json> <actions.json> <out_dir> [days]", file=sys.stderr)
        sys.exit(1)
    pull = json.loads(Path(sys.argv[1]).read_text())
    actions = json.loads(Path(sys.argv[2]).read_text())
    out_dir = Path(sys.argv[3])
    days = int(sys.argv[4]) if len(sys.argv) > 4 else 14
    date_str = datetime.now().strftime("%Y-%m-%d")
    h, p = render(pull, actions, out_dir, date_str, days)
    print(f"HTML: {h}\nPDF:  {p}")
