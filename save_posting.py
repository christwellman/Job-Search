"""Write a scraped job posting into Postings/ as a frontmatter-tagged .txt file.

Used by the `save-posting` Claude Code skill: the skill extracts the posting
via the browser, then pipes {"meta": {...}, "body": "...", "force": bool} as
JSON on stdin to this script.
"""
import json
import sys
from pathlib import Path

from postings import POSTINGS_DIR, now_date, render_posting, sanitize_filename


def run(data: dict, postings_dir: Path = POSTINGS_DIR) -> dict:
    meta = dict(data.get("meta", {}))
    body = data.get("body", "")
    force = bool(data.get("force", False))
    meta.setdefault("date_scraped", now_date())

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
