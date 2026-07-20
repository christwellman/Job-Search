"""Shared job-posting file format: parse, render, and filename helpers."""
import datetime
import re
from pathlib import Path

POSTINGS_DIR = Path(__file__).resolve().parent / "Postings"

# Frontmatter keys, in fixed output order.
FIELDS = ("title", "company", "location", "source_url", "date_scraped")

# Characters not allowed in filenames on common filesystems.
_ILLEGAL = re.compile(r'[<>:"/\\|?*]')
_WHITESPACE = re.compile(r"\s+")


def sanitize_filename(title: str, company: str) -> str:
    base = f"{title} - {company}"
    base = _ILLEGAL.sub(" ", base)
    base = _WHITESPACE.sub(" ", base).strip()
    return f"{base}.txt"


def render_posting(meta: dict, body: str) -> str:
    lines = ["---"]
    for key in FIELDS:
        lines.append(f"{key}: {meta.get(key) or ''}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + "\n" + body.strip() + "\n"


def parse_posting(text: str) -> tuple[dict, str]:
    """Split a posting into (metadata, body).

    Reads a leading `---`-fenced block of `key: value` lines. Text without a
    well-formed header returns ({}, text.strip())."""
    text = text or ""
    if not text.lstrip().startswith("---"):
        return {}, text.strip()

    lines = text.lstrip("\n").split("\n")  # lines[0] == "---"
    meta: dict = {}
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
        key, sep, val = lines[idx].partition(":")
        if sep:
            meta[key.strip()] = val.strip()

    if end is None:  # no closing fence — not a real header
        return {}, text.strip()

    body = "\n".join(lines[end + 1:]).strip()
    return meta, body


def now_date() -> str:
    return datetime.date.today().isoformat()
