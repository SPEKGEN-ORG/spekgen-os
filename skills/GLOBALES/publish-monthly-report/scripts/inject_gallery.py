#!/usr/bin/env python3
"""Inject a content gallery section into the GR monthly report HTML."""

import base64
import io
import os
from pathlib import Path
from PIL import Image

BASE = Path("/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL")
REPORT = Path("/Users/gibranalonzo/.claude/skills/publish-monthly-report/reports/gr-reporte-abril.html")

# Cover image per organic post (first slide for carousels)
ORGANIC = [
    ("GR-001", "Gaxaliv — Carrusel Educativo", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 1/GR-001/00. IMAGENES FINALES/GR-001_S1_HOOK.png"),
    ("GR-003", "BELLSAN — Static", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 1/GR-003/00. IMAGENES FINALES/GR-003_BELLSAN.png"),
    ("GR-004", "HORMO FX — Carrusel Síntomas", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 1/GR-004/00. IMAGENES FINALES/GR_HORMOFX_004_S1_HOOK_1x1.png"),
    ("GR-005", "Enzimas — Carrusel Educativo", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 1/GR-005/00. IMAGENES FINALES/GR_ENZYMAS_005_S1_HOOK_1x1.png"),
    ("GR-006", "INTRA B Sleep — Static", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 1/GR-006/00. IMAGENES FINALES/GR_INTRAB_SLEEP_006_S1_STATIC_1x1.png"),
    ("GR-007", "Brand — Static", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 1/GR-007/00. IMAGENES FINALES/GR_BRAND_007_S1_STATIC_1x1.png"),
    ("GR-008", "DETOX FX — Carrusel Educativo", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 2/GR-008/00. IMAGENES FINALES/GR_DETOXFX_008_S1_HOOK_1x1.png"),
    ("GR-031", "Hormonal — Testimonial", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 2/GR-031/00. IMAGENES FINALES/GR-031_HORMONAL_TESTIMONIAL_4x5.png"),
    ("GR-032", "Hormonal — Stack", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 2/GR-032/00. IMAGENES FINALES/GR-032_HORMONAL_STACK_4x5.png"),
    ("GR-033", "Gastrointestinal — Testimonial", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 2/GR-033/00. IMAGENES FINALES/GR-033_GASTRO_TESTIMONIAL_4x5.png"),
    ("GR-034", "Gastrointestinal — Stack", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 2/GR-034/00. IMAGENES FINALES/GR-034_GASTRO_STACK_4x5.png"),
    ("GR-035", "Proteicos — Testimonial", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 2/GR-035/00. IMAGENES FINALES/GR-035_PROTEICOS_TESTIMONIAL_4x5.png"),
    ("GR-036", "Proteicos — Stack", BASE / "GR - GREENRAY/GR - 06. SOCIAL MEDIA/ABRIL/SEMANA 2/GR-036/00. IMAGENES FINALES/GR-036_PROTEICOS_STACK_4x5.png"),
]

GR_META = BASE / "GR - GREENRAY/GR - 05. META ADS"
FACTORY = BASE / "SPK - SPEKGEN AGENCY/SPK - 15. FACTORY/ads/BATCH_CROSS_2026-04-21-v4/RESOURCES"

# Batch 1 — ads subidos antes del 22 abr (en carpeta GR META ADS) — 1 representativo por grupo
ADS_BATCH1 = [
    ("GR-AD-001", "Gaxaliv — Protocolo (Carrusel)", GR_META / "GR-AD-001_PROTOCOLO_GAXALIV/VARIACIONES/SLIDE1_SINTOMAS.png"),
    ("GR-AD-002", "BELLSAN", GR_META / "GR-AD-002_BELLSAN/VARIACIONES/V1.png"),
    ("GR-AD-003", "Colágeno FITNESS ★ Ganador ROAS 3.1x", GR_META / "GR-AD-003_COLAGENO_FITNESS/VARIACIONES/V1.png"),
    ("GR-AD-004", "G-XAMIN", GR_META / "GR-AD-004_GXAMIN/VARIACIONES/V1.png"),
    ("GR-AD-005", "HORMO MEN 40+", GR_META / "GR-AD-005_HORMO_MEN_40/VARIACIONES/V1.png"),
    ("GR-AD-006", "Gastrointestinal Collection", GR_META / "GR-AD-006_GASTRO_COLLECTION/VARIACIONES/V1.png"),
    ("GR-AD-008", "HORMO Collection", GR_META / "GR-AD-008_HORMO_COLLECTION/VARIACIONES/V1.png"),
]

# Batch 2 — 22 abr (BATCH_CROSS_2026-04-21-v4)
ADS_BATCH2 = [
    ("GR-AD-019A", "HORMO FX — Variante A", FACTORY / "GR-AD-019/FINAL/GR-AD-019_4x5_A.png"),
    ("GR-AD-019B", "HORMO FX — Variante B", FACTORY / "GR-AD-019/FINAL/GR-AD-019_4x5_B.png"),
    ("GR-AD-019C", "HORMO FX — Oferta", FACTORY / "GR-AD-019C/FINAL/GR-AD-019C_4x5.png"),
    ("GR-AD-020A", "Gastrointestinal Stack", FACTORY / "GR-AD-020/FINAL/GR-AD-020_4x5.png"),
    ("GR-AD-020C", "Gastrointestinal — Oferta", FACTORY / "GR-AD-020C/FINAL/GR-AD-020C_4x5.png"),
    ("GR-AD-021A", "Proteína Complex", FACTORY / "GR-AD-021/FINAL/GR-AD-021_4x5.png"),
    ("GR-AD-021CA", "Proteína — Variante A", FACTORY / "GR-AD-021C/FINAL/GR-AD-021C_4x5_A.png"),
    ("GR-AD-021CB", "Proteína — Variante B", FACTORY / "GR-AD-021C/FINAL/GR-AD-021C_4x5_B.png"),
]

ADS = ADS_BATCH1 + ADS_BATCH2

def to_b64(path: Path, max_w=220, quality=55) -> str:
    """Resize and encode as JPEG base64."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w > max_w:
        img = img.resize((max_w, int(h * max_w / w)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

def build_card(code, label, path, badge_color="#4ade80"):
    b64 = to_b64(path)
    size_kb = round(len(b64) * 3 / 4 / 1024)
    print(f"  {code}: {size_kb} KB")
    return f"""<div class="spk-gal-card">
  <img src="data:image/jpeg;base64,{b64}" alt="{label}" loading="lazy">
  <div class="spk-gal-label">
    <span class="spk-gal-code" style="background:{badge_color}22;color:{badge_color};border:1px solid {badge_color}44">{code}</span>
    {label}
  </div>
</div>"""

GALLERY_CSS = """
<style>
.spk-gallery-section{margin:2.5rem 0;padding:2rem;background:#1a1a2e;border-radius:16px}
.spk-gallery-section h2{color:#e2e8f0;font-size:1.3rem;font-weight:700;margin:0 0 .5rem}
.spk-gallery-section .spk-gallery-sub{color:#94a3b8;font-size:.85rem;margin:0 0 1.5rem}
.spk-gallery-section h3{color:#cbd5e1;font-size:1rem;font-weight:600;margin:1.5rem 0 .75rem;padding-bottom:.4rem;border-bottom:1px solid #2d3748}
.spk-gal-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:.75rem}
.spk-gal-card{background:#0f172a;border-radius:10px;overflow:hidden;border:1px solid #2d3748;transition:transform .2s,border-color .2s}
.spk-gal-card:hover{transform:translateY(-3px);border-color:#4ade8066}
.spk-gal-card img{width:100%;display:block;aspect-ratio:1;object-fit:cover}
.spk-gal-label{padding:.5rem .6rem;font-size:.72rem;color:#94a3b8;display:flex;flex-direction:column;gap:.25rem}
.spk-gal-code{display:inline-block;padding:2px 6px;border-radius:4px;font-size:.65rem;font-weight:600;margin-bottom:2px;width:fit-content}
</style>
"""

def build_gallery():
    print("Procesando organic posts...")
    organic_cards = []
    for code, label, path in ORGANIC:
        if path.exists():
            organic_cards.append(build_card(code, label, path, "#4ade80"))
        else:
            print(f"  MISSING: {path}")

    print("Procesando ads batch 1...")
    b1_cards = []
    for code, label, path in ADS_BATCH1:
        if path.exists():
            b1_cards.append(build_card(code, label, path, "#f59e0b"))
        else:
            print(f"  MISSING: {path}")

    print("Procesando ads batch 2...")
    b2_cards = []
    for code, label, path in ADS_BATCH2:
        if path.exists():
            b2_cards.append(build_card(code, label, path, "#60a5fa"))
        else:
            print(f"  MISSING: {path}")

    total_organic = len(organic_cards)
    total_ads = len(b1_cards) + len(b2_cards)

    organic_html = "\n".join(organic_cards)
    b1_html = "\n".join(b1_cards)
    b2_html = "\n".join(b2_cards)

    return f"""{GALLERY_CSS}
<div id="spk-gallery" class="spk-gallery-section">
  <h2>Galería de Contenido — Abril 2026</h2>
  <p class="spk-gallery-sub">{total_organic} posts orgánicos · {total_ads} piezas de ads · {total_organic + total_ads} piezas totales</p>

  <h3>Contenido Orgánico ({total_organic} piezas publicadas)</h3>
  <div class="spk-gal-grid">
    {organic_html}
  </div>

  <h3 style="margin-top:2rem">Ads Meta — Batch 1 ({len(b1_cards)} piezas)</h3>
  <div class="spk-gal-grid">
    {b1_html}
  </div>

  <h3 style="margin-top:2rem">Ads Meta — Batch 2 · 22 abr ({len(b2_cards)} piezas · CTR 9–16%)</h3>
  <div class="spk-gal-grid">
    {b2_html}
  </div>
</div>
"""

if __name__ == "__main__":
    print("Generando galería...")
    gallery_html = build_gallery()

    html = REPORT.read_text(encoding="utf-8")

    # Inject before </body>
    if "<!-- SPK_GALLERY -->" in html:
        # Replace existing placeholder
        import re
        html = re.sub(r'<!-- SPK_GALLERY -->.*?<!-- /SPK_GALLERY -->', f'<!-- SPK_GALLERY -->{gallery_html}<!-- /SPK_GALLERY -->', html, flags=re.DOTALL)
    else:
        html = html.replace("</body>", f"<!-- SPK_GALLERY -->{gallery_html}<!-- /SPK_GALLERY -->\n</body>")

    REPORT.write_text(html, encoding="utf-8")
    size_kb = round(len(html.encode()) / 1024)
    print(f"\nReporte actualizado: {size_kb} KB total")
    print(f"Path: {REPORT}")
    os.system(f'open "{REPORT}"')
