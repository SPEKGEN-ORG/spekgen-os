#!/usr/bin/env python3
"""
build_recap_pdf.py v2 — Dual PDF output: WHITEBOARD (1-page A3) + DECK (multi-page A4).

Para batches type=content. Para ads matriz cross-client, usar build_recap_pdf_ads_matrix.py.

Uso:
    python3 build_recap_pdf.py /path/to/batch_dir --format both
    python3 build_recap_pdf.py /path/to/batch_dir --format whiteboard
    python3 build_recap_pdf.py /path/to/batch_dir --format deck

Output:
    {batch_dir}/_DELIVERABLES/{POST_ID}_WHITEBOARD.pdf
    {batch_dir}/_DELIVERABLES/{POST_ID}_DECK.pdf

Dependencias: Pillow
"""
import argparse, json, sys, textwrap
from pathlib import Path
from PIL import Image as PILImage, ImageDraw, ImageFont

PALETTES = {
    "HC": {"primary": (26, 155, 140), "accent": (232, 133, 46), "cream": (255, 252, 239),
           "dark": (26, 30, 46), "light": (245, 245, 245), "gray": (200, 200, 200), "white": (255, 255, 255)},
    "LF": {"primary": (0, 0, 0), "accent": (255, 100, 0), "cream": (245, 245, 240),
           "dark": (20, 20, 20), "light": (245, 245, 245), "gray": (180, 180, 180), "white": (255, 255, 255)},
    "GR": {"primary": (44, 95, 78), "accent": (200, 156, 84), "cream": (250, 245, 235),
           "dark": (30, 30, 30), "light": (245, 245, 245), "gray": (200, 200, 200), "white": (255, 255, 255)},
    "MG": {"primary": (50, 100, 60), "accent": (180, 130, 50), "cream": (250, 248, 240),
           "dark": (30, 30, 30), "light": (245, 245, 245), "gray": (200, 200, 200), "white": (255, 255, 255)},
}
DEFAULT_PALETTE = PALETTES["HC"]
DPI = 220   # bumped from 150 for sharper text rendering

def load_font(size, bold=False):
    bold_paths = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf"]
    paths = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"]
    for p in (bold_paths if bold else paths):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def mm(v, dpi=DPI):
    return int(v / 25.4 * dpi)

def get_palette(client):
    return PALETTES.get((client or "HC").upper(), DEFAULT_PALETTE)

MONTHS_ES = {
    "01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
    "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
    "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
}

def fix_spanish(s):
    """Restaura Ñ y tildes que pudieron perderse al guardar en JSON."""
    if not s:
        return s
    return (s.replace("SENAL", "SEÑAL").replace("Senal", "Señal").replace("senal", "señal"))

def format_date_pretty(date_str, time_str=None):
    """2026-04-29 → 29 abril 2026; +time → '29 abril 2026 · 11:00 AM'"""
    if not date_str:
        return None
    try:
        y, m, d = date_str.split("-")
        out = f"{int(d)} {MONTHS_ES.get(m, m)} {y}"
        if time_str:
            # 11:00 → 11:00 AM
            try:
                h, mn = time_str.split(":")
                hi = int(h)
                ampm = "AM" if hi < 12 else "PM"
                hi = hi if hi <= 12 else hi - 12
                hi = 12 if hi == 0 else hi
                out += f" · {hi}:{mn} {ampm}"
            except Exception:
                out += f" · {time_str}"
        return out
    except Exception:
        return date_str

def format_pretty(s):
    """carousel-7slides → 'Carrusel orgánico'; etc."""
    if not s:
        return None
    s_lower = s.lower()
    if "carousel" in s_lower or "carrusel" in s_lower:
        return "Carrusel orgánico"
    if "single" in s_lower or "post" in s_lower:
        return "Single post"
    if "reel" in s_lower:
        return "Reel"
    return s.replace("-", " ").replace("_", " ").title()

def make_label(slide, max_chars_per_line=22, max_lines=2):
    """Genera label smart-wrapped a partir del slide.

    Prioridad:
    1. slide.text (más legible y curado)
    2. slide.role (fallback técnico)

    Wrap a word-boundary, max N lines.
    """
    raw = slide.get("text") or slide.get("role") or f"S{slide['num']}"
    raw = fix_spanish(raw.replace("_", " "))

    # Word-wrap respetando boundaries
    words = raw.split()
    lines = []
    current = ""
    for w in words:
        candidate = (current + " " + w).strip() if current else w
        if len(candidate) <= max_chars_per_line:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = w
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)

    # Si la última línea quedó truncada, mostrar elipsis
    used_chars = sum(len(l) for l in lines) + len(lines) - 1  # spaces between
    if used_chars < len(raw) and lines:
        last = lines[-1]
        if len(last) > max_chars_per_line - 1:
            last = last[:max_chars_per_line - 1].rstrip()
        lines[-1] = last + "…"

    return lines  # retorna lista de líneas, no string

def make_meta_line(data):
    """Línea pretty: 'Serie: X · Producto · Formato · Fecha · REVISIÓN INTERNA'."""
    parts = []
    if data.get("series"):
        parts.append(f"Serie: {fix_spanish(data['series'].replace('_', ' '))}")
    if data.get("product"):
        parts.append(data["product"])
    fmt = format_pretty(data.get("format"))
    if fmt:
        parts.append(fmt)
    dt = format_date_pretty(data.get("publish_date"), data.get("publish_time"))
    if dt:
        parts.append(dt)
    parts.append("REVISIÓN INTERNA")
    return "  ·  ".join(parts)

def get_winning_image_paths(batch_dir, data):
    post_id = data["post_id"]
    final = batch_dir / "FINAL"
    winners = data.get("winning_variants") or {}
    out = []
    for slide in data["slides"]:
        n = slide["num"]
        v = winners.get(str(n)) or "v1"
        p = final / f"{post_id}_S{n}_{v}.jpg"
        if not p.exists():
            cands = sorted(final.glob(f"{post_id}_S{n}_v*.jpg"))
            if cands:
                p = cands[0]
            else:
                continue
        out.append(p)
    return out

# ── WHITEBOARD A3 landscape ──────────────────────────────────────────────────
def render_whiteboard_page(batch_dir, data):
    """Rinde 1 página A3 landscape (header + storyboard + caption + footer).
    Retorna PIL.Image para que el caller decida si guarda single-page o multi-page PDF."""
    PW = mm(420); PH = mm(297)
    pal = get_palette(data.get("client"))
    canvas = PILImage.new("RGB", (PW, PH), pal["white"])
    d = ImageDraw.Draw(canvas)

    MARGIN = mm(12)
    HDR_H = mm(18)

    d.rectangle([0, 0, PW, HDR_H], fill=pal["primary"])
    f_title = load_font(36, bold=True)
    f_meta = load_font(20)
    title = fix_spanish(data.get("title") or data["post_id"])
    d.text((MARGIN, mm(3)), f"{data['post_id']} — {title}", font=f_title, fill=pal["white"])
    d.text((MARGIN, mm(11)), make_meta_line(data), font=f_meta, fill=pal["cream"])
    d.rectangle([0, HDR_H, PW, HDR_H + mm(2)], fill=pal["accent"])

    images = get_winning_image_paths(batch_dir, data)
    N = max(len(images), 1)
    GAP = mm(5)
    NUM_TAB_H = mm(8)             # número arriba (NO encima de la imagen)
    LABEL_LINE_H = mm(5)
    LABEL_LINES = 2
    LABEL_H = LABEL_LINES * LABEL_LINE_H + mm(2)
    AVAIL_W = PW - 2 * MARGIN
    SLIDE_W = (AVAIL_W - (N - 1) * GAP) // N
    SLIDE_H = int(SLIDE_W * 1.25)
    CAP_H = mm(62)
    BLOCK_H = NUM_TAB_H + SLIDE_H + LABEL_H + mm(8) + CAP_H
    AVAIL_VERT = PH - (HDR_H + mm(2)) - MARGIN
    NUM_TAB_Y = HDR_H + mm(2) + (AVAIL_VERT - BLOCK_H) // 2
    SLIDE_Y = NUM_TAB_Y + NUM_TAB_H

    total_w = N * SLIDE_W + (N - 1) * GAP
    x_start = (PW - total_w) // 2

    f_num = load_font(28, bold=True)
    f_label = load_font(20)

    for i, img_path in enumerate(images):
        slide = data["slides"][i]
        x = x_start + i * (SLIDE_W + GAP)
        y = SLIDE_Y

        # ── Número ARRIBA del slide (no encima de la imagen) ──
        num_text = f"{i+1:02d}"
        num_w = mm(11)
        num_h = NUM_TAB_H - mm(1)
        num_y = NUM_TAB_Y
        d.rounded_rectangle([x, num_y, x + num_w, num_y + num_h],
                            radius=mm(1.5), fill=pal["primary"])
        d.text((x + num_w // 2, num_y + num_h // 2), num_text,
               font=f_num, fill=pal["white"], anchor="mm")

        # Conector visual: línea fina del número al borde derecho del slide
        line_y = num_y + num_h // 2
        d.line([x + num_w + mm(2), line_y, x + SLIDE_W, line_y],
               fill=pal["gray"], width=1)

        # ── Imagen del slide LIMPIA (sin overlay) ──
        img = PILImage.open(img_path).convert("RGB").resize((SLIDE_W, SLIDE_H), PILImage.LANCZOS)
        d.rectangle([x + 3, y + 3, x + SLIDE_W + 3, y + SLIDE_H + 3], fill=pal["gray"])
        canvas.paste(img, (x, y))
        d.rectangle([x, y, x + SLIDE_W, y + SLIDE_H], outline=pal["gray"], width=1)

        # ── Label debajo (smart-wrapped, hasta 2 líneas) ──
        lx = x + SLIDE_W // 2
        ly = y + SLIDE_H + mm(3)
        label_lines = make_label(slide, max_chars_per_line=22, max_lines=LABEL_LINES)
        for j, line in enumerate(label_lines[:LABEL_LINES]):
            d.text((lx, ly + j * LABEL_LINE_H), line,
                   font=f_label, fill=pal["dark"], anchor="mt")

    # Caption
    CAP_Y = SLIDE_Y + SLIDE_H + LABEL_H + mm(8)
    d.rounded_rectangle([MARGIN, CAP_Y, PW - MARGIN, CAP_Y + CAP_H],
                        radius=mm(3), fill=pal["light"], outline=pal["gray"], width=1)
    d.rectangle([MARGIN, CAP_Y, MARGIN + mm(3), CAP_Y + CAP_H], fill=pal["accent"])
    f_cap_head = load_font(24, bold=True)
    d.text((MARGIN + mm(6), CAP_Y + mm(4)), "CAPTION SUGERIDO", font=f_cap_head, fill=pal["primary"])

    f_cap = load_font(18)
    f_cta = load_font(20, bold=True)
    caption = data.get("caption") or ""
    paragraphs = caption.split("\n\n")
    col_w = (PW - 2 * MARGIN - mm(12)) // 2
    col_x = [MARGIN + mm(6), MARGIN + mm(6) + col_w + mm(6)]
    cur_y = [CAP_Y + mm(12), CAP_Y + mm(12)]
    line_h = mm(5.5)
    current_col = 0

    cta_kw = data.get("cta_keyword") or ""
    for para in paragraphs:
        is_cta = "▶" in para or (cta_kw and cta_kw in para)
        is_legal = "Coadyuvante" in para or "consulta veterinaria" in para.lower()
        fnt = f_cta if is_cta else f_cap
        clr = pal["accent"] if is_cta else (pal["gray"] if is_legal else pal["dark"])
        lh = int(line_h * 1.1) if is_cta else (int(line_h * 0.85) if is_legal else line_h)
        wrapped = textwrap.wrap(para, width=72)
        block_h = len(wrapped) * lh + mm(3)
        if current_col == 0 and cur_y[0] + block_h > CAP_Y + CAP_H - mm(4):
            current_col = 1
        for line in wrapped:
            if cur_y[current_col] + lh > CAP_Y + CAP_H - mm(3):
                break
            d.text((col_x[current_col], cur_y[current_col]), line, font=fnt, fill=clr)
            cur_y[current_col] += lh
        cur_y[current_col] += mm(2.5)

    f_foot = load_font(16)
    footer = f"SPEKGEN · {data.get('model_used','—')} · {data.get('client','—')} · {data.get('publish_date','—')}"
    d.text((PW // 2, PH - mm(4)), footer, font=f_foot, fill=pal["gray"], anchor="ms")

    return canvas

def build_whiteboard(batch_dir, data):
    """Single-post PDF: 1 page A3 landscape."""
    canvas = render_whiteboard_page(batch_dir, data)
    out = batch_dir / "_DELIVERABLES" / f"{data['post_id']}_WHITEBOARD.pdf"
    out.parent.mkdir(exist_ok=True)
    canvas.save(str(out), "PDF", resolution=DPI)
    print(f"  ✓ WHITEBOARD: {out}")
    return out

def _date_range_label(posts):
    """Saca un label de fecha bonito tipo 'Abril 2026' o '28 abril – 4 mayo 2026'."""
    dates = [p[1].get("publish_date") for p in posts if p[1].get("publish_date")]
    if not dates:
        return None
    dates_sorted = sorted(dates)
    first = format_date_pretty(dates_sorted[0])
    last = format_date_pretty(dates_sorted[-1])
    if first == last:
        return first
    # Si todos del mismo mes y año
    y1, m1, _ = dates_sorted[0].split("-")
    y2, m2, _ = dates_sorted[-1].split("-")
    if y1 == y2 and m1 == m2:
        return f"{MONTHS_ES.get(m1, m1).capitalize()} {y1}"
    return f"{first} – {last}"

def render_batch_cover_a3(batch_name, posts, client):
    """Cover editorial A3: client letters huge + meta block + thumbnails grid de slide 1 de cada post."""
    PW = mm(420); PH = mm(297)
    pal = get_palette(client)
    canvas = PILImage.new("RGB", (PW, PH), pal["white"])
    d = ImageDraw.Draw(canvas)

    # Top header bar (slim)
    HDR_H = mm(12)
    d.rectangle([0, 0, PW, HDR_H], fill=pal["primary"])
    f_brand = load_font(20, bold=True)
    f_brand_meta = load_font(16)
    d.text((mm(15), mm(2)), "SPEKGEN", font=f_brand, fill=pal["cream"])
    today = format_date_pretty(__import__('datetime').date.today().isoformat()) or ""
    d.text((PW - mm(15), mm(2)), f"Generado · {today}",
           font=f_brand_meta, fill=pal["cream"], anchor="rt")
    d.rectangle([0, HDR_H, PW, HDR_H + mm(2)], fill=pal["accent"])

    # ── LEFT BLOCK (huge meta) ──
    LEFT_X = mm(20)
    LEFT_W = mm(150)
    BODY_TOP = HDR_H + mm(15)

    # Client letters HUGE (HC, LF, GR, MG)
    f_client = load_font(220, bold=True)
    client_letters = (client or "—").upper()
    d.text((LEFT_X, BODY_TOP - mm(4)), client_letters, font=f_client, fill=pal["primary"])

    # Date range
    f_daterange = load_font(38, bold=True)
    drange = _date_range_label(posts) or ""
    d.text((LEFT_X, BODY_TOP + mm(72)), drange, font=f_daterange, fill=pal["accent"])

    # Batch name (smaller, lighter)
    f_batch = load_font(26)
    # Sanea nombre: HC_2026-04_DEMO → "HC 2026-04 DEMO"
    batch_pretty = batch_name.replace("_", " ")
    d.text((LEFT_X, BODY_TOP + mm(92)), batch_pretty, font=f_batch, fill=pal["dark"])

    # N posts pill
    f_n = load_font(28, bold=True)
    pill_text = f"  {len(posts)} POSTS  "
    bbox = d.textbbox((0, 0), pill_text, font=f_n)
    pw, ph = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pill_x = LEFT_X
    pill_y = BODY_TOP + mm(108)
    d.rounded_rectangle([pill_x, pill_y, pill_x + pw + mm(8), pill_y + ph + mm(6)],
                        radius=mm(3), fill=pal["primary"])
    d.text((pill_x + mm(4), pill_y + mm(2)), pill_text.strip(), font=f_n, fill=pal["white"])

    # Stamp REVISIÓN INTERNA
    f_stamp = load_font(18, bold=True)
    d.text((LEFT_X, BODY_TOP + mm(132)), "REVISIÓN INTERNA · NO PUBLICAR HASTA APROBACIÓN",
           font=f_stamp, fill=pal["gray"])

    # ── RIGHT BLOCK (thumbnails grid) ──
    RIGHT_X = mm(195)
    RIGHT_W = PW - RIGHT_X - mm(20)
    THUMB_TOP = BODY_TOP

    # Calcular grid: máximo 9 thumbnails (3x3). Para n posts:
    n = min(len(posts), 9)
    if n <= 1:
        cols = 1
    elif n <= 4:
        cols = 2
    elif n <= 9:
        cols = 3
    rows = (n + cols - 1) // cols

    GAP = mm(4)
    avail_h = PH - THUMB_TOP - mm(35)
    thumb_w = (RIGHT_W - (cols - 1) * GAP) // cols
    thumb_h = int(thumb_w * 1.25)  # 4:5 aspect
    # Si no cabe en alto, achicar
    needed_h = rows * thumb_h + (rows - 1) * GAP
    if needed_h > avail_h:
        thumb_h = (avail_h - (rows - 1) * GAP) // rows
        thumb_w = int(thumb_h / 1.25)

    # Centrar grid horizontalmente en RIGHT_W
    grid_w = cols * thumb_w + (cols - 1) * GAP
    grid_x = RIGHT_X + (RIGHT_W - grid_w) // 2

    f_label = load_font(14, bold=True)
    f_pid = load_font(13)

    for idx, (batch_dir, data) in enumerate(posts[:n]):
        col = idx % cols
        row = idx // cols
        tx = grid_x + col * (thumb_w + GAP)
        ty = THUMB_TOP + row * (thumb_h + GAP)

        # Get slide 1 winning variant
        post_id = data["post_id"]
        winners = data.get("winning_variants") or {}
        v = winners.get("1") or "v1"
        s1 = batch_dir / "FINAL" / f"{post_id}_S1_{v}.jpg"
        if not s1.exists():
            cands = sorted((batch_dir / "FINAL").glob(f"{post_id}_S1_v*.jpg"))
            s1 = cands[0] if cands else None

        if s1 and s1.exists():
            img = PILImage.open(s1).convert("RGB").resize((thumb_w, thumb_h), PILImage.LANCZOS)
            # Sombra
            d.rectangle([tx + 2, ty + 2, tx + thumb_w + 2, ty + thumb_h + 2], fill=pal["gray"])
            canvas.paste(img, (tx, ty))
            d.rectangle([tx, ty, tx + thumb_w, ty + thumb_h], outline=pal["dark"], width=1)
        else:
            # Placeholder dashed
            d.rectangle([tx, ty, tx + thumb_w, ty + thumb_h], outline=pal["gray"], width=2)
            d.text((tx + thumb_w // 2, ty + thumb_h // 2), "?", font=load_font(60, bold=True),
                   fill=pal["gray"], anchor="mm")

        # Number badge top-left
        bw = mm(8); bh = mm(6)
        d.rectangle([tx, ty, tx + bw, ty + bh], fill=pal["accent"])
        d.text((tx + mm(1.2), ty + mm(0.5)), f"{idx+1:02d}",
               font=load_font(15, bold=True), fill=pal["white"])

        # Post ID below
        d.text((tx + thumb_w // 2, ty + thumb_h + mm(1)), post_id,
               font=f_pid, fill=pal["dark"], anchor="mt")

    # Si hay más posts que el grid (>9), indicar
    if len(posts) > n:
        more = len(posts) - n
        d.text((RIGHT_X + RIGHT_W // 2, THUMB_TOP + rows * (thumb_h + GAP) + mm(2)),
               f"+ {more} más", font=load_font(16, bold=True),
               fill=pal["accent"], anchor="mt")

    # ── FOOTER ──
    d.rectangle([0, PH - mm(8), PW, PH - mm(6)], fill=pal["accent"])
    d.text((PW // 2, PH - mm(3)), f"SPEKGEN  ·  {client.upper()}  ·  Confidencial",
           font=load_font(13), fill=pal["gray"], anchor="ms")

    return canvas

def build_whiteboard_multi(posts, out_path, batch_name, client):
    """Multi-post PDF: cover + 1 page A3 per post."""
    pages = [render_batch_cover_a3(batch_name, posts, client)]
    for batch_dir, data in posts:
        pages.append(render_whiteboard_page(batch_dir, data))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(str(out_path), "PDF", resolution=DPI, save_all=True, append_images=pages[1:])
    print(f"  ✓ WHITEBOARD MULTI: {out_path} ({len(pages)} pages = 1 cover + {len(posts)} posts)")
    return out_path

# ── DECK A4 portrait multi-page ──────────────────────────────────────────────
def build_deck(batch_dir, data):
    PW = mm(210); PH = mm(297)
    pal = get_palette(data.get("client"))
    pages = []

    f_huge = load_font(56, bold=True)
    f_title = load_font(32, bold=True)
    f_meta = load_font(20)
    f_label = load_font(22, bold=True)
    f_cap = load_font(20)
    f_cta = load_font(22, bold=True)

    # Cover
    cover = PILImage.new("RGB", (PW, PH), pal["primary"])
    dc = ImageDraw.Draw(cover)
    dc.rectangle([0, mm(180), PW, mm(184)], fill=pal["accent"])
    dc.text((mm(15), mm(50)), data["post_id"], font=f_huge, fill=pal["accent"])
    title = fix_spanish(data.get("title") or data["post_id"])
    y = mm(80)
    for ln in textwrap.wrap(title, width=22)[:6]:
        dc.text((mm(15), y), ln, font=f_title, fill=pal["white"])
        y += mm(13)
    md_lines = [
        f"Cliente: {data.get('client','—')}",
        f"Pilar: {data.get('pillar','—')}",
        f"Formato: {data.get('format','—')}",
        f"Producto: {data.get('product','—')}",
        f"Publicación: {data.get('publish_date','—')} · {data.get('publish_time','—')}",
        f"Modelo IA: {data.get('model_used','—')}",
        f"Status: {data.get('status','—')}",
    ]
    y = mm(195)
    for ln in md_lines:
        dc.text((mm(15), y), ln, font=f_meta, fill=pal["cream"])
        y += mm(8)
    pages.append(cover)

    # Slides individuales
    images = get_winning_image_paths(batch_dir, data)
    for i, img_path in enumerate(images):
        slide = data["slides"][i]
        page = PILImage.new("RGB", (PW, PH), pal["white"])
        dp = ImageDraw.Draw(page)
        dp.rectangle([0, 0, PW, mm(15)], fill=pal["primary"])
        # Label en deck = todo en 1 línea, max 40 chars (cabe en header A4 portrait)
        deck_label = " ".join(make_label(slide, max_chars_per_line=40, max_lines=1))
        dp.text((mm(10), mm(3)),
                f"Slide {slide['num']}: {deck_label}",
                font=f_label, fill=pal["white"])

        max_w = PW - mm(30)
        max_h = PH - mm(60)
        img = PILImage.open(img_path).convert("RGB")
        ratio = min(max_w / img.width, max_h / img.height)
        new_w, new_h = int(img.width * ratio), int(img.height * ratio)
        img = img.resize((new_w, new_h), PILImage.LANCZOS)
        page.paste(img, ((PW - new_w) // 2, mm(20)))

        text_y = mm(20) + new_h + mm(8)
        if text_y < PH - mm(20) and slide.get("text"):
            for ln in textwrap.wrap(slide["text"], width=70)[:3]:
                dp.text((mm(15), text_y), ln, font=f_cap, fill=pal["dark"])
                text_y += mm(7)

        dp.text((PW // 2, PH - mm(7)),
                f"{data['post_id']} · {i+1}/{len(images)}",
                font=load_font(14), fill=pal["gray"], anchor="ms")
        pages.append(page)

    # Caption page
    cap = PILImage.new("RGB", (PW, PH), pal["white"])
    dc2 = ImageDraw.Draw(cap)
    dc2.rectangle([0, 0, PW, mm(15)], fill=pal["primary"])
    dc2.text((mm(10), mm(3)), "CAPTION + CTA", font=f_label, fill=pal["white"])
    y = mm(25)
    cta_kw = data.get("cta_keyword") or ""
    for para in (data.get("caption") or "").split("\n\n"):
        is_cta = "▶" in para or (cta_kw and cta_kw in para)
        fnt = f_cta if is_cta else f_cap
        clr = pal["accent"] if is_cta else pal["dark"]
        for ln in textwrap.wrap(para, width=60):
            if y > PH - mm(20):
                break
            dc2.text((mm(15), y), ln, font=fnt, fill=clr)
            y += mm(7)
        y += mm(3)
    if data.get("hashtags"):
        y += mm(5)
        dc2.text((mm(15), y), "Hashtags: " + " ".join(data["hashtags"]),
                 font=load_font(16), fill=pal["gray"])
    pages.append(cap)

    out = batch_dir / "_DELIVERABLES" / f"{data['post_id']}_DECK.pdf"
    out.parent.mkdir(exist_ok=True)
    pages[0].save(str(out), "PDF", resolution=DPI, save_all=True, append_images=pages[1:])
    print(f"  ✓ DECK: {out} ({len(pages)} pages)")
    return out

# ════════════════════════════════════════════════════════════════════════════
# ADS RECAP — overview grid + per-ad deck
# ════════════════════════════════════════════════════════════════════════════

def _format_ad_label(format_code):
    """MULTIPRODUCT_STACK → 'Multiproduct Stack'."""
    if not format_code:
        return "—"
    return format_code.replace("_", " ").title()

def _get_ad_image_path(batch_dir, entry):
    """Devuelve path de la imagen ganadora del ad, o v1 fallback."""
    final = batch_dir / "FINAL"
    code = entry["ad_code"]
    winner = entry.get("winning_variant") or "v1"
    p = final / f"{code}_{winner}.jpg"
    if p.exists():
        return p
    cands = sorted(final.glob(f"{code}_v*.jpg"))
    return cands[0] if cands else None

def render_ads_overview_a3(batch_dir, data):
    """1-página A3 landscape: cover-style con metadata + grid de thumbnails de TODOS los ads del batch."""
    PW = mm(420); PH = mm(297)
    pal = get_palette(data.get("client") or "HC")
    canvas = PILImage.new("RGB", (PW, PH), pal["white"])
    d = ImageDraw.Draw(canvas)

    # Header bar
    HDR_H = mm(18)
    d.rectangle([0, 0, PW, HDR_H], fill=pal["primary"])
    f_title = load_font(36, bold=True)
    f_meta = load_font(20)
    batch_id = data.get("batch_id") or batch_dir.name
    client = (data.get("client") or "—").upper()
    n_ads = len(data.get("entries", []))
    d.text((mm(12), mm(3)), f"{batch_id}", font=f_title, fill=pal["white"])
    meta_parts = [
        f"Client: {client}",
        f"{n_ads} ads",
        f"Modelo: {data.get('model_used','—')}",
        format_date_pretty(data.get("created")) or "",
        f"Status: {data.get('status','DRAFT')}",
        "REVISIÓN INTERNA",
    ]
    d.text((mm(12), mm(11)), "  ·  ".join([p for p in meta_parts if p]),
           font=f_meta, fill=pal["cream"])
    d.rectangle([0, HDR_H, PW, HDR_H + mm(2)], fill=pal["accent"])

    # Grid de thumbnails
    entries = data.get("entries", [])
    N = max(len(entries), 1)
    MARGIN = mm(12)
    GAP = mm(5)
    NUM_TAB_H = mm(8)
    LABEL_H = mm(14)  # 2 líneas: ad_code corto + format

    # Layout: cuántas columnas / filas
    if N <= 3:
        cols = N
    elif N <= 6:
        cols = 3
    elif N <= 9:
        cols = 3
    elif N <= 12:
        cols = 4
    elif N <= 16:
        cols = 4
    else:
        cols = 5
    rows = (N + cols - 1) // cols

    AVAIL_W = PW - 2 * MARGIN
    AVAIL_H = PH - HDR_H - mm(2) - MARGIN - mm(8)  # footer space
    THUMB_W = (AVAIL_W - (cols - 1) * GAP) // cols
    THUMB_H_max = (AVAIL_H - rows * (NUM_TAB_H + LABEL_H) - (rows - 1) * GAP) // rows
    THUMB_H = min(int(THUMB_W * 1.0), THUMB_H_max)  # 1:1 para ads (más común aspect ratio)
    if THUMB_H < mm(30):  # piso
        THUMB_H = mm(30)

    grid_w = cols * THUMB_W + (cols - 1) * GAP
    x_start = (PW - grid_w) // 2
    grid_h = rows * (NUM_TAB_H + THUMB_H + LABEL_H) + (rows - 1) * GAP
    y_start = HDR_H + mm(2) + (AVAIL_H - grid_h) // 2 + mm(4)

    f_num = load_font(22, bold=True)
    f_code = load_font(13, bold=True)
    f_format = load_font(12)

    for i, entry in enumerate(entries):
        col = i % cols
        row = i // cols
        x = x_start + col * (THUMB_W + GAP)
        cell_y = y_start + row * (NUM_TAB_H + THUMB_H + LABEL_H + GAP)

        # Number tab encima
        num_w = mm(11)
        num_y = cell_y
        d.rounded_rectangle([x, num_y, x + num_w, num_y + NUM_TAB_H - mm(1)],
                            radius=mm(1.5), fill=pal["primary"])
        d.text((x + num_w // 2, num_y + (NUM_TAB_H - mm(1)) // 2),
               f"{i+1:02d}", font=f_num, fill=pal["white"], anchor="mm")
        # Línea conectora
        line_y = num_y + (NUM_TAB_H - mm(1)) // 2
        d.line([x + num_w + mm(2), line_y, x + THUMB_W, line_y],
               fill=pal["gray"], width=1)

        # Imagen
        img_y = cell_y + NUM_TAB_H
        img_path = _get_ad_image_path(batch_dir, entry)
        if img_path and img_path.exists():
            img = PILImage.open(img_path).convert("RGB").resize((THUMB_W, THUMB_H), PILImage.LANCZOS)
            d.rectangle([x + 2, img_y + 2, x + THUMB_W + 2, img_y + THUMB_H + 2], fill=pal["gray"])
            canvas.paste(img, (x, img_y))
            d.rectangle([x, img_y, x + THUMB_W, img_y + THUMB_H], outline=pal["gray"], width=1)
        else:
            # Placeholder dashed rojo si falta imagen
            d.rectangle([x, img_y, x + THUMB_W, img_y + THUMB_H], outline=(200, 60, 60), width=2)
            d.text((x + THUMB_W // 2, img_y + THUMB_H // 2), "FALTA",
                   font=load_font(20, bold=True), fill=(200, 60, 60), anchor="mm")

        # Label: ad_code + format
        lbl_y = img_y + THUMB_H + mm(2)
        # ad_code: truncado si muy largo
        code = entry.get("ad_code", "—")
        if len(code) > 28:
            code = code[:26] + "…"
        d.text((x + THUMB_W // 2, lbl_y), code, font=f_code, fill=pal["dark"], anchor="mt")
        fmt = _format_ad_label(entry.get("format"))
        status = entry.get("status", "—")
        d.text((x + THUMB_W // 2, lbl_y + mm(5)), f"{fmt} · {status}",
               font=f_format, fill=pal["gray"], anchor="mt")

    # Footer
    d.rectangle([0, PH - mm(8), PW, PH - mm(6)], fill=pal["accent"])
    d.text((PW // 2, PH - mm(3)), f"SPEKGEN  ·  {client}  ·  Confidencial",
           font=load_font(13), fill=pal["gray"], anchor="ms")

    return canvas

def build_ads_overview(batch_dir, data):
    """v3: Delega a matrix recap (HTML+Playwright). Old Pillow grid renombrada a fallback."""
    return build_ads_matrix_recap(batch_dir, data)


def build_ads_overview_pillow_legacy(batch_dir, data):
    """v2 fallback: Pillow grid simple. Solo usar si Playwright no disponible."""
    canvas = render_ads_overview_a3(batch_dir, data)
    out = batch_dir / "_DELIVERABLES" / f"{data.get('batch_id', batch_dir.name)}_OVERVIEW.pdf"
    out.parent.mkdir(exist_ok=True)
    canvas.save(str(out), "PDF", resolution=DPI)
    print(f"  ✓ ADS OVERVIEW (legacy Pillow): {out}")
    return out


def build_ads_matrix_recap(batch_dir, data):
    """v3 recap: whiteboard matrix per-bucket via HTML+Playwright.

    Lee _buckets/{client}.json para colores + labels. Grupifica por bucket.
    Renderiza cobertura matrix + per-bucket detail rows con thumbnails + status Meta.
    Output: {batch_id}_recap.pdf en root del batch_dir.
    """
    import base64
    from datetime import datetime
    batch_dir = Path(batch_dir)
    batch_id = data.get("batch_id", batch_dir.name)
    client = data.get("client", "LF")

    # Load _buckets/{CLIENT}.json
    skill_dir = Path(__file__).parent.parent
    buckets_path = skill_dir / "_buckets" / f"{client}.json"
    if not buckets_path.exists():
        print(f"  ⚠ _buckets/{client}.json no existe — usando defaults")
        buckets_cfg = {
            "buckets": {
                "OFFER": {"color": "#059669", "label": "Offer"},
                "LUPITA+OFFER": {"color": "#7C3AED", "label": "Lupita+Offer"},
                "LUPITA+AUTHORITY": {"color": "#0EA5E9", "label": "Lupita+Authority"},
                "PROBLEM-SOLUTION": {"color": "#F59E0B", "label": "Problem-Solution"},
                "WILDCARD": {"color": "#DC2626", "label": "Wildcard"},
            },
            "ad_account": "TBD"
        }
    else:
        buckets_cfg = json.loads(buckets_path.read_text())

    BUCKET_DEFS = buckets_cfg["buckets"]
    AD_ACCT = buckets_cfg.get("ad_account", "").replace("act_", "")

    def meta_link(ad_id):
        return f"https://adsmanager.facebook.com/adsmanager/manage/ads/edit?act={AD_ACCT}&selected_ad_ids={ad_id}"

    def img_b64(p):
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode()

    # Group entries by bucket (normalize parenthetical formats)
    import re as _re
    grouped = {b: [] for b in BUCKET_DEFS}
    for e in data.get("entries", []):
        fmt_norm = _re.sub(r"\s*\(.*?\)\s*", "", e.get("format", "")).strip()
        if fmt_norm in grouped:
            grouped[fmt_norm].append(e)
        else:
            # Fallback: try first match by prefix
            matched = False
            for k in BUCKET_DEFS:
                if fmt_norm.startswith(k):
                    grouped[k].append(e)
                    matched = True
                    break
            if not matched:
                # Last resort: assign to WILDCARD
                if "WILDCARD" in grouped:
                    grouped["WILDCARD"].append(e)

    uploaded = sum(1 for e in data.get("entries", []) if e.get("meta_ad_id"))
    dropped = sum(1 for e in data.get("entries", []) if e.get("status") == "DROPPED")

    # Coverage matrix row
    cov_cells_html = ""
    for bucket, defn in BUCKET_DEFS.items():
        entries = grouped[bucket]
        if not entries:
            cov_cells_html += '<td class="cov-cell cov-empty"><div class="cov-num">0 ✗</div><div class="cov-codes">—</div></td>'
        else:
            codes = ", ".join(e["ad_code"].split("_")[0] for e in entries)
            active = sum(1 for e in entries if e.get("meta_ad_id"))
            drop = sum(1 for e in entries if e.get("status") == "DROPPED")
            icons = ""
            if active: icons += f'<span class="ok">{active}✓</span> '
            if drop: icons += f'<span class="drop">{drop}⊘</span>'
            cov_cells_html += f'<td class="cov-cell"><div class="cov-num">{len(entries)}</div><div class="cov-icons">{icons}</div><div class="cov-codes">{codes}</div></td>'

    # Per-bucket rows with tiles
    detail_rows_html = ""
    for bucket, defn in BUCKET_DEFS.items():
        color = defn["color"]
        label = defn.get("label", bucket)
        entries = grouped[bucket]
        if not entries:
            detail_rows_html += f'''
            <tr>
              <td class="bucket" style="background:{color}">{label}</td>
              <td><div class="faltante"><div class="faltante-text">FALTANTE</div><div class="faltante-sub" style="background:{color}">{label}</div><div class="faltante-detail">Producir variantes próximo batch</div></div></td>
            </tr>'''
            continue
        tiles_html = ""
        for e in entries:
            code_short = e["ad_code"].split("_")[0]
            product = e.get("product", "")[:50]
            if e.get("status") == "DROPPED":
                tiles_html += f'''<div class="tile dropped"><div class="tile-img dropped-img">DROPPED</div><div class="tile-meta"><div class="tile-code">{code_short}</div><div class="tile-product">{product}</div><div class="tile-status status-dropped">⊘ DROPPED</div><div class="tile-detail">Concept rechazado</div></div></div>'''
            else:
                img_path = batch_dir / e.get("final_image_path", "")
                if img_path.exists():
                    img_data = img_b64(img_path)
                    img_tag = f'<img class="tile-img" src="data:image/png;base64,{img_data}" />'
                else:
                    img_tag = '<div class="tile-img missing">FALTA IMG</div>'
                ad_id = e.get("meta_ad_id", "")
                status_label = "● UPLOADED ACTIVE" if ad_id else "○ READY"
                status_class = "status-uploaded" if ad_id else "status-ready"
                link_html = f'<a class="tile-link" href="{meta_link(ad_id)}">→ Ver en Meta</a>' if ad_id else ""
                id_html = f'<div class="tile-id">{ad_id}</div>' if ad_id else ""
                tiles_html += f'''<div class="tile">{img_tag}<div class="tile-meta"><div class="tile-code">{code_short}</div><div class="tile-product">{product}</div><div class="tile-status {status_class}">{status_label}</div>{id_html}{link_html}</div></div>'''
        detail_rows_html += f'''
            <tr>
              <td class="bucket" style="background:{color}">{label}</td>
              <td><div class="tiles-row">{tiles_html}</div></td>
            </tr>'''

    bucket_headers_html = "".join(
        f'<th class="bucket-header" style="background:{defn["color"]}">{defn.get("label", b)}</th>'
        for b, defn in BUCKET_DEFS.items()
    )

    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @page {{ size: A3 landscape; margin: 14mm; }}
  body {{ font-family: -apple-system, 'Inter', sans-serif; color: #1F2937; margin: 0; padding: 18px; }}
  h1 {{ color: #6B4FBB; font-size: 28px; margin-bottom: 4px; }}
  .meta {{ color: #6B7280; font-size: 12px; margin-bottom: 4px; }}
  .stats {{ color: #1F2937; font-size: 13px; margin-bottom: 18px; }}
  .stats strong {{ color: #6B4FBB; }}
  hr {{ border: none; border-top: 2px solid #E5E7EB; margin: 14px 0; }}
  h2 {{ color: #1F2937; font-size: 16px; margin: 18px 0 10px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  .coverage th, .coverage td {{ border: 1px solid #E5E7EB; padding: 12px 10px; text-align: center; vertical-align: top; }}
  .coverage th {{ background: #F3F4F6; font-size: 12px; font-weight: 700; }}
  .coverage th.bucket-header {{ color: white; padding: 12px 8px; }}
  .coverage .row-label {{ background: #6B4FBB; color: white; font-weight: 800; font-size: 18px; width: 60px; text-align: center; }}
  .cov-cell {{ font-size: 11px; }}
  .cov-num {{ font-size: 28px; font-weight: 800; color: #1F2937; line-height: 1; }}
  .cov-icons {{ margin: 4px 0; font-size: 14px; font-weight: 700; }}
  .cov-icons .ok {{ color: #059669; }}
  .cov-icons .drop {{ color: #DC2626; }}
  .cov-codes {{ font-size: 9px; color: #6B7280; }}
  .cov-empty .cov-num {{ color: #DC2626; }}
  .tiles {{ width: 100%; border-collapse: separate; border-spacing: 0; }}
  .tiles td {{ vertical-align: top; padding: 8px; border: 1px solid #E5E7EB; }}
  .bucket {{ color: white; font-weight: 800; font-size: 12px; padding: 14px 10px !important; text-align: center; width: 110px; vertical-align: middle !important; letter-spacing: 0.5px; }}
  .tiles-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .tile {{ width: 175px; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
  .tile-img {{ width: 175px; height: 218px; object-fit: cover; display: block; }}
  .tile-img.missing {{ background: #FEE2E2; color: #DC2626; display: flex; align-items: center; justify-content: center; font-weight: 800; }}
  .tile-meta {{ padding: 7px 8px; font-size: 9.5px; line-height: 1.3; }}
  .tile-code {{ font-weight: 800; color: #1F2937; font-size: 10.5px; font-family: 'SF Mono', Monaco, monospace; }}
  .tile-product {{ color: #4B5563; margin: 2px 0; }}
  .tile-status {{ font-weight: 700; margin-top: 4px; font-size: 9px; }}
  .status-uploaded {{ color: #059669; }}
  .status-ready {{ color: #F59E0B; }}
  .status-dropped {{ color: #DC2626; }}
  .tile-id {{ color: #6B7280; font-family: 'SF Mono', Monaco, monospace; font-size: 8px; margin-top: 2px; }}
  .tile-link {{ color: #6B4FBB; text-decoration: none; font-size: 9px; display: block; margin-top: 2px; font-weight: 600; }}
  .tile.dropped {{ opacity: 0.6; }}
  .dropped-img {{ background: #FEE2E2; color: #DC2626; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px; height: 218px; }}
  .tile-detail {{ color: #6B7280; font-style: italic; font-size: 8.5px; margin-top: 2px; }}
  .faltante {{ border: 2px dashed #DC2626; background: #FEF2F2; padding: 28px; text-align: center; border-radius: 6px; }}
  .faltante-text {{ color: #DC2626; font-size: 22px; font-weight: 800; }}
  .faltante-sub {{ color: white; display: inline-block; padding: 3px 12px; border-radius: 12px; font-size: 11px; margin: 8px 0; font-weight: 700; }}
  .faltante-detail {{ color: #6B7280; font-size: 11px; margin-top: 4px; }}
  .footer {{ color: #9CA3AF; font-size: 9px; margin-top: 18px; padding-top: 10px; border-top: 1px dashed #E5E7EB; line-height: 1.4; }}
</style></head>
<body>
<h1>{batch_id} — Recap</h1>
<div class="meta">SPEKGEN Factory · {client} · Render {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
<div class="stats"><strong>{len(data.get("entries", []))}</strong> ads totales · <strong>{uploaded}</strong> uploaded · <strong>{dropped}</strong> dropped</div>
<hr/>
<h2>Matriz de cobertura · {client} × Buckets</h2>
<table class="coverage">
  <tr><th></th>{bucket_headers_html}</tr>
  <tr><td class="row-label">{client}</td>{cov_cells_html}</tr>
</table>
<h2>Ads por Bucket</h2>
<table class="tiles">{detail_rows_html}</table>
<div class="footer">Buckets: {' · '.join(f'<strong>{defn.get("label", b)}</strong>' for b, defn in BUCKET_DEFS.items())}.<br/>Links "→ Ver en Meta" abren Ads Manager del cliente en pestaña nueva.</div>
</body></html>'''

    html_path = batch_dir / "_recap_render.html"
    html_path.write_text(html, encoding="utf-8")

    pdf_path = batch_dir / f"{batch_id}_recap.pdf"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            page.pdf(path=str(pdf_path), format="A3", landscape=True,
                     margin={"top":"10mm","bottom":"10mm","left":"10mm","right":"10mm"},
                     print_background=True)
            browser.close()
        print(f"  ✓ ADS RECAP MATRIX: {pdf_path}")
        return pdf_path
    except ImportError:
        print(f"  ⚠ Playwright no instalado — fallback a Pillow legacy")
        return build_ads_overview_pillow_legacy(batch_dir, data)
    except Exception as e:
        print(f"  ⚠ Playwright error: {e} — fallback Pillow")
        return build_ads_overview_pillow_legacy(batch_dir, data)

def build_ads_deck(batch_dir, data):
    """Multi-page A4: 1 ad por página con imagen + ad_copy box."""
    PW = mm(210); PH = mm(297)
    pal = get_palette(data.get("client") or "HC")
    pages = []

    f_huge = load_font(48, bold=True)
    f_title = load_font(28, bold=True)
    f_meta = load_font(18)
    f_label = load_font(20, bold=True)
    f_body = load_font(16)
    f_body_bold = load_font(16, bold=True)
    f_small = load_font(13)

    # ── Cover ──
    cover = PILImage.new("RGB", (PW, PH), pal["primary"])
    dc = ImageDraw.Draw(cover)
    dc.rectangle([0, mm(180), PW, mm(184)], fill=pal["accent"])
    dc.text((mm(15), mm(40)), "ADS BATCH", font=f_huge, fill=pal["accent"])
    batch_id = data.get("batch_id", batch_dir.name)
    dc.text((mm(15), mm(60)), batch_id, font=f_title, fill=pal["white"])
    md_lines = [
        f"Cliente: {(data.get('client') or '—').upper()}",
        f"# Ads: {len(data.get('entries', []))}",
        f"Modelo: {data.get('model_used','—')}",
        f"Created: {format_date_pretty(data.get('created')) or '—'}",
        f"Status: {data.get('status','DRAFT')}",
    ]
    y = mm(195)
    for ln in md_lines:
        dc.text((mm(15), y), ln, font=f_meta, fill=pal["cream"])
        y += mm(8)
    pages.append(cover)

    # ── Per-ad page ──
    for i, entry in enumerate(data.get("entries", [])):
        page = PILImage.new("RGB", (PW, PH), pal["white"])
        dp = ImageDraw.Draw(page)

        # Header
        dp.rectangle([0, 0, PW, mm(15)], fill=pal["primary"])
        ad_code = entry.get("ad_code", "—")
        dp.text((mm(8), mm(3)), f"#{i+1:02d}  {ad_code}",
                font=f_label, fill=pal["white"])

        # Imagen (centrada, max 110mm)
        img_path = _get_ad_image_path(batch_dir, entry)
        max_w = PW - mm(30)
        max_h = mm(120)
        if img_path and img_path.exists():
            img = PILImage.open(img_path).convert("RGB")
            ratio = min(max_w / img.width, max_h / img.height)
            new_w = int(img.width * ratio); new_h = int(img.height * ratio)
            img = img.resize((new_w, new_h), PILImage.LANCZOS)
            ix = (PW - new_w) // 2
            iy = mm(20)
            page.paste(img, (ix, iy))
        else:
            iy = mm(20)
            new_h = max_h
            dp.rectangle([mm(15), iy, PW - mm(15), iy + new_h], outline=(200,60,60), width=2)
            dp.text((PW//2, iy + new_h//2), "FALTA IMAGEN", font=f_label,
                    fill=(200,60,60), anchor="mm")

        # Ad copy box debajo
        box_y = iy + new_h + mm(8)
        box_h = PH - box_y - mm(10)
        dp.rounded_rectangle([mm(10), box_y, PW - mm(10), box_y + box_h],
                             radius=mm(2), fill=pal["light"], outline=pal["gray"], width=1)
        dp.rectangle([mm(10), box_y, mm(13), box_y + box_h], fill=pal["accent"])

        # Format + status + meta_id chip-row
        cy = box_y + mm(3)
        dp.text((mm(16), cy), f"Format: ", font=f_body_bold, fill=pal["dark"])
        dp.text((mm(34), cy), _format_ad_label(entry.get("format")),
                font=f_body, fill=pal["primary"])
        dp.text((mm(95), cy), f"Status: ", font=f_body_bold, fill=pal["dark"])
        dp.text((mm(112), cy), entry.get("status", "—"), font=f_body, fill=pal["primary"])
        meta_id = entry.get("meta_ad_id")
        if meta_id:
            dp.text((mm(150), cy), f"Meta: {meta_id}", font=f_small, fill=pal["gray"])

        cy += mm(7)
        # Product + audience + landing
        product = entry.get("product", "—")
        dp.text((mm(16), cy), f"Producto: ", font=f_body_bold, fill=pal["dark"])
        dp.text((mm(40), cy), product, font=f_body, fill=pal["dark"])
        cy += mm(6)

        # Hook on image
        hook = entry.get("hook_text_on_image")
        if hook:
            dp.text((mm(16), cy), "Hook:", font=f_body_bold, fill=pal["dark"])
            cy += mm(5)
            for ln in textwrap.wrap(hook, width=70)[:2]:
                if cy > box_y + box_h - mm(5):
                    break
                dp.text((mm(16), cy), ln, font=f_body, fill=pal["accent"])
                cy += mm(5)
            cy += mm(2)

        # Ad copy
        ac = entry.get("ad_copy") or {}
        if ac.get("headline"):
            dp.text((mm(16), cy), "Headline:", font=f_body_bold, fill=pal["dark"])
            cy += mm(5)
            for ln in textwrap.wrap(ac["headline"], width=70)[:2]:
                if cy > box_y + box_h - mm(5):
                    break
                dp.text((mm(16), cy), ln, font=f_body, fill=pal["dark"])
                cy += mm(5)
            cy += mm(1)

        if ac.get("primary_text"):
            dp.text((mm(16), cy), "Primary text:", font=f_body_bold, fill=pal["dark"])
            cy += mm(5)
            for ln in textwrap.wrap(ac["primary_text"], width=72)[:5]:
                if cy > box_y + box_h - mm(8):
                    break
                dp.text((mm(16), cy), ln, font=f_body, fill=pal["dark"])
                cy += mm(5)
            cy += mm(1)

        if ac.get("cta_type") or ac.get("landing_url"):
            cta = ac.get("cta_type", "—")
            url = ac.get("landing_url", "")
            url_short = (url[:60] + "…") if len(url) > 60 else url
            dp.text((mm(16), cy), f"CTA: {cta}  ·  {url_short}",
                    font=f_small, fill=pal["gray"])

        # Footer
        dp.text((PW // 2, PH - mm(5)),
                f"{batch_id} · {i+1}/{len(data.get('entries', []))}",
                font=f_small, fill=pal["gray"], anchor="ms")
        pages.append(page)

    out = batch_dir / "_DELIVERABLES" / f"{data.get('batch_id', batch_dir.name)}_DECK.pdf"
    out.parent.mkdir(exist_ok=True)
    pages[0].save(str(out), "PDF", resolution=DPI, save_all=True, append_images=pages[1:])
    print(f"  ✓ ADS DECK: {out} ({len(pages)} pages = 1 cover + {len(data.get('entries', []))} ads)")
    return out


def main():
    ap = argparse.ArgumentParser(description="Genera PDF whiteboard/deck para 1 post o N posts en multi mode.")
    ap.add_argument("batch_dir", help="Folder de un post (single) o folder padre con N post folders (--multi)")
    ap.add_argument("--format", choices=["whiteboard", "deck", "both"], default="both")
    ap.add_argument("--multi", action="store_true",
                    help="Trata batch_dir como padre con múltiples post subfolders (cada uno con batch.json).")
    ap.add_argument("--name", help="Nombre del batch para el cover en --multi (default: nombre del folder)")
    ap.add_argument("--posts", nargs="+",
                    help="(Solo --multi) Lista explícita de post_ids a incluir en orden. Si se omite, toma todos.")
    args = ap.parse_args()

    bd = Path(args.batch_dir).resolve()

    # ── Multi-post mode ──
    if args.multi:
        if not bd.is_dir():
            sys.exit(f"--multi requiere un folder existente: {bd}")

        # Recolectar posts: si --posts se especifica, en ese orden; sino, sorted dirlist
        posts = []
        if args.posts:
            for pid in args.posts:
                cand = bd / pid
                bj = cand / "batch.json"
                if not bj.exists():
                    print(f"  [WARN] {pid} no tiene batch.json, skip")
                    continue
                posts.append((cand, json.loads(bj.read_text())))
        else:
            for sub in sorted(bd.iterdir()):
                if sub.is_dir() and sub.name != "_DELIVERABLES" and (sub / "batch.json").exists():
                    data = json.loads((sub / "batch.json").read_text())
                    # Detección de "post" content: tiene post_id y slides (vs ads batch que tiene entries[])
                    if data.get("post_id") and data.get("slides"):
                        posts.append((sub, data))

        if not posts:
            sys.exit(f"No content posts encontrados en {bd}")

        batch_name = args.name or bd.name
        client = posts[0][1].get("client", "HC")
        out_dir = bd / "_DELIVERABLES"
        out_dir.mkdir(exist_ok=True)

        print(f"\nBuilding MULTI-POST deliverables · batch={batch_name} · {len(posts)} posts · client={client}\n")
        for i, (_, d_) in enumerate(posts, 1):
            print(f"  {i:02d}. {d_['post_id']} — {fix_spanish(d_.get('title') or '')[:60]}")

        if args.format in ("whiteboard", "both"):
            print()
            build_whiteboard_multi(posts, out_dir / f"{batch_name}_WHITEBOARD.pdf", batch_name, client)

        if args.format in ("deck", "both"):
            print()
            # Para deck en multi: genera un deck por post (los decks son largos individualmente)
            for pd, pdata in posts:
                build_deck(pd, pdata)
        print()
        return

    # ── Single mode (content o ads) ──
    bj = bd / "batch.json"
    if not bj.exists():
        sys.exit(f"No existe {bj}")
    data = json.loads(bj.read_text())

    is_ads = data.get("type") == "ads" or "entries" in data
    is_content = "slides" in data or data.get("type") == "content"

    if is_ads:
        batch_id = data.get("batch_id", bd.name)
        print(f"\nBuilding ADS deliverables for {batch_id} ({data.get('client')})…\n")
        # Para ads: --format whiteboard → overview ; --format deck → deck ; both → ambos
        if args.format in ("whiteboard", "both"):
            build_ads_overview(bd, data)
        if args.format in ("deck", "both"):
            build_ads_deck(bd, data)
    elif is_content:
        print(f"\nBuilding CONTENT deliverables for {data['post_id']} ({data.get('client')})…\n")
        if args.format in ("whiteboard", "both"):
            build_whiteboard(bd, data)
        if args.format in ("deck", "both"):
            build_deck(bd, data)
    else:
        sys.exit("Schema no reconocido. Necesita 'slides' (content) o 'entries' (ads).")
    print()

if __name__ == "__main__":
    main()
