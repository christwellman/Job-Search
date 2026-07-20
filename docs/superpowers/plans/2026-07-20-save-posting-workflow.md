# Save-Posting Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user paste a job URL in chat and have Claude save a clean, metadata-tagged posting file into `Postings/` — reading login-gated/JS sites via the user's logged-in Chrome.

**Architecture:** The workflow logic lives in a Claude Code skill (`.claude/skills/save-posting/SKILL.md`) that drives the `claude-in-chrome` browser tools to extract the posting, then pipes the extracted fields + body as JSON to a small Python writer (`save_posting.py`) that owns filename sanitizing, frontmatter rendering, and duplicate handling. Splitting the pure file-writing logic out of the prose skill is what makes it testable.

**Tech Stack:** Python 3 standard library only (`json`, `re`, `datetime`, `pathlib`, `unittest`). No new dependencies. Browser access via existing `claude-in-chrome` MCP tools.

## Global Constraints

- No new third-party dependencies — Python **standard library only** (tests use `unittest`, not pytest).
- Posting files go in `Postings/` and keep the `.txt` extension and `<Title> - <Company>.txt` naming so existing `Scanner.py` picks them up unchanged.
- Frontmatter schema is exactly these five keys, in this order: `title`, `company`, `location`, `source_url`, `date_scraped`. Missing values are written empty, never fabricated.
- `date_scraped` is an ISO date (`YYYY-MM-DD`), defaulting to today.
- Never overwrite an existing posting file without an explicit `force` flag.
- Metadata header applies to **new** postings only; do not backfill the existing 21.
- Run Python via the repo venv: `./venv/bin/python`.

---

### Task 1: `save_posting.py` — pure writer module + CLI

**Files:**
- Create: `save_posting.py`
- Test: `test_save_posting.py`

**Interfaces:**
- Consumes: nothing (leaf module).
- Produces:
  - `sanitize_filename(title: str, company: str) -> str` → `"<Title> - <Company>.txt"`, illegal chars replaced with spaces, whitespace collapsed.
  - `render_posting(meta: dict, body: str) -> str` → full file text: `---`-fenced frontmatter (the five fixed keys, in order) + blank line + trimmed body + trailing newline.
  - `run(data: dict, postings_dir: pathlib.Path) -> dict` → writes the file (unless it exists and `data["force"]` is falsy) and returns `{"status": "saved"|"exists", "path": str}`. Defaults `date_scraped` to today when absent.
  - CLI: `./venv/bin/python save_posting.py` reads one JSON object `{"meta": {...}, "body": "...", "force": bool}` from stdin and prints the `run(...)` result dict as JSON.

- [ ] **Step 1: Write the failing tests**

Create `test_save_posting.py`:

```python
import datetime
import json
import tempfile
import unittest
from pathlib import Path

import save_posting as sp


class TestSanitizeFilename(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            sp.sanitize_filename("Senior BizOps Manager", "Netflix"),
            "Senior BizOps Manager - Netflix.txt",
        )

    def test_illegal_chars_become_spaces(self):
        # slash, colon, pipe, etc. are replaced with a space, not deleted
        self.assertEqual(
            sp.sanitize_filename("Manager, Data/Analytics", "1Password"),
            "Manager, Data Analytics - 1Password.txt",
        )

    def test_whitespace_collapsed_and_trimmed(self):
        self.assertEqual(
            sp.sanitize_filename("  Lead   Analyst  ", "  Acme  "),
            "Lead Analyst - Acme.txt",
        )


class TestRenderPosting(unittest.TestCase):
    def test_full_frontmatter_and_body(self):
        meta = {
            "title": "BizOps Lead",
            "company": "OpenAI",
            "location": "Remote (US)",
            "source_url": "https://example.com/job/1",
            "date_scraped": "2026-07-20",
        }
        out = sp.render_posting(meta, "  Do great work.  ")
        expected = (
            "---\n"
            "title: BizOps Lead\n"
            "company: OpenAI\n"
            "location: Remote (US)\n"
            "source_url: https://example.com/job/1\n"
            "date_scraped: 2026-07-20\n"
            "---\n"
            "\n"
            "Do great work.\n"
        )
        self.assertEqual(out, expected)

    def test_missing_fields_are_empty_never_missing(self):
        out = sp.render_posting({"title": "X", "company": "Y"}, "body")
        self.assertIn("location: \n", out)
        self.assertIn("source_url: \n", out)
        self.assertIn("date_scraped: \n", out)


class TestRun(unittest.TestCase):
    def _data(self, **over):
        d = {
            "meta": {"title": "BizOps Lead", "company": "OpenAI"},
            "body": "body text",
            "force": False,
        }
        d.update(over)
        return d

    def test_writes_file_and_defaults_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = sp.run(self._data(), Path(tmp))
            self.assertEqual(result["status"], "saved")
            path = Path(result["path"])
            self.assertTrue(path.exists())
            text = path.read_text()
            self.assertIn(f"date_scraped: {datetime.date.today().isoformat()}\n", text)

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = sp.run(self._data(), Path(tmp))
            Path(first["path"]).write_text("ORIGINAL")
            result = sp.run(self._data(), Path(tmp))
            self.assertEqual(result["status"], "exists")
            self.assertEqual(Path(result["path"]).read_text(), "ORIGINAL")

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = sp.run(self._data(), Path(tmp))
            Path(first["path"]).write_text("ORIGINAL")
            result = sp.run(self._data(force=True), Path(tmp))
            self.assertEqual(result["status"], "saved")
            self.assertNotEqual(Path(result["path"]).read_text(), "ORIGINAL")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./venv/bin/python -m unittest test_save_posting -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'save_posting'` (or `AttributeError` once the file exists but functions don't).

- [ ] **Step 3: Write the implementation**

Create `save_posting.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./venv/bin/python -m unittest test_save_posting -v`
Expected: PASS (8 tests OK).

- [ ] **Step 5: Smoke-test the CLI end to end**

Run:
```bash
echo '{"meta":{"title":"Test Role","company":"Acme","location":"Remote","source_url":"https://x.test/1"},"body":"Hello."}' \
  | ./venv/bin/python save_posting.py
```
Expected: prints `{"status": "saved", "path": ".../Postings/Test Role - Acme.txt"}`.
Then remove the scratch file:
```bash
rm -f "Postings/Test Role - Acme.txt"
```

- [ ] **Step 6: Commit**

```bash
git add save_posting.py test_save_posting.py
git commit -m "feat: add save_posting writer module for scraped postings"
```

---

### Task 2: `save-posting` skill

**Files:**
- Create: `.claude/skills/save-posting/SKILL.md`

**Interfaces:**
- Consumes: `save_posting.py` CLI from Task 1 (`run` via stdin JSON).
- Produces: a documented, repeatable workflow (no code symbols).

- [ ] **Step 1: Write the skill file**

Create `.claude/skills/save-posting/SKILL.md`:

```markdown
---
name: save-posting
description: Use when the user pastes a job-posting URL or says "save this posting" — reads the posting from their logged-in Chrome and writes a clean, metadata-tagged file into Postings/.
---

# Save Posting

Save a job posting from a URL into `Postings/` as a frontmatter-tagged `.txt`
file that `Scanner.py` can consume. Built for LinkedIn / Workday / iCIMS /
company career pages, which are JavaScript-rendered and login-gated — so read
them through the user's already-logged-in Chrome, not an HTTP fetch.

## Trigger

- The user pastes a job URL, or
- The user says "save this posting" while a job tab is open.

## Steps

1. **Load browser tools** (if deferred): one `ToolSearch` call for
   `tabs_context_mcp, tabs_create_mcp, navigate, read_page, get_page_text`.
2. **Find or open the posting.** Call `tabs_context_mcp`. If the posting tab
   is already open, use it; otherwise open the URL in a new tab.
3. **Read the rendered page** with `get_page_text` (fall back to `read_page`).
4. **Detect a wall.** If the text is blank, a login/"sign in" page, or an
   anti-bot challenge, STOP and ask the user to log in or navigate to the
   posting in Chrome, then retry. Offer: they can paste the description text
   directly instead.
5. **Extract fields** from the rendered text:
   - `title`, `company`, `location` (use `Remote` when stated; leave empty if
     genuinely absent — never guess), and the **full job-description body**.
   - `source_url` = the posting's URL.
   - Strip boilerplate: site nav, cookie/consent banners, "Apply now" / "Save
     job" controls, related-jobs sidebars, and footers.
6. **Write the file.** Pipe JSON to the writer:

       echo '<json>' | ./venv/bin/python save_posting.py

   where `<json>` is `{"meta": {"title": ..., "company": ..., "location": ...,
   "source_url": ...}, "body": "<cleaned description>"}`. Prefer writing the
   JSON to a scratchpad file and piping that in to avoid quoting problems with
   long bodies.
7. **Handle duplicates.** If the writer returns `{"status": "exists", ...}`,
   tell the user a posting with that name already exists and ask whether to
   overwrite. Only on a yes, re-run with `"force": true` in the JSON.
8. **Confirm and stop.** Report `title / company / location / saved path`. Do
   NOT auto-run tailoring — saving is a deliberate, standalone step.

## Notes

- The writer defaults `date_scraped` to today and owns filename sanitizing —
  do not construct the path yourself.
- If one page lists multiple postings, ask which one (or use the one in focus).
- For a posting delivered as a PDF, read it if reachable; otherwise ask the
  user to paste the text.
```

- [ ] **Step 2: Verify the skill is well-formed**

Run: `./venv/bin/python -c "import pathlib,sys; t=pathlib.Path('.claude/skills/save-posting/SKILL.md').read_text(); assert t.startswith('---') and 'name: save-posting' in t and 'save_posting.py' in t; print('SKILL.md OK')"`
Expected: prints `SKILL.md OK`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/save-posting/SKILL.md
git commit -m "feat: add save-posting skill (URL -> Postings via Chrome)"
```

---

### Task 3: End-to-end verification + README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the skill (Task 2) and writer (Task 1).
- Produces: user-facing docs; a real saved posting proving the flow.

- [ ] **Step 1: Live end-to-end run**

With a real job posting open in Chrome, invoke the `save-posting` skill on its
URL. Verify the created `Postings/<Title> - <Company>.txt`:
- has frontmatter with all five keys, `date_scraped` = today, correct
  `source_url`;
- body is the job description with nav/cookie/apply boilerplate removed;
- filename is `<Title> - <Company>.txt`.

Then confirm the duplicate path: invoke it again on the same URL and verify the
writer reports `exists` and does not overwrite until confirmed.

Expected: a clean posting file on the first run; an `exists` prompt (no
overwrite) on the second. If a login wall appears, verify the skill asks you to
log in rather than saving garbage.

- [ ] **Step 2: Document the workflow in README**

Add this section to `README.md` (after the existing usage lines):

```markdown
## Saving postings

To capture a job posting, paste its URL to Claude Code (or say "save this
posting" with the tab open). Claude reads it from your logged-in Chrome —
handling LinkedIn/Workday/company pages that a plain scraper can't — and writes
`Postings/<Title> - <Company>.txt` with a metadata header:

    ---
    title: ...
    company: ...
    location: ...
    source_url: ...
    date_scraped: YYYY-MM-DD
    ---

Then run `Scanner.py` as usual to summarize and tailor.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document save-posting workflow"
```

---

## Notes for later (roadmap, not this plan)

Per the spec, these are separate future plans and are intentionally **not**
implemented here: R1 migrate `Scanner.py` to the Anthropic API + level up
tailoring (and generalize `markdown_to_pdf.py`), R2 aspiration/gap file, R3
stale-posting flagging. The frontmatter schema written above (`date_scraped`
especially) is the hook R2 and R3 will build on.
