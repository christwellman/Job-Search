# R1 — Anthropic Scanner + Tailoring + PDF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `Scanner.py` off OpenAI to Anthropic (Haiku summaries, Sonnet tailoring), make it frontmatter-aware and higher-quality, generalize the PDF converter, and rebuild the broken venv.

**Architecture:** A new `postings.py` owns the posting file format (parse + render + filename); `save_posting.py` and `Scanner.py` both use it. `Scanner.py` calls the Anthropic SDK with a lazily-constructed shared client across the existing thread pool. `markdown_to_pdf.py` becomes a CLI. A fresh venv installs everything from `requirements.txt`.

**Tech Stack:** Python 3.11 (Homebrew). Third-party: `anthropic`, `python-dotenv`, `markdown`, `weasyprint`, `tqdm`. Tests: stdlib `unittest`.

## Global Constraints

- Models: summaries use `claude-haiku-4-5`; tailoring uses `claude-sonnet-5`. Use these exact IDs.
- Never fabricate resume content — the tailoring prompt must forbid inventing experience, skills, employers, titles, or dates.
- Posting frontmatter schema is the five keys from `#3`: `title`, `company`, `location`, `source_url`, `date_scraped`. Header-less legacy postings must still process.
- No API key is ever entered by the assistant — `ANTHROPIC_API_KEY` is set by the user in `.env`; module import must NOT require it (construct the client lazily).
- Run the rebuilt venv's interpreter as `./venv/bin/python`. Task 1 predates the rebuild and runs under system `python3` (stdlib only).
- `Customized Resumes/`, `venv/`, `.env` stay git-ignored (already are).

---

### Task 1: `postings.py` — shared posting-format module

**Files:**
- Create: `postings.py`
- Modify: `save_posting.py`
- Test: `test_postings.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `sanitize_filename(title, company) -> str` (moved verbatim from `save_posting.py`)
  - `render_posting(meta, body) -> str` (moved verbatim)
  - `parse_posting(text) -> (dict, str)` — splits a `---`-fenced header + body; header-less text returns `({}, text.strip())`
  - `POSTINGS_DIR`, `FIELDS` constants
- `save_posting.py` re-exports `sanitize_filename` / `render_posting` by importing them, so `test_save_posting.py` keeps passing unchanged.

- [ ] **Step 1: Write the failing tests**

Create `test_postings.py`:

```python
import unittest

import postings as p


class TestParsePosting(unittest.TestCase):
    def test_roundtrip_full_header(self):
        meta = {
            "title": "BizOps Lead",
            "company": "OpenAI",
            "location": "Remote",
            "source_url": "https://example.com/job/1",
            "date_scraped": "2026-07-20",
        }
        text = p.render_posting(meta, "Body line one.\nBody line two.")
        got_meta, got_body = p.parse_posting(text)
        self.assertEqual(got_meta["title"], "BizOps Lead")
        self.assertEqual(got_meta["company"], "OpenAI")
        self.assertEqual(got_meta["location"], "Remote")
        self.assertEqual(got_meta["source_url"], "https://example.com/job/1")
        self.assertEqual(got_meta["date_scraped"], "2026-07-20")
        self.assertEqual(got_body, "Body line one.\nBody line two.")

    def test_no_header_returns_whole_body(self):
        text = "Just a plain posting.\nNo frontmatter here."
        meta, body = p.parse_posting(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, "Just a plain posting.\nNo frontmatter here.")

    def test_partial_header(self):
        text = "---\ntitle: Analyst\ncompany: Acme\n---\n\nDesc."
        meta, body = p.parse_posting(text)
        self.assertEqual(meta, {"title": "Analyst", "company": "Acme"})
        self.assertEqual(body, "Desc.")

    def test_empty_value_parses_as_empty_string(self):
        text = "---\ntitle: X\nlocation:\n---\n\nB"
        meta, body = p.parse_posting(text)
        self.assertEqual(meta["title"], "X")
        self.assertEqual(meta["location"], "")

    def test_unclosed_header_treated_as_body(self):
        text = "---\ntitle: X\nno closing fence"
        meta, body = p.parse_posting(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, text.strip())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_postings -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'postings'`.

- [ ] **Step 3: Create `postings.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest test_postings -v`
Expected: PASS (5 tests OK).

- [ ] **Step 5: Update `save_posting.py` to import from `postings.py`**

Replace the top of `save_posting.py` — delete its `POSTINGS_DIR`, `FIELDS`, `_ILLEGAL`, `_WHITESPACE`, `sanitize_filename`, and `render_posting` definitions, and import them instead. The file should become:

```python
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
```

- [ ] **Step 6: Run both test suites to verify nothing broke**

Run: `python3 -m unittest test_postings test_save_posting -v`
Expected: PASS (13 tests OK — 5 postings + 8 save_posting; the moved functions are still reachable as `save_posting.sanitize_filename` via the import).

- [ ] **Step 7: Commit**

```bash
git add postings.py test_postings.py save_posting.py
git commit -m "refactor: extract postings.py with parse/render/sanitize"
```

---

### Task 2: `requirements.txt` + rebuild the venv

**Files:**
- Create: `requirements.txt`

**Interfaces:**
- Consumes: nothing.
- Produces: a working `./venv/bin/python` with `anthropic`, `markdown`, `weasyprint`, `tqdm`, `dotenv` importable. Tasks 3–5 depend on this.

- [ ] **Step 1: Create `requirements.txt`**

```
anthropic
python-dotenv
markdown
weasyprint
tqdm
```

- [ ] **Step 2: Rebuild the venv**

Run:
```bash
rm -rf venv
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```
Expected: installs complete without error.

- [ ] **Step 3: Verify the key packages import**

Run: `./venv/bin/python -c "import anthropic, markdown, weasyprint, dotenv, tqdm; print('deps OK')"`
Expected: prints `deps OK`.
If WeasyPrint raises `OSError`/`cannot load library` about `pango`/`cairo`/`gobject`, run `brew install pango` and retry this step. Do not proceed until it prints `deps OK`.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "build: add requirements.txt (venv/ stays git-ignored)"
```

---

### Task 3: Generalize `markdown_to_pdf.py`

**Files:**
- Modify: `markdown_to_pdf.py`
- Test: `test_markdown_to_pdf.py`

**Interfaces:**
- Consumes: `markdown`, `weasyprint`, `Resume.css` (Task 2).
- Produces:
  - `build_html(md_text: str, css_href: str) -> str` (pure, testable)
  - `convert(input_path: Path, output_path: Path) -> Path`
  - CLI: `python markdown_to_pdf.py <input.md> [output.pdf]`

- [ ] **Step 1: Write the failing test**

Create `test_markdown_to_pdf.py`:

```python
import unittest

import markdown_to_pdf as mp


class TestBuildHtml(unittest.TestCase):
    def test_renders_markdown_and_links_css(self):
        html = mp.build_html("# Hi\n\nsome text", "file:///x/Resume.css")
        self.assertTrue(html.startswith("<html>"))
        self.assertIn("<h1>Hi</h1>", html)
        self.assertIn('href="file:///x/Resume.css"', html)
        self.assertIn("some text", html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m unittest test_markdown_to_pdf -v`
Expected: FAIL — `AttributeError: module 'markdown_to_pdf' has no attribute 'build_html'` (the current file runs conversion at import; the new file exposes `build_html`).

- [ ] **Step 3: Rewrite `markdown_to_pdf.py`**

```python
"""Convert a Markdown resume to PDF: python markdown_to_pdf.py <input.md> [out.pdf]."""
import argparse
import tempfile
from pathlib import Path

import markdown
from weasyprint import HTML

SCRIPT_DIR = Path(__file__).resolve().parent
CSS_PATH = SCRIPT_DIR / "Resume.css"


def build_html(md_text: str, css_href: str) -> str:
    body = markdown.markdown(md_text)
    return (
        f'<html><head><link rel="stylesheet" type="text/css" href="{css_href}">'
        f"</head><body>{body}</body></html>"
    )


def convert(input_path: Path, output_path: Path) -> Path:
    md_text = input_path.read_text(encoding="utf-8")
    html = build_html(md_text, CSS_PATH.as_uri())
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(html)
        tmp_path = tmp.name
    try:
        HTML(tmp_path).write_pdf(str(output_path))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Markdown resume to PDF.")
    parser.add_argument("input", help="Path to the Markdown resume")
    parser.add_argument("output", nargs="?", help="Output PDF (defaults to <input>.pdf)")
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".pdf")
    convert(input_path, output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./venv/bin/python -m unittest test_markdown_to_pdf -v`
Expected: PASS.

- [ ] **Step 5: Live render smoke test**

Run (pick any existing customized resume, or `Resume.md`):
```bash
./venv/bin/python markdown_to_pdf.py "Resume.md" "/private/tmp/claude-501/-Users-christwellman-Projects-Job-Search/a470a4ad-93ca-4a8b-b3ce-baf453b596be/scratchpad/r1_test.pdf"
test -s "/private/tmp/claude-501/-Users-christwellman-Projects-Job-Search/a470a4ad-93ca-4a8b-b3ce-baf453b596be/scratchpad/r1_test.pdf" && echo "PDF OK"
```
Expected: prints `Wrote ...` then `PDF OK`. Confirm no `resume.html` was created in the repo root: `test ! -e resume.html && echo "no stray html"`.

- [ ] **Step 6: Commit**

```bash
git add markdown_to_pdf.py test_markdown_to_pdf.py
git commit -m "feat: generalize markdown_to_pdf.py into a CLI"
```

---

### Task 4: Rewrite `Scanner.py` for Anthropic

**Files:**
- Modify: `Scanner.py`
- Delete: `listModels.py`

**Interfaces:**
- Consumes: `postings.parse_posting` (Task 1); `anthropic`, `dotenv`, `tqdm` (Task 2); `Reference/Action words`, `Reference/Resume Statements.md`.
- Produces: a CLI that reads `Postings/*.txt`, writes `Customized Resumes/summary_<file>` and `Customized Resumes/Chris Twellman - <file>.md`. Importable without an API key (client is lazy).

- [ ] **Step 1: Rewrite `Scanner.py`**

```python
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from tqdm import tqdm

from postings import parse_posting

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")

SUMMARY_MODEL = "claude-haiku-4-5"
TAILOR_MODEL = "claude-sonnet-5"
REFERENCE_DIR = SCRIPT_DIR / "Reference"

_client = None


def get_client() -> anthropic.Anthropic:
    """Construct the Anthropic client lazily so importing this module needs no key."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _read_reference(name: str) -> str:
    try:
        return (REFERENCE_DIR / name).read_text(encoding="utf-8")
    except OSError:
        logging.warning(f"Reference file not found: {name}")
        return ""


ACTION_WORDS = _read_reference("Action words")
RESUME_STATEMENTS = _read_reference("Resume Statements.md")


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def _posting_text(meta: dict, body: str) -> str:
    if not meta:
        return body
    header = "\n".join(f"{k}: {v}" for k, v in meta.items() if v)
    return f"{header}\n\n{body}"


def summarize_job_posting(meta: dict, body: str):
    try:
        response = get_client().messages.create(
            model=SUMMARY_MODEL,
            max_tokens=1024,
            system="You are a career placement specialist who finds great opportunities for skilled candidates.",
            messages=[{
                "role": "user",
                "content": (
                    "Summarize this job posting as a concise, scannable bullet list. Include: "
                    "the exact job title; the company; the location (or 'Remote'); 3-5 key "
                    "responsibilities; the required qualifications and experience; and 1-2 "
                    "compelling aspects of the role. Focus on the most relevant details.\n\n"
                    f"{_posting_text(meta, body)}"
                ),
            }],
        )
        return _text(response)
    except Exception as e:
        logging.error(f"Error summarizing job posting: {e}")
        return None


def tailor_resume(resume: str, meta: dict, body: str):
    try:
        response = get_client().messages.create(
            model=TAILOR_MODEL,
            max_tokens=8000,
            system=(
                "You are an expert resume writer and ATS specialist. You rewrite resumes to "
                "match a target job posting while staying strictly truthful."
            ),
            messages=[{
                "role": "user",
                "content": (
                    "Rewrite my resume to target the job posting below.\n\n"
                    "Rules:\n"
                    "- Position my experience as a solution to the posting's needs.\n"
                    "- Reuse the posting's exact keywords, terms, and phrasing where they honestly apply.\n"
                    "- Keep it concise, active voice, and quantify impact where the original supports it.\n"
                    "- Never fabricate experience, skills, employers, titles, or dates. Only reframe what is in my resume.\n"
                    "- Output the full tailored resume in Markdown.\n"
                    "- End with a section '## ATS Keyword Coverage' listing the posting's key terms "
                    "and, for each, whether it is now reflected in the resume (yes / partial / missing).\n\n"
                    "You may draw phrasing from these references, but do not copy any claim my resume "
                    "does not support:\n"
                    f"<action_words>\n{ACTION_WORDS}\n</action_words>\n"
                    f"<resume_statements>\n{RESUME_STATEMENTS}\n</resume_statements>\n\n"
                    f"<resume>\n{resume}\n</resume>\n\n"
                    f"<job_posting>\n{_posting_text(meta, body)}\n</job_posting>"
                ),
            }],
        )
        return _text(response)
    except Exception as e:
        logging.error(f"Error tailoring resume: {e}")
        return None


def process_job_posting(filename, input_folder, output_folder, resume_content):
    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, f"summary_{filename}")
    tailored_resume_path = os.path.join(
        output_folder, f"Chris Twellman - {filename.replace('.txt', '.md')}"
    )
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            raw = f.read()
        if not raw.strip():
            logging.warning(f"Job posting content is empty for file: {filename}")
            return
        meta, body = parse_posting(raw)

        summary = summarize_job_posting(meta, body)
        if not summary:
            logging.warning(f"Skipped (summary failed): {filename}")
            return
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        logging.info(f"Processed: {filename}")

        tailored = tailor_resume(resume_content, meta, body)
        if tailored:
            with open(tailored_resume_path, "w", encoding="utf-8") as f:
                f.write(tailored)
            logging.info(f"Tailored resume created for: {filename}")
        else:
            logging.warning(f"Skipped (tailoring failed): {filename}")
    except Exception as e:
        logging.error(f"Error processing file {filename}: {e}")


def process_job_postings(input_folder, output_folder, resume_path):
    if not os.getenv("ANTHROPIC_API_KEY"):
        logging.error("Missing environment variable: ANTHROPIC_API_KEY (add it to .env)")
        raise SystemExit(1)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    processed = set(f[8:] for f in os.listdir(output_folder) if f.startswith("summary_"))
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_content = f.read()
    if not resume_content.strip():
        logging.error("Resume content is empty.")
        return

    files_to_process = [
        fn for fn in os.listdir(input_folder)
        if fn.endswith(".txt") and fn not in processed
    ]
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(process_job_posting, fn, input_folder, output_folder, resume_content)
            for fn in files_to_process
        ]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Processing job postings"):
            pass


if __name__ == "__main__":
    process_job_postings("Postings", "Customized Resumes", str(SCRIPT_DIR / "Resume.md"))
```

- [ ] **Step 2: Delete the OpenAI helper**

Run: `git rm listModels.py`
Expected: `rm 'listModels.py'`.

- [ ] **Step 3: Verify the module imports with no API key**

Run: `env -u ANTHROPIC_API_KEY ./venv/bin/python -c "import Scanner; print('import OK')"`
Expected: prints `import OK` (no key required at import — the client is lazy). If it errors about an API key, the client is being constructed at import; fix `get_client` usage.

- [ ] **Step 4: Commit**

```bash
git add Scanner.py
git rm --cached listModels.py 2>/dev/null; true
git commit -m "feat: migrate Scanner.py to Anthropic (Haiku summary, Sonnet tailoring)"
```

---

### Task 5: Live end-to-end run + README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: everything above; `ANTHROPIC_API_KEY` in `.env` (user-provided).
- Produces: verified real output; updated docs.

- [ ] **Step 1: Confirm the API key is present**

Run: `grep -q '^ANTHROPIC_API_KEY=' .env && echo "key present" || echo "MISSING KEY"`
Expected: `key present`. If `MISSING KEY`, stop and ask the user to add `ANTHROPIC_API_KEY=...` to `.env` before continuing — do not proceed.

- [ ] **Step 2: Run the Scanner live**

Run: `./venv/bin/python Scanner.py`
Expected: a tqdm progress bar and `INFO` lines; it processes any postings in `Postings/` not already summarized (including `Data Analyst - GitHub.txt` from `#3`).

- [ ] **Step 3: Verify the output**

Run:
```bash
ls "Customized Resumes/" | grep -i "GitHub"
echo "--- tailored tail ---"
tail -30 "Customized Resumes/Chris Twellman - Data Analyst - GitHub.md"
```
Expected: both `summary_Data Analyst - GitHub.txt` and `Chris Twellman - Data Analyst - GitHub.md` exist; the tailored file ends with an `## ATS Keyword Coverage` section; the resume body contains no raw `---` frontmatter leakage (the header was parsed, not fed verbatim).

- [ ] **Step 4: Confirm a legacy (header-less) posting still processes**

Verify at least one older `Postings/*.txt` without frontmatter also produced a `summary_...` and tailored file in this run (or add one and re-run). Expected: it processes normally — `parse_posting` returned `({}, body)`.

- [ ] **Step 5: Update `README.md`**

Replace the body of `README.md` with:

```markdown
# Job-Search

Tools to tailor a resume to specific job postings using Claude.

## Setup

    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt

Add your Anthropic key to `.env`:

    ANTHROPIC_API_KEY=sk-ant-...

## Saving postings

Paste a job URL to Claude Code (or say "save this posting" with the tab open).
Claude reads it from your logged-in Chrome and writes
`Postings/<Title> - <Company>.txt` with a metadata header (title, company,
location, source_url, date_scraped).

## Tailoring

Put your resume in `Resume.md`, then:

    ./venv/bin/python Scanner.py

For each posting in `Postings/`, this writes a summary and a tailored resume
(with an ATS keyword-coverage checklist) to `Customized Resumes/`. Summaries use
Claude Haiku; tailoring uses Claude Sonnet.

## PDF

    ./venv/bin/python markdown_to_pdf.py "Customized Resumes/<file>.md"

Writes a PDF beside the source file, styled with `Resume.css`.
```

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: update README for Anthropic workflow"
```

---

## Notes for later (roadmap, not this plan)

R2 (Aspiration/gap file) aggregates the `## ATS Keyword Coverage` sections produced here. R3 (stale-posting flagging) uses `date_scraped`. Both remain separate future plans.
