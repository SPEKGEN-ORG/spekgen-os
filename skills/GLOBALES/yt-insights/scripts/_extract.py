"""yt-dlp wrapper + VTT cleanup."""
import re
import json
import subprocess
import sys
from pathlib import Path


def slug_from_title(title: str) -> str:
    """Convert video title to kebab-case slug."""
    s = title.lower()
    # Remove common noise
    s = re.sub(r"\bin\s+\d+\s+min(s|utes)?\b", "", s)
    # Replace non-alphanumeric with hyphens
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    # Limit length
    parts = s.split("-")
    keep = []
    total = 0
    for p in parts:
        if not p:
            continue
        if total + len(p) + 1 > 60:
            break
        keep.append(p)
        total += len(p) + 1
    return "-".join(keep) or "untitled"


def _vtt_to_clean(vtt_path: Path, srt_out: Path, txt_out: Path):
    """Convert VTT auto-subs to a clean SRT (with timestamps) and TXT."""
    vtt = vtt_path.read_text()
    lines = vtt.split("\n")
    ts_re = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d)\s-->")
    tag_re = re.compile(r"<[^>]+>")

    out = []  # (start_seconds, text)
    seen = set()
    current_ts = None
    for line in lines:
        line = line.rstrip()
        m = ts_re.match(line)
        if m:
            h, mn, s, _ms = map(int, m.groups())
            current_ts = h * 3600 + mn * 60 + s
            continue
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        txt = tag_re.sub("", line).strip()
        if not txt or txt in seen:
            continue
        seen.add(txt)
        out.append((current_ts or 0, txt))

    def fmt_ts(s):
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        return f"{h:02d}:{m:02d}:{sec:02d}"

    with open(srt_out, "w") as f:
        for ts, txt in out:
            f.write(f"[{fmt_ts(ts)}] {txt}\n")

    with open(txt_out, "w") as f:
        last_block_ts = 0
        block = []
        for ts, txt in out:
            if ts - last_block_ts > 30 and block:
                f.write(" ".join(block) + "\n\n")
                block = []
                last_block_ts = ts
            block.append(txt)
        if block:
            f.write(" ".join(block) + "\n")


def extract_transcript_and_metadata(url: str, videos_root: Path, today_iso: str, mode: str = "fail"):
    """
    Run yt-dlp, write transcript files + metadata.json.
    Returns (folder_path, metadata_dict).

    mode:
      "fail"      → if folder exists, exit 3 with FOLDER_EXISTS message (default)
      "overwrite" → reuse the same folder, sobrescribe transcript/metadata
      "version"   → create folder with -v2, -v3, etc suffix
    """
    # First, get title to build slug
    print(f"[yt-dlp] Fetching metadata...", file=sys.stderr)
    res = subprocess.run(
        ["yt-dlp", "--skip-download", "--print",
         "%(title)s|||%(channel)s|||%(duration)s|||%(upload_date)s|||%(view_count)s|||%(webpage_url)s",
         url],
        capture_output=True, text=True, check=True,
    )
    title, channel, duration, upload_date, view_count, webpage_url = res.stdout.strip().split("|||")

    slug = slug_from_title(title)
    base_folder = videos_root / f"{today_iso}_{slug}"

    if base_folder.exists():
        if mode == "fail":
            print(f"FOLDER_EXISTS: {base_folder}", file=sys.stderr)
            sys.exit(3)
        elif mode == "version":
            n = 2
            while (videos_root / f"{today_iso}_{slug}-v{n}").exists():
                n += 1
            folder = videos_root / f"{today_iso}_{slug}-v{n}"
        else:  # overwrite
            folder = base_folder
    else:
        folder = base_folder
    folder.mkdir(parents=True, exist_ok=True)

    # Now download subs + info json
    print(f"[yt-dlp] Downloading auto-subs + info json -> {folder}", file=sys.stderr)
    cmd = [
        "yt-dlp",
        "--write-auto-sub", "--write-sub",
        "--sub-lang", "en,en-US,es",
        "--skip-download",
        "--write-info-json",
        "--convert-subs", "srt",
        "--output", "raw.%(ext)s",
        "--paths", str(folder),
        url,
    ]
    subprocess.run(cmd, capture_output=True, text=True)

    # Find any subs file
    vtt_files = sorted(folder.glob("raw.*.vtt"))
    info_files = sorted(folder.glob("raw.info.json"))

    if not vtt_files:
        # No subs available
        print("NEED_MANUAL_TRANSCRIPT", file=sys.stderr)
        sys.exit(2)

    # Prefer en, then en-US, then any
    chosen = None
    for pref in ["raw.en.vtt", "raw.en-US.vtt"]:
        for v in vtt_files:
            if v.name == pref:
                chosen = v
                break
        if chosen:
            break
    if not chosen:
        chosen = vtt_files[0]

    _vtt_to_clean(chosen, folder / "transcript.srt", folder / "transcript.txt")

    # Cleanup raw VTT files (we have the cleaned transcript now)
    for v in vtt_files:
        try:
            v.unlink()
        except Exception:
            pass

    # Parse info JSON for chapters
    chapters = []
    if info_files:
        info = json.loads(info_files[0].read_text())
        for ch in info.get("chapters") or []:
            chapters.append({
                "start_seconds": int(ch["start_time"]),
                "end_seconds": int(ch.get("end_time", 0)),
                "title": ch["title"],
            })

    # Format upload date YYYY-MM-DD
    if len(upload_date) == 8:
        upload_date_fmt = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    else:
        upload_date_fmt = upload_date

    meta = {
        "url": webpage_url,
        "title": title,
        "channel": channel,
        "duration_seconds": int(duration) if duration.isdigit() else None,
        "upload_date": upload_date_fmt,
        "view_count": int(view_count) if view_count.isdigit() else None,
        "language": chosen.name.split(".")[1],
        "extracted_at": today_iso,
        "extracted_by": "yt-insights skill v1.0",
        "chapters": chapters,
    }
    (folder / "metadata.json").write_text(json.dumps(meta, indent=2))

    return folder, meta
