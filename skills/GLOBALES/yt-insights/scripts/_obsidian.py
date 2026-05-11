"""Generate Obsidian linkable note from template."""
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
TEMPLATES = ROOT.parent / "templates"

# Clientes/topics that auto-link
KNOWN_BACKLINKS = [
    "HEALTHY CHUCHOS", "GREENRAY", "LO FITNESS", "METAGREEN",
    "GAE", "@gibran.alonzo.ecom", "SPEKGEN",
    "Claude Code", "Make", "Shopify", "Meta Ads", "GHL",
    "factory-batch", "publish-prospect", "kill-prospect",
]


def _detect_backlinks(text: str) -> list[str]:
    """Find which known terms appear in text and should become Obsidian backlinks."""
    found = []
    text_upper = text.upper()
    for term in KNOWN_BACKLINKS:
        if term.upper() in text_upper and term not in found:
            found.append(term)
    return found


def _extract_section(md: str, header_pattern: str) -> str:
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
                continue
            elif in_section and level <= section_level:
                break
        if in_section:
            out.append(line)
    return "\n".join(out).strip()


def write_obsidian_note(obsidian_dir: Path, folder: Path, meta: dict, insights_md: str, briefs_md: str):
    obsidian_dir.mkdir(parents=True, exist_ok=True)

    slug = folder.name.split("_", 1)[1] if "_" in folder.name else folder.name
    tldr = _extract_section(insights_md, r"^TL;?DR$")
    actions = _extract_section(insights_md, r"^Action items")
    backlinks = _detect_backlinks(insights_md + "\n" + briefs_md)

    env = Environment(loader=FileSystemLoader(TEMPLATES))
    template = env.get_template("obsidian_note.md.j2")
    note = template.render(
        title=meta["title"],
        channel=meta["channel"],
        url=meta["url"],
        duration_min=(meta.get("duration_seconds") or 0) // 60,
        upload_date=meta.get("upload_date", ""),
        extracted_at=meta.get("extracted_at", ""),
        tldr=tldr,
        actions=actions,
        insights_path=str(folder / "insights.pdf"),
        briefs_path=str(folder / "content_briefs.pdf"),
        recap_path=str(folder / "_RECAP.pdf"),
        folder_path=str(folder),
        backlinks=backlinks,
    )
    out_path = obsidian_dir / f"{slug}.md"
    out_path.write_text(note)
    return out_path
