#!/usr/bin/env python3
"""
SPEKGEN — Campaign Architecture PDF Builder

Toma un JSON de entrada describiendo la arquitectura de una campana (cliente, campanas,
ad sets, ads con imagenes o placeholders, landings) y genera un PDF visual panoramico
(A3 landscape, 420x297mm) con thumbnails reales embebidos para cada ad.

Uso:
    python build_pdf.py <input.json>
    python build_pdf.py <input.json> --output /path/to/out.pdf

El JSON debe seguir el schema documentado en templates/schema.md.

Se apoya en:
    - Pillow para redimensionar + convertir a base64
    - Playwright (chromium) para HTML -> PDF

Dependencias:
    pip install pillow playwright
    playwright install chromium

El script:
    1. Lee el JSON
    2. Para cada ad con images_folder: carga PNG/JPG y los embebe como base64
    3. Para cada ad con placeholder=true: dibuja bloque "Pendiente"
    4. Construye HTML usando template interno (copiado de arquitectura HC v1)
    5. Llama a Playwright para renderizar a PDF
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow no instalado. pip install pillow", file=sys.stderr)
    sys.exit(1)


# ---------- Image loading & base64 ----------

def img_to_b64(path: Path, max_w: int = 260, quality: int = 82) -> str:
    """Carga una imagen, la redimensiona y la convierte a base64 JPEG."""
    img = Image.open(path).convert("RGB")
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def load_folder_images(folder: Path, max_w: int = 260) -> list[tuple[str, str]]:
    """Carga todas las imagenes PNG/JPG del folder ordenadas alfabeticamente."""
    if not folder.exists():
        print(f"  WARN: folder no existe: {folder}")
        return []
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files = sorted([p for p in folder.iterdir() if p.suffix.lower() in exts])
    return [(p.name, img_to_b64(p, max_w=max_w)) for p in files]


# ---------- HTML renderers ----------

def render_header(data: dict[str, Any]) -> str:
    meta = data.get("meta", {})
    metrics_html = ""
    for m in data.get("header_metrics", []):
        val_size = m.get("value_size", "14px")
        metrics_html += (
            f'<div class="metric">'
            f'<div class="label">{m["label"]}</div>'
            f'<div class="value" style="font-size:{val_size}">{m["value"]}</div>'
            f'</div>'
        )
    return f'''
    <div class="header">
      <div>
        <h1>{meta.get("title", "Arquitectura de Campana")}</h1>
        <div class="sub">{meta.get("subtitle", "")}</div>
        <div class="tagline">{meta.get("tagline", "")}</div>
      </div>
      <div class="metrics">{metrics_html}</div>
    </div>
    '''


def render_ad_card(ad: dict[str, Any], images_root: Path | None) -> str:
    pclass = ad.get("product_code", "marca")
    badge_class = "v" if ad.get("is_video") else ""
    metric_tier = ad.get("metric_tier", "high")
    metric_class = {
        "high": "wci",
        "mid": "wci mid",
        "low": "wci low",
        "tbd": "wci tbd",
    }.get(metric_tier, "wci")

    # Slides or placeholder
    placeholder = ad.get("placeholder", False)
    images_folder = ad.get("images_folder")
    slide_data: list[tuple[str, str]] = []

    if not placeholder and images_folder:
        folder_path = Path(images_folder)
        if not folder_path.is_absolute() and images_root is not None:
            folder_path = images_root / images_folder
        slide_data = load_folder_images(folder_path)
        if not slide_data:
            placeholder = True  # fallback

    if placeholder:
        icon = ad.get("placeholder_icon", "▶")
        text = ad.get("placeholder_text", "Pendiente")
        text_html = text.replace("\n", "<br>")
        slides_html = (
            f'<div class="ph-icon">{icon}</div>'
            f'<div class="ph-text">{text_html}</div>'
        )
        slides_wrapper_class = "ad-slides video-ph"
    else:
        slides_html = ""
        for i, (_, b64) in enumerate(slide_data):
            slides_html += (
                f'<img src="data:image/jpeg;base64,{b64}" class="slide-thumb" alt="S{i + 1}">'
            )
        slides_wrapper_class = "ad-slides"

    # Landing
    landing = ad.get("landing", {})
    l_type = landing.get("type", "")
    l_url = landing.get("url", "")
    l_detail = landing.get("detail", "")

    # Meta row (format + origin)
    fmt = ad.get("format", "")
    origin = ad.get("origin", "")

    video_class = " video" if ad.get("is_video") else ""

    return f'''
    <div class="ad-card {pclass}{video_class}">
      <div class="ad-badge {badge_class}">{ad.get("id", "")}</div>
      <div class="{slides_wrapper_class}">{slides_html}</div>
      <div class="ad-info">
        <div class="ad-name">{ad.get("name", "")}</div>
        <div class="ad-hook">"{ad.get("hook", "")}"</div>
        <div class="ad-meta">
          <span class="ad-fmt">{fmt}</span>
          <span class="ad-origin">{origin}</span>
        </div>
      </div>
      <div class="ad-right">
        <div class="prod-pill prod-{pclass}">{ad.get("product", "")}</div>
        <div class="{metric_class}">{ad.get("metric_label", "")}</div>
      </div>
      <div class="arrow">→</div>
      <div class="landing">
        <div class="ltype">{l_type}</div>
        <div class="lurl">{l_url}</div>
        <div class="lprice">{l_detail}</div>
      </div>
    </div>
    '''


def render_phase(phase: dict[str, Any], images_root: Path | None) -> str:
    dot_color = phase.get("color", "#2563eb")
    ads_html = "\n".join(render_ad_card(a, images_root) for a in phase.get("ads", []))
    return f'''
    <div class="phase">
      <span class="pdot" style="background:{dot_color}"></span>{phase.get("name", "")}
      <span class="pinfo">{phase.get("info", "")}</span>
    </div>
    <div class="ads-grid">
      {ads_html}
    </div>
    '''


def render_adset(adset: dict[str, Any], images_root: Path | None) -> str:
    style = adset.get("style", "")
    phases_html = "\n".join(render_phase(p, images_root) for p in adset.get("phases", []))
    kv_items = ""
    for kv in adset.get("details", []):
        k = kv.get("k", "")
        v = kv.get("v", "")
        kv_items += f'<div class="akv">{k}: <b>{v}</b></div>'
    return f'''
    <div class="adset-bar" {f'style="{style}"' if style else ''}>
      <div class="tag">AD SET</div>
      <div class="aname">{adset.get("name", "")}</div>
      {kv_items}
    </div>
    {phases_html}
    '''


def render_campaign(campaign: dict[str, Any], images_root: Path | None) -> str:
    style = campaign.get("style", "")
    tag_style = campaign.get("tag_style", "")
    kv_items = ""
    for kv in campaign.get("details", []):
        k = kv.get("k", "")
        v = kv.get("v", "")
        kv_items += f'<div class="ckv">{k}: <b>{v}</b></div>'
    adsets_html = "\n".join(render_adset(a, images_root) for a in campaign.get("ad_sets", []))
    return f'''
    <div class="campaign">
      <div class="campaign-bar" {f'style="{style}"' if style else ''}>
        <div class="tag" {f'style="{tag_style}"' if tag_style else ''}>CAMPAIGN</div>
        <div class="cname">{campaign.get("name", "")}</div>
        {kv_items}
      </div>
      {adsets_html}
    </div>
    '''


def render_legend(items: list[dict[str, Any]], meta_text: str) -> str:
    items_html = ""
    for it in items:
        kind = it.get("kind", "dot")
        if kind == "dot":
            items_html += (
                f'<div class="item"><div class="dot" style="background:{it["color"]}"></div>'
                f'{it["label"]}</div>'
            )
        elif kind == "text":
            items_html += f'<div class="item">{it["label"]}</div>'
        elif kind == "dash":
            items_html += '<div class="item">—</div>'
    return f'''
    <div class="legend">
      {items_html}
      <div class="meta">{meta_text}</div>
    </div>
    '''


def render_detail_page(page: dict[str, Any]) -> str:
    """Renderiza una pagina de detalle (page 2) — config tecnica, budget viz, timeline, etc."""
    # Header (distinto al principal — con 3 metrics)
    header = page.get("header", {})
    metrics_html = ""
    for m in header.get("metrics", []):
        metrics_html += (
            f'<div class="metric">'
            f'<div class="label">{m["label"]}</div>'
            f'<div class="value" style="font-size:{m.get("value_size", "10px")}">{m["value"]}</div>'
            f'</div>'
        )
    header_html = f'''
    <div class="header">
      <div>
        <h1>{header.get("title", "")}</h1>
        <div class="sub">{header.get("subtitle", "")}</div>
        <div class="tagline">{header.get("tagline", "")}</div>
      </div>
      <div class="metrics">{metrics_html}</div>
    </div>
    '''

    # Phase summary cards (top strip)
    phase_summary_html = ""
    if page.get("phase_summary"):
        cards = ""
        for pc in page["phase_summary"]:
            cards += f'''
            <div class="phase-card">
              <div class="pn">● {pc.get("pn", "")}</div>
              <div class="ptitle">{pc.get("title", "")}</div>
              <div class="pdesc">{pc.get("desc", "")}</div>
              <div class="pcount">{pc.get("count", "")} <span>{pc.get("count_label", "")}</span></div>
            </div>
            '''
        phase_summary_html = f'<div class="phase-summary">{cards}</div>'

    # Campaign block(s) for page 2
    campaign_blocks_html = ""
    for camp in page.get("campaigns", []):
        campaign_blocks_html += render_campaign(camp, None)

    # Quiz block (optional, paired with campaign)
    if page.get("quiz_block"):
        qb = page["quiz_block"]
        steps_html = ""
        for i, s in enumerate(qb.get("funnel", [])):
            if i > 0:
                steps_html += '<div class="farrow">→</div>'
            steps_html += f'<div class="fstep">{s}</div>'
        quiz_html = f'''
        <div class="quiz-block">
          <div class="quiz-card">
            <h4>{qb.get("flow_title", "Quiz Funnel — Flujo")}</h4>
            <div class="desc">{qb.get("flow_desc", "")}</div>
            <div class="funnel">{steps_html}</div>
          </div>
          <div class="quiz-card">
            <h4>{qb.get("landing_title", "Landing")}</h4>
            <div class="desc">{qb.get("landing_desc", "")}</div>
          </div>
        </div>
        '''
        # Inyectar dentro del ultimo campaign si hay
        if campaign_blocks_html:
            campaign_blocks_html = campaign_blocks_html.rstrip()
            # Cerrar .campaign y reabrir con quiz
            insert_point = campaign_blocks_html.rfind("</div>")
            campaign_blocks_html = (
                campaign_blocks_html[:insert_point]
                + quiz_html
                + campaign_blocks_html[insert_point:]
            )
        else:
            campaign_blocks_html = f'<div class="campaign">{quiz_html}</div>'

    # Detail cards grid (page2-grid) — optional
    detail_grid_html = ""
    if page.get("detail_grid"):
        left_card = page["detail_grid"].get("left", {})
        right_blocks = page["detail_grid"].get("right", [])

        def render_kv_grid(kvs):
            if not kvs:
                return ""
            items = ""
            for kv in kvs:
                items += f'<div class="k">{kv["k"]}</div><div class="v">{kv["v"]}</div>'
            return f'<div class="kv-grid">{items}</div>'

        def render_detail_card(card):
            sections_html = ""
            for sec in card.get("sections", []):
                sections_html += f'<h4>{sec["heading"]}</h4>{render_kv_grid(sec.get("kvs", []))}'
            head_style = card.get("head_style", "")
            dnum_style = card.get("dnum_style", "")
            return f'''
            <div class="detail-card">
              <div class="detail-head" {f'style="{head_style}"' if head_style else ''}>
                <div class="dnum" {f'style="{dnum_style}"' if dnum_style else ''}>{card.get("dnum", "")}</div>
                <div class="dtitle">{card.get("dtitle", "")}</div>
                <div class="ddesc">{card.get("ddesc", "")}</div>
              </div>
              <div class="detail-body">
                {sections_html}
              </div>
            </div>
            '''

        left_html = render_detail_card(left_card) if left_card else ""
        right_html = ""
        for block in right_blocks:
            btype = block.get("type", "card")
            if btype == "card":
                right_html += render_detail_card(block)
            elif btype == "budget_viz":
                segs_html = ""
                for seg in block.get("segments", []):
                    segs_html += (
                        f'<div class="seg" style="flex:{seg["flex"]};background:{seg["color"]}">'
                        f'{seg["label"]}</div>'
                    )
                legend_items = ""
                for li in block.get("legend", []):
                    legend_items += (
                        f'<div class="bi"><div class="bd" style="background:{li["color"]}"></div>'
                        f'{li["label"]}</div>'
                    )
                right_html += f'''
                <div class="budget-viz">
                  <div class="btitle">{block.get("title", "")}</div>
                  <div class="budget-bar">{segs_html}</div>
                  <div class="budget-legend">{legend_items}</div>
                </div>
                '''
            elif btype == "timeline":
                weeks_html = ""
                for w in block.get("weeks", []):
                    weeks_html += f'''
                    <div class="week">
                      <div class="wname">{w["name"]}</div>
                      <div class="wtask">{w["task"]}</div>
                    </div>
                    '''
                right_html += f'''
                <div class="timeline">
                  <div class="btitle" style="font-size:8.5px;font-weight:800;color:#475569;text-transform:uppercase;letter-spacing:0.6px;">{block.get("title", "")}</div>
                  <div class="tbar">{weeks_html}</div>
                </div>
                '''
        detail_grid_html = f'''
        <div class="page2-grid">
          {left_html}
          <div>{right_html}</div>
        </div>
        '''

    # Legend
    legend_html = render_legend(
        page.get("legend_items", []),
        page.get("legend_meta", ""),
    )

    return f'''
    <div class="page">
      {header_html}
      {phase_summary_html}
      {campaign_blocks_html}
      {detail_grid_html}
      {legend_html}
      <div class="page-foot">{page.get("page_foot", "")}</div>
      <div class="page-num">{page.get("page_num", "")}</div>
    </div>
    '''


def render_architecture_page(page: dict[str, Any], data: dict[str, Any], images_root: Path | None) -> str:
    """Renderiza la pagina 1 principal con la arquitectura panoramica."""
    header_html = render_header(data)
    campaigns_html = "\n".join(render_campaign(c, images_root) for c in page.get("campaigns", []))
    legend_html = render_legend(
        page.get("legend_items", []),
        page.get("legend_meta", ""),
    )
    return f'''
    <div class="page">
      {header_html}
      {campaigns_html}
      {legend_html}
      <div class="page-foot">{page.get("page_foot", "")}</div>
      <div class="page-num">{page.get("page_num", "")}</div>
    </div>
    '''


# ---------- CSS (fijo, base HC v1) ----------

CSS = '''
@page { size: 420mm 297mm; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  background: #f8fafc; color: #0f172a; font-size: 10px; line-height: 1.35;
  -webkit-font-smoothing: antialiased;
}
.page {
  width: 420mm; height: 297mm; padding: 10mm 12mm;
  page-break-after: always; background: white; position: relative; overflow: hidden;
}
.page:last-child { page-break-after: auto; }

.header {
  background: linear-gradient(135deg, #0a1628 0%, #1e3a5f 50%, #2563eb 100%);
  color: white; padding: 12px 18px; border-radius: 8px; margin-bottom: 10px;
  display: grid; grid-template-columns: 1fr auto; gap: 20px; align-items: center;
}
.header h1 { font-size: 20px; font-weight: 900; letter-spacing: -0.5px; }
.header .sub { font-size: 10px; opacity: 0.85; margin-top: 2px; font-weight: 500; }
.header .tagline { font-size: 9px; color: #7dd3fc; margin-top: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; }
.header .metrics { display: flex; gap: 14px; }
.header .metric {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(125,211,252,0.25);
  padding: 6px 12px; border-radius: 5px; text-align: center; min-width: 74px;
}
.header .metric .label { font-size: 7.5px; text-transform: uppercase; letter-spacing: 0.8px; opacity: 0.7; }
.header .metric .value { font-weight: 900; color: #7dd3fc; margin-top: 1px; }

.campaign {
  background: white; border: 1.5px solid #e2e8f0; border-radius: 8px;
  margin-bottom: 8px; overflow: hidden;
}
.campaign-bar {
  background: linear-gradient(90deg, #0a1628 0%, #1e3a5f 100%);
  color: white; padding: 7px 14px;
  display: grid; grid-template-columns: auto 1fr auto auto auto; gap: 16px;
  align-items: center; font-size: 9.5px;
}
.campaign-bar .tag {
  background: #7dd3fc; color: #0a1628; padding: 2px 6px; border-radius: 3px;
  font-weight: 800; font-size: 7.5px; letter-spacing: 0.8px;
}
.campaign-bar .cname { font-size: 12px; font-weight: 800; letter-spacing: -0.3px; }
.campaign-bar .ckv { font-size: 8.5px; opacity: 0.75; }
.campaign-bar .ckv b { color: #7dd3fc; font-weight: 700; }

.adset-bar {
  background: #1e3a5f; color: white; padding: 6px 14px 6px 28px;
  display: grid; grid-template-columns: auto 1fr auto auto auto auto;
  gap: 14px; align-items: center; font-size: 8.5px; position: relative;
}
.adset-bar::before { content: "└"; position: absolute; left: 14px; top: 2px; color: #7dd3fc; font-size: 12px; }
.adset-bar .tag {
  background: rgba(125,211,252,0.2); color: #7dd3fc; padding: 2px 6px;
  border-radius: 3px; font-weight: 700; font-size: 7px; letter-spacing: 0.6px;
}
.adset-bar .aname { font-weight: 700; font-size: 9.5px; }
.adset-bar .akv { opacity: 0.75; }
.adset-bar .akv b { color: #7dd3fc; }

.phase {
  background: #f1f5f9; padding: 5px 14px 5px 40px;
  font-size: 8.5px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #475569; border-top: 1px solid #e2e8f0; position: relative;
}
.phase .pdot {
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: #2563eb; margin-right: 6px; vertical-align: middle;
}
.phase .pinfo {
  float: right; font-weight: 500; text-transform: none; letter-spacing: 0;
  color: #64748b; font-size: 8.5px;
}

.ads-grid { padding: 7px 14px 9px 40px; display: grid; gap: 5px; }

.ad-card {
  display: grid;
  grid-template-columns: 24px auto 1.3fr auto 12px 1.1fr;
  gap: 8px; align-items: center;
  background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #94a3b8;
  padding: 6px 10px; border-radius: 6px;
}

.ad-badge {
  background: #0a1628; color: white; font-weight: 800; font-size: 9px;
  padding: 3px 0; text-align: center; border-radius: 4px;
}
.ad-badge.v { background: #7c3aed; }

.ad-slides {
  display: flex; gap: 3px; align-items: flex-end;
  height: 68px;
}
.slide-thumb {
  height: 68px; width: auto; object-fit: contain;
  border: 1.5px solid #cbd5e1; border-radius: 3px;
  background: #e2e8f0;
  max-width: 80px;
}
.ad-slides.video-ph {
  background: #f1f5f9; border: 1.5px dashed #c4b5fd;
  width: 140px; border-radius: 4px;
  justify-content: center; gap: 8px; padding: 0 10px;
}
.ph-icon { font-size: 18px; color: #7c3aed; }
.ph-text { font-size: 8px; color: #6d28d9; font-weight: 700; text-align: left; }

.ad-info { min-width: 0; }
.ad-name { font-weight: 800; font-size: 10px; color: #0f172a; }
.ad-hook {
  font-size: 9px; color: #64748b; font-style: italic; margin-top: 2px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ad-meta { font-size: 8px; color: #475569; margin-top: 2px; }
.ad-meta .ad-fmt { font-weight: 700; color: #0f172a; }
.ad-meta .ad-origin { color: #64748b; margin-left: 10px; }
.ad-meta .ad-origin b { color: #2563eb; }

.ad-right { display: flex; flex-direction: column; gap: 3px; align-items: flex-end; }

.wci {
  background: #10b981; color: white; font-size: 8px; font-weight: 800;
  padding: 3px 7px; border-radius: 10px; white-space: nowrap;
}
.wci.mid { background: #3b82f6; }
.wci.low { background: #94a3b8; }
.wci.tbd { background: #e2e8f0; color: #64748b; }

.prod-pill {
  font-size: 8px; font-weight: 800; padding: 3px 7px; border-radius: 10px;
  color: white; text-transform: uppercase; letter-spacing: 0.4px; white-space: nowrap;
}
.prod-artridog { background: #f59e0b; }
.prod-dogrelax { background: #8b5cf6; }
.prod-omegadog { background: #06b6d4; }
.prod-gastrodog { background: #10b981; }
.prod-marca { background: #1e3a5f; }
.prod-brand { background: #1e3a5f; }
.prod-default { background: #64748b; }
/* GREENRAY products */
.prod-gaxaliv { background: #16a34a; }
.prod-bellsan { background: #f97316; }
.prod-colageno { background: #ec4899; }
.prod-gxamin { background: #2563eb; }
.prod-hormo { background: #dc2626; }
.prod-gastrocoll { background: #059669; }
.prod-hormocoll { background: #991b1b; }
.prod-wa { background: #25d366; }
.prod-quiz { background: #7c3aed; }
.prod-guia { background: #f59e0b; }
.prod-funnel { background: #0ea5e9; }
.prod-metafit { background: #FF9F43; }
.prod-fitmax { background: #ec4899; }
.prod-kittrio { background: #5B8DEF; }
.prod-lupita { background: #C5A55A; }

.arrow { color: #94a3b8; font-size: 14px; text-align: center; font-weight: 300; }

.landing {
  background: white; border: 1px solid #cbd5e1; padding: 4px 8px;
  border-radius: 4px; font-size: 8.5px;
}
.landing .ltype {
  font-weight: 800; color: #2563eb; font-size: 7.5px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.landing .lurl { color: #0f172a; font-size: 9px; margin-top: 1px; font-weight: 700; }
.landing .lprice { font-size: 8px; color: #10b981; font-weight: 700; margin-top: 1px; }

.ad-card.artridog { border-left-color: #f59e0b; }
.ad-card.dogrelax { border-left-color: #8b5cf6; }
.ad-card.omegadog { border-left-color: #06b6d4; }
.ad-card.gastrodog { border-left-color: #10b981; }
.ad-card.marca { border-left-color: #1e3a5f; }
.ad-card.brand { border-left-color: #1e3a5f; }
.ad-card.default { border-left-color: #94a3b8; }
.ad-card.gaxaliv { border-left-color: #16a34a; }
.ad-card.bellsan { border-left-color: #f97316; }
.ad-card.colageno { border-left-color: #ec4899; }
.ad-card.gxamin { border-left-color: #2563eb; }
.ad-card.hormo { border-left-color: #dc2626; }
.ad-card.gastrocoll { border-left-color: #059669; }
.ad-card.hormocoll { border-left-color: #991b1b; }
.ad-card.wa { border-left-color: #25d366; background: #f0fdf4; }
.ad-card.quiz { border-left-color: #7c3aed; background: #faf5ff; }
.ad-card.guia { border-left-color: #f59e0b; background: #fffbeb; }
.ad-card.funnel { border-left-color: #0ea5e9; background: #f0f9ff; }
.ad-card.metafit { border-left-color: #FF9F43; }
.ad-card.fitmax { border-left-color: #ec4899; }
.ad-card.kittrio { border-left-color: #5B8DEF; }
.ad-card.lupita { border-left-color: #C5A55A; background: #fdf8ef; }

.ad-card.video { background: #faf5ff; }

.quiz-block {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  padding: 10px 14px 12px 40px;
}
.quiz-card {
  background: #faf5ff; border: 1.5px dashed #a78bfa;
  border-radius: 8px; padding: 10px 12px;
}
.quiz-card h4 {
  font-size: 10px; color: #6d28d9; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.8px;
}
.quiz-card .desc { font-size: 8.5px; color: #475569; margin-top: 5px; line-height: 1.5; }
.quiz-card .funnel {
  display: flex; gap: 4px; margin-top: 8px; align-items: center; font-size: 8px;
}
.quiz-card .fstep {
  background: white; border: 1px solid #c4b5fd; padding: 4px 7px;
  border-radius: 4px; font-weight: 700; color: #6d28d9; flex: 1; text-align: center;
}
.quiz-card .farrow { color: #a78bfa; font-weight: 700; }

.legend {
  display: grid; grid-template-columns: repeat(6, auto) 1fr;
  gap: 12px; background: #0f172a; color: white; padding: 8px 16px;
  border-radius: 6px; font-size: 8px; margin-top: 6px;
}
.legend .item { display: flex; align-items: center; gap: 5px; }
.legend .dot { width: 9px; height: 9px; border-radius: 50%; }
.legend .meta { text-align: right; opacity: 0.7; }

.page-num {
  position: absolute; bottom: 5mm; right: 12mm;
  font-size: 8px; color: #94a3b8; font-weight: 600;
}
.page-foot {
  position: absolute; bottom: 5mm; left: 12mm;
  font-size: 8px; color: #94a3b8; font-weight: 600;
}

.page2-grid {
  display: grid; grid-template-columns: 1.1fr 1fr;
  gap: 12px; height: calc(100% - 70px);
}
.detail-card {
  background: white; border: 1.5px solid #e2e8f0; border-radius: 8px; overflow: hidden;
}
.detail-head {
  background: linear-gradient(90deg, #0a1628 0%, #1e3a5f 100%);
  color: white; padding: 10px 14px;
}
.detail-head .dnum { font-size: 8.5px; color: #7dd3fc; font-weight: 800; letter-spacing: 1.2px; }
.detail-head .dtitle { font-size: 14px; font-weight: 800; margin-top: 2px; }
.detail-head .ddesc { font-size: 8.5px; opacity: 0.8; margin-top: 3px; }
.detail-body { padding: 10px 14px; }
.detail-body h4 {
  font-size: 9.5px; font-weight: 800; color: #1e3a5f;
  text-transform: uppercase; letter-spacing: 0.8px;
  margin-bottom: 5px; padding-bottom: 3px; border-bottom: 1px solid #e2e8f0;
}
.detail-body h4:not(:first-child) { margin-top: 10px; }
.kv-grid { display: grid; grid-template-columns: 100px 1fr; gap: 3px 10px; font-size: 8.5px; }
.kv-grid .k { color: #64748b; font-weight: 600; }
.kv-grid .v { color: #0f172a; font-weight: 600; }
.kv-grid .v b { color: #2563eb; }

.budget-viz { margin-top: 10px; padding: 10px 12px; background: #f8fafc; border-radius: 6px; }
.budget-viz .btitle {
  font-size: 8.5px; font-weight: 800; color: #475569;
  text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px;
}
.budget-bar { display: flex; height: 24px; border-radius: 4px; overflow: hidden; background: #e2e8f0; }
.budget-bar .seg { display: flex; align-items: center; justify-content: center; color: white; font-size: 8.5px; font-weight: 700; }
.budget-legend { display: flex; gap: 14px; margin-top: 6px; font-size: 8px; color: #475569; }
.budget-legend .bi { display: flex; align-items: center; gap: 4px; }
.budget-legend .bd { width: 9px; height: 9px; border-radius: 2px; }

.timeline { margin-top: 10px; }
.timeline .tbar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; margin-top: 5px; }
.timeline .week {
  background: #f1f5f9; border-top: 3px solid #2563eb;
  padding: 6px 9px; border-radius: 4px; font-size: 8px;
}
.timeline .week .wname { font-weight: 800; color: #1e3a5f; font-size: 8.5px; margin-bottom: 2px; }
.timeline .week .wtask { color: #475569; line-height: 1.4; }
.timeline .week:nth-child(2) { border-top-color: #7c3aed; }
.timeline .week:nth-child(3) { border-top-color: #10b981; }
.timeline .week:nth-child(4) { border-top-color: #f59e0b; }

.phase-summary {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 8px; margin-bottom: 8px;
}
.phase-card {
  background: white; border: 1.5px solid #e2e8f0; border-left: 4px solid #2563eb;
  border-radius: 6px; padding: 8px 10px;
}
.phase-card .pn {
  font-size: 8px; color: #2563eb; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.8px;
}
.phase-card .ptitle { font-size: 10px; font-weight: 800; margin-top: 2px; }
.phase-card .pdesc { font-size: 8px; color: #64748b; margin-top: 3px; line-height: 1.45; }
.phase-card .pcount { font-size: 15px; font-weight: 900; color: #0f172a; margin-top: 4px; }
.phase-card .pcount span { font-size: 8.5px; color: #64748b; font-weight: 600; }
.phase-card:nth-child(2) { border-left-color: #7c3aed; }
.phase-card:nth-child(2) .pn { color: #7c3aed; }
.phase-card:nth-child(3) { border-left-color: #94a3b8; }
.phase-card:nth-child(3) .pn { color: #94a3b8; }
'''


# ---------- Build & render ----------

def build_html(data: dict[str, Any], input_path: Path) -> str:
    """Construye el HTML completo a partir del JSON de entrada."""
    images_root_str = data.get("meta", {}).get("images_root")
    if images_root_str:
        images_root = Path(images_root_str)
        if not images_root.is_absolute():
            images_root = (input_path.parent / images_root).resolve()
    else:
        images_root = input_path.parent

    pages_html = ""
    for i, page in enumerate(data.get("pages", [])):
        ptype = page.get("type", "architecture")
        if ptype == "architecture":
            pages_html += render_architecture_page(page, data, images_root)
        elif ptype == "detail":
            pages_html += render_detail_page(page)
        else:
            raise ValueError(f"Tipo de pagina desconocido: {ptype}")

    title = data.get("meta", {}).get("title", "Arquitectura de Campana")
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
{pages_html}
</body>
</html>'''


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    """Usa Playwright para renderizar el HTML a PDF A3 landscape."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright no instalado. pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(pdf_path),
            width="420mm",
            height="297mm",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="SPEKGEN Campaign Architecture PDF Builder")
    parser.add_argument("input", help="Path al JSON de entrada")
    parser.add_argument("--output", "-o", help="Path del PDF de salida (default: segun meta.output_pdf del JSON)")
    parser.add_argument("--html-only", action="store_true", help="Solo generar HTML, no PDF")
    parser.add_argument("--keep-html", action="store_true", help="No borrar el HTML intermedio")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"ERROR: input no existe: {input_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(input_path.read_text(encoding="utf-8"))

    # Output PDF path
    if args.output:
        pdf_path = Path(args.output).resolve()
    else:
        meta_out = data.get("meta", {}).get("output_pdf")
        if meta_out:
            pdf_path = Path(meta_out)
            if not pdf_path.is_absolute():
                pdf_path = (input_path.parent / meta_out).resolve()
        else:
            pdf_path = input_path.with_suffix(".pdf")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # Build HTML
    print(f"Building HTML from: {input_path.name}")
    html = build_html(data, input_path)
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    print(f"HTML written: {html_path} ({html_path.stat().st_size / 1024:.1f} KB)")

    if args.html_only:
        print("HTML only mode — skipping PDF")
        return

    # Render PDF
    print("Rendering PDF with Playwright...")
    render_pdf(html_path, pdf_path)
    print(f"PDF written: {pdf_path} ({pdf_path.stat().st_size / 1024:.1f} KB)")

    if not args.keep_html:
        html_path.unlink()
        print("HTML intermedio eliminado (--keep-html para conservarlo)")

    print(f"\nOK — open '{pdf_path}'")


if __name__ == "__main__":
    main()
