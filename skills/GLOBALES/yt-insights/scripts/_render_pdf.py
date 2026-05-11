"""Markdown → HTML → PDF rendering with Playwright + dark SPEKGEN CSS."""
import re
import sys
import json
import base64
from pathlib import Path
from html import escape

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
TEMPLATES = ROOT.parent / "templates"


def _md_to_html(md_text: str, screenshots_by_ts: dict = None) -> str:
    """
    Convert markdown to HTML using a small custom parser.
    Supports: # ## ###, **bold**, *italic*, `code`, code blocks ```,
    lists (- and 1.), tables (| ... |), > quotes, links [a](b),
    horizontal rules ---, and a custom {{ts:14:label}} screenshot inline marker.
    """
    if screenshots_by_ts is None:
        screenshots_by_ts = {}

    lines = md_text.split("\n")
    out = []
    i = 0
    in_code = False
    code_lang = ""
    in_table = False
    table_rows = []

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        # First row = header, second = separator (skip), rest = body
        header = table_rows[0]
        body = table_rows[2:] if len(table_rows) > 2 else []
        out.append('<table>')
        out.append('<thead><tr>')
        for c in header:
            out.append(f'<th>{_inline(c.strip())}</th>')
        out.append('</tr></thead>')
        out.append('<tbody>')
        for row in body:
            out.append('<tr>')
            for c in row:
                out.append(f'<td>{_inline(c.strip())}</td>')
            out.append('</tr>')
        out.append('</tbody></table>')
        table_rows = []

    def _inline(text: str) -> str:
        # Code spans
        text = re.sub(r"`([^`]+)`", lambda m: f'<code>{escape(m.group(1))}</code>', text)
        # Bold
        text = re.sub(r"\*\*([^\*]+)\*\*", r"<strong>\1</strong>", text)
        # Italic (avoid matching ** by checking surroundings)
        text = re.sub(r"(?<!\*)\*([^\*\n]+)\*(?!\*)", r"<em>\1</em>", text)
        # Links
        text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', text)
        # Obsidian-style backlinks [[X]]
        text = re.sub(r"\[\[([^\]]+)\]\]", r'<span class="backlink">\1</span>', text)
        return text

    while i < len(lines):
        line = lines[i]
        # Code blocks
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip()
                out.append(f'<pre class="code lang-{code_lang}"><code>')
            else:
                in_code = False
                out.append('</code></pre>')
            i += 1
            continue
        if in_code:
            out.append(escape(line))
            i += 1
            continue

        # Tables
        if "|" in line and re.match(r"^\s*\|.+\|\s*$", line):
            cells = [c for c in line.strip().strip("|").split("|")]
            table_rows.append(cells)
            in_table = True
            i += 1
            continue
        else:
            if in_table:
                flush_table()
                in_table = False

        # Horizontal rule
        if re.match(r"^---+\s*$", line):
            out.append('<hr/>')
            i += 1
            continue

        # Headers
        if line.startswith("# "):
            out.append(f'<h1>{_inline(line[2:].strip())}</h1>')
            i += 1
            continue
        if line.startswith("## "):
            out.append(f'<h2>{_inline(line[3:].strip())}</h2>')
            i += 1
            continue
        if line.startswith("### "):
            out.append(f'<h3>{_inline(line[4:].strip())}</h3>')
            i += 1
            continue
        if line.startswith("#### "):
            out.append(f'<h4>{_inline(line[5:].strip())}</h4>')
            i += 1
            continue

        # Quote
        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            out.append(f'<blockquote>{_inline(" ".join(quote_lines))}</blockquote>')
            continue

        # Unordered list
        if re.match(r"^\s*[-*+]\s+", line):
            out.append('<ul>')
            while i < len(lines) and re.match(r"^\s*[-*+]\s+", lines[i]):
                item = re.sub(r"^\s*[-*+]\s+", "", lines[i])
                out.append(f'<li>{_inline(item)}</li>')
                i += 1
            out.append('</ul>')
            continue

        # Ordered list
        if re.match(r"^\s*\d+\.\s+", line):
            out.append('<ol>')
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i])
                out.append(f'<li>{_inline(item)}</li>')
                i += 1
            out.append('</ol>')
            continue

        # Empty line
        if not line.strip():
            i += 1
            continue

        # Paragraph (collect until empty line)
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not _is_block_start(lines[i]):
            para.append(lines[i])
            i += 1
        out.append(f'<p>{_inline(" ".join(para))}</p>')

    if in_table:
        flush_table()

    return "\n".join(out)


def _is_block_start(line: str) -> bool:
    return (
        line.startswith(("#", "```", ">", "---"))
        or re.match(r"^\s*[-*+]\s+", line) is not None
        or re.match(r"^\s*\d+\.\s+", line) is not None
        or re.match(r"^\s*\|.+\|\s*$", line) is not None
    )


def _img_data_uri(path: str) -> str:
    """Embed image as base64 data URI."""
    p = Path(path)
    if not p.exists():
        return ""
    data = base64.b64encode(p.read_bytes()).decode()
    return f"data:image/png;base64,{data}"


def _render_with_playwright(html: str, out_pdf: Path):
    """Render HTML to PDF using Playwright headless chromium."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(
            path=str(out_pdf),
            format="A4",
            margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"},
            print_background=True,
            display_header_footer=False,
        )
        browser.close()


def render_insights_pdf(md: str, out_path: Path, meta: dict):
    env = Environment(loader=FileSystemLoader(TEMPLATES))
    body_html = _md_to_html(md)
    template = env.get_template("pdf_base.html.j2")
    html = template.render(
        title=meta["title"],
        subtitle="Insights & Action Items",
        kicker=f"{meta['channel']} · {meta['duration_seconds']//60} min · {meta.get('upload_date','')}",
        url=meta["url"],
        body=body_html,
        doc_kind="insights",
    )
    _render_with_playwright(html, out_path)
    return out_path


def render_briefs_pdf(md: str, out_path: Path, meta: dict):
    env = Environment(loader=FileSystemLoader(TEMPLATES))
    body_html = _md_to_html(md)
    template = env.get_template("pdf_base.html.j2")
    html = template.render(
        title=meta["title"],
        subtitle="Content Briefs — @gibran.alonzo.ecom",
        kicker=f"{meta['channel']} · {meta['duration_seconds']//60} min · {meta.get('upload_date','')}",
        url=meta["url"],
        body=body_html,
        doc_kind="briefs",
    )
    _render_with_playwright(html, out_path)
    return out_path


def _extract_section(md: str, header_pattern: str) -> str:
    """Extract a section from markdown by header (until next ## same level)."""
    lines = md.split("\n")
    out = []
    in_section = False
    section_level = None
    for line in lines:
        m = re.match(r"^(#+)\s+(.*)", line)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            if not in_section and re.search(header_pattern, text, re.IGNORECASE):
                in_section = True
                section_level = level
                continue  # skip header itself
            elif in_section and level <= section_level:
                break
        if in_section:
            out.append(line)
    return "\n".join(out).strip()


def _extract_idea_titles(briefs_md: str) -> list[dict]:
    """
    Extract idea titles from briefs_md. Returns list of {kind, num, title, why}.
    Handles formats:
      ### CARRUSEL #1 — "Title"
      ### REEL #1 — "Title"
      ### 🏆 IDEA #1 — Carrusel: "Title"
    """
    ideas = []
    lines = briefs_md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^###\s+(?:🏆\s+)?(CARRUSEL|REEL|IDEA)\s*#?(\d+)\s*[—:-]\s*(.+)$", line, re.IGNORECASE)
        if m:
            kind = m.group(1).upper()
            num = m.group(2)
            title = m.group(3).strip().strip('"').strip()
            # Look ahead for "Por qué" line to get justification
            why = ""
            for j in range(i+1, min(i+30, len(lines))):
                if re.match(r"^\*\*Por qué", lines[j]):
                    # Collect bullets until empty line or next ###
                    for k in range(j+1, min(j+10, len(lines))):
                        l = lines[k].strip()
                        if not l or l.startswith("###") or l.startswith("---"):
                            break
                        if l.startswith(("-", "*")):
                            why = l.lstrip("-* ").strip()
                            break
                    break
            ideas.append({"kind": kind, "num": num, "title": title, "why": why})
        i += 1
    return ideas


def render_recap_pdf(insights_md: str, briefs_md: str, out_path: Path, meta: dict):
    """One-pager recap: TL;DR + ideas list (titles + 1-line why)."""
    env = Environment(loader=FileSystemLoader(TEMPLATES))

    tldr = _extract_section(insights_md, r"^TL;?DR$")
    tldr_html = _md_to_html(tldr) if tldr else "<p><em>(sin TL;DR)</em></p>"

    ideas = _extract_idea_titles(briefs_md)
    carruseles = [i for i in ideas if i["kind"] == "CARRUSEL"]
    reels = [i for i in ideas if i["kind"] == "REEL"]
    generic = [i for i in ideas if i["kind"] == "IDEA"]

    def _render_idea_block(items, label):
        if not items:
            return ""
        html = f'<h3>{label}</h3><ol class="ideas-list">'
        for it in items:
            why = f' <span class="why">— {escape(it["why"])}</span>' if it["why"] else ""
            html += f'<li><strong>{escape(it["title"])}</strong>{why}</li>'
        html += '</ol>'
        return html

    if carruseles or reels:
        ideas_html = _render_idea_block(carruseles, "Carruseles") + _render_idea_block(reels, "Reels")
    else:
        ideas_html = _render_idea_block(generic, "Ideas")
    if not ideas_html:
        ideas_html = "<p><em>(sin ideas extraídas)</em></p>"

    template = env.get_template("recap.html.j2")
    html = template.render(
        title=meta["title"],
        kicker=f"{meta['channel']} · {meta['duration_seconds']//60} min · {meta.get('upload_date','')}",
        url=meta["url"],
        tldr=tldr_html,
        ideas=ideas_html,
        slug=Path(out_path).parent.name,
    )
    _render_with_playwright(html, out_path)
    return out_path
