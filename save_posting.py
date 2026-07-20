"""Write a scraped job posting into Postings/ as a frontmatter-tagged .txt file.

Used by the `save-posting` Claude Code skill: the skill extracts the posting
via the browser, then pipes {"meta": {...}, "body": "...", "force": bool} as
JSON on stdin to this script.
"""
import datetime
import json
import re
import sys
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


def run(data: dict, postings_dir: Path = POSTINGS_DIR) -> dict:
    meta = dict(data.get("meta", {}))
    body = data.get("body", "")
    force = bool(data.get("force", False))
    meta.setdefault("date_scraped", datetime.date.today().isoformat())

    postings_dir = Path(postings_dir)
    path = postings_dir / sanitize_filename(
        meta.get("title", ""), meta.get("company", "")
    )

    if path.exists() and not force:
        return {"status": "exists", "path": str(path)}

    postings_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(render_posting(meta, body), encoding="utf-8")
    return {"status": "saved", "path": str(path)}


def main() -> None:
    data = json.load(sys.stdin)
    print(json.dumps(run(data)))


if __name__ == "__main__":
    main()
