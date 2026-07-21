# R2 — Aspiration / Gap File Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `aspirations.py` — mines the `## ATS Keyword Coverage` tables in tailored resumes for `missing`/`partial` gaps and asks Claude Haiku to cluster, categorize, and rank them into `Aspiration.md`.

**Architecture:** Pure stdlib parsers (`parse_coverage`, `collect_gaps`) gather gap terms; one lazily-constructed Anthropic client runs a single Haiku synthesis call; `main()` wires them and writes `Aspiration.md`. Parsers are unit-tested; the synthesis is verified live.

**Tech Stack:** Python 3.11. Third-party: `anthropic`, `python-dotenv` (already installed in the venv). Tests: stdlib `unittest`, run with `./venv/bin/python`.

## Global Constraints

- Synthesis model is `claude-haiku-4-5`.
- Gaps = table rows whose Coverage cell starts with `partial` or `missing` (case-insensitive); `yes`, the header row, and the `---` separator are excluded.
- `Aspiration.md` is regenerated (overwritten) each run and written to the repo root; it is git-ignored.
- No API key entered by the assistant — `ANTHROPIC_API_KEY` comes from `.env`; module import must not require it (lazy client).
- If no resume has a coverage section, print a message, make no API call, and write no file.
- Run Python as `./venv/bin/python`.

---

### Task 1: `aspirations.py` — parsers, synthesis, CLI

**Files:**
- Create: `aspirations.py`
- Test: `test_aspirations.py`

**Interfaces:**
- Consumes: `Customized Resumes/Chris Twellman - *.md`; `anthropic`, `dotenv`.
- Produces:
  - `parse_coverage(md_text) -> list[tuple[str, str]]` — `(keyword, cls)` for `partial`/`missing` rows only
  - `collect_gaps(resumes_dir) -> list[dict]` — `{"keyword", "cls", "source"}`, `source` = job name (prefix stripped)
  - `synthesize(gaps) -> str` — Haiku call, returns Markdown
  - CLI `python aspirations.py` — writes `Aspiration.md`

- [ ] **Step 1: Write the failing tests**

Create `test_aspirations.py`:

```python
import tempfile
import unittest
from pathlib import Path

import aspirations as a

SAMPLE = """# Resume

Some content.

## ATS Keyword Coverage

| Keyword / Term | Coverage |
|---|---|
| SQL | yes |
| Power BI | missing |
| Data storytelling | yes (examples) |
| Consulting | missing (no top-firm experience) |
| Mentoring | partial (implied, not explicit) |

## Some Other Section

| x | y |
"""


class TestParseCoverage(unittest.TestCase):
    def test_returns_only_missing_and_partial(self):
        got = a.parse_coverage(SAMPLE)
        self.assertEqual(got, [
            ("Power BI", "missing"),
            ("Consulting", "missing"),
            ("Mentoring", "partial"),
        ])

    def test_no_section_returns_empty(self):
        self.assertEqual(a.parse_coverage("# Resume\n\nno coverage table here"), [])

    def test_header_variant_and_stops_at_next_heading(self):
        text = (
            "## ATS Keyword Coverage\n"
            "| Keyword/Term | Coverage |\n"
            "|---|---|\n"
            "| Alteryx | missing |\n"
            "## Next\n"
            "| Leaked | missing |\n"
        )
        self.assertEqual(a.parse_coverage(text), [("Alteryx", "missing")])


class TestCollectGaps(unittest.TestCase):
    def test_collects_strips_prefix_and_skips_sectionless(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "Chris Twellman - Data Analyst - GitHub.md").write_text(SAMPLE)
            (d / "Chris Twellman - Old Format - Legacy.md").write_text("# Resume\n\nno table\n")
            gaps = a.collect_gaps(d)
            self.assertEqual(len(gaps), 3)
            self.assertTrue(all(g["source"] == "Data Analyst - GitHub" for g in gaps))
            self.assertEqual(
                {g["keyword"] for g in gaps}, {"Power BI", "Consulting", "Mentoring"}
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./venv/bin/python -m unittest test_aspirations -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aspirations'`.

- [ ] **Step 3: Create `aspirations.py`**

```python
"""Build Aspiration.md from the ATS Keyword Coverage tables in tailored resumes.

Reads every `Customized Resumes/Chris Twellman - *.md`, collects the skills, tools,
and certifications marked `missing` or `partial`, and asks Claude to cluster,
categorize, and rank them into an aspiration/gap plan.

Usage:
    python aspirations.py
"""
import logging
import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")

RESUMES_DIR = SCRIPT_DIR / "Customized Resumes"
OUTPUT_PATH = SCRIPT_DIR / "Aspiration.md"
SYNTH_MODEL = "claude-haiku-4-5"
RESUME_PREFIX = "Chris Twellman - "

_COVERAGE_RE = re.compile(r"^\s*(yes|partial|missing)\b", re.I)
_client = None


def get_client() -> anthropic.Anthropic:
    """Construct the Anthropic client lazily so importing this module needs no key."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def parse_coverage(md_text: str) -> list[tuple[str, str]]:
    lines = md_text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("## ats keyword coverage"):
            start = i
            break
    if start is None:
        return []

    results = []
    for ln in lines[start + 1:]:
        s = ln.strip()
        if s.startswith("## "):  # next section
            break
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        keyword, coverage = cells[0], cells[1]
        m = _COVERAGE_RE.match(coverage)
        if not m:  # skips the header ("Coverage") and separator ("---") rows
            continue
        cls = m.group(1).lower()
        if cls in ("partial", "missing"):
            results.append((keyword, cls))
    return results


def collect_gaps(resumes_dir: Path) -> list[dict]:
    gaps = []
    for path in sorted(resumes_dir.glob("Chris Twellman - *.md")):
        job = path.stem
        if job.startswith(RESUME_PREFIX):
            job = job[len(RESUME_PREFIX):]
        for keyword, cls in parse_coverage(path.read_text(encoding="utf-8", errors="ignore")):
            gaps.append({"keyword": keyword, "cls": cls, "source": job})
    return gaps


def synthesize(gaps: list[dict]) -> str:
    gap_block = "\n".join(
        f"[{g['cls']}] {g['keyword']}  (from: {g['source']})" for g in gaps
    )
    response = get_client().messages.create(
        model=SYNTH_MODEL,
        max_tokens=2000,
        system=(
            "You are a career development advisor. You turn a raw list of resume gaps "
            "into a clear, prioritized development plan."
        ),
        messages=[{
            "role": "user",
            "content": (
                "Below is a list of skills, tools, certifications, and requirements that "
                "recurred across job postings I pursued, each marked 'missing' (I lack it) "
                "or 'partial' (I have it but it reads weak), with the job it came from.\n\n"
                "Produce a Markdown aspiration/gap plan:\n"
                "- Cluster synonymous or closely-related items into a single named gap.\n"
                "- Group clusters under exactly these three '## ' sections: "
                "'Certifications & Education', 'Tools & Technologies', 'Skills & Capabilities'.\n"
                "- Within each section, rank clusters by how many distinct jobs they appear in "
                "(most-recurring first) and show that count.\n"
                "- Tag each cluster 'Acquire' (mostly missing) or 'Strengthen' (mostly partial).\n"
                "- Start with a one-line intro. Output only the Markdown, no preamble.\n\n"
                f"<gaps>\n{gap_block}\n</gaps>"
            ),
        }],
    )
    return "".join(b.text for b in response.content if b.type == "text")


def main() -> None:
    gaps = collect_gaps(RESUMES_DIR)
    if not gaps:
        print(
            "No ATS Keyword Coverage sections found in Customized Resumes/. "
            "Run Scanner.py on some postings first."
        )
        return
    if not os.getenv("ANTHROPIC_API_KEY"):
        logging.error("Missing environment variable: ANTHROPIC_API_KEY (add it to .env)")
        raise SystemExit(1)

    try:
        markdown = synthesize(gaps)
    except Exception as e:
        logging.error(f"Error synthesizing aspiration file: {e}")
        raise SystemExit(1)

    OUTPUT_PATH.write_text(markdown.strip() + "\n", encoding="utf-8")
    sources = {g["source"] for g in gaps}
    print(f"{len(gaps)} gap mentions across {len(sources)} postings -> {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./venv/bin/python -m unittest test_aspirations -v`
Expected: PASS (4 tests OK).

- [ ] **Step 5: Verify the module imports with no API key**

Run: `env -u ANTHROPIC_API_KEY ./venv/bin/python -c "import aspirations; print('import OK')"`
Expected: prints `import OK` (lazy client — no key needed to import).

- [ ] **Step 6: Commit**

```bash
git add aspirations.py test_aspirations.py
git commit -m "feat: add aspirations.py to build Aspiration.md from coverage gaps"
```

---

### Task 2: `.gitignore` + README

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`

**Interfaces:**
- Consumes: `aspirations.py` (Task 1).
- Produces: config + docs.

- [ ] **Step 1: Ignore the generated file**

Add a line to `.gitignore` (in the `# Specific Files` block, near the other generated artifacts):

```
Aspiration.md
```

- [ ] **Step 2: Add the README section**

Append to `README.md` (after the Housekeeping section):

```markdown
## Aspiration file

Build a running list of the skills, tools, certifications, and education you
don't yet fully have — mined from the "ATS Keyword Coverage" tables in your
tailored resumes:

    ./venv/bin/python aspirations.py

This reads every tailored resume in `Customized Resumes/`, collects the terms
marked `missing` or `partial`, and asks Claude to cluster, categorize
(Certifications & Education / Tools & Technologies / Skills & Capabilities), and
rank them by how often they recur — writing `Aspiration.md`. Regenerated each run.
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore README.md
git commit -m "docs: ignore Aspiration.md and document aspirations.py"
```

---

### Task 3: Live run verification

**Files:** none (verification only; writes the real `Aspiration.md`).

**Interfaces:**
- Consumes: `aspirations.py`, the real `Customized Resumes/`, `ANTHROPIC_API_KEY`.
- Produces: a real `Aspiration.md` and evidence the synthesis works.

- [ ] **Step 1: Confirm the key is present**

Run: `grep -q '^ANTHROPIC_API_KEY=.\+' .env && echo "key present" || echo "MISSING KEY"`
Expected: `key present`. If missing, stop and ask the user to add it before running.

- [ ] **Step 2: Run it**

Run: `./venv/bin/python aspirations.py`
Expected: prints `N gap mentions across M postings -> Aspiration.md` (M matches the number of tailored resumes that carry a coverage section — the 6 re-run under R1).

- [ ] **Step 3: Verify the output**

Run:
```bash
echo "=== headings ===" ; grep -n '^## ' Aspiration.md
echo "=== top of file ===" ; head -20 Aspiration.md
```
Expected: the three category headings (`Certifications & Education`, `Tools & Technologies`, `Skills & Capabilities`) are present; clusters show recurrence counts and Acquire/Strengthen tags; a term that was `missing` across multiple postings (e.g. consulting, an advanced degree, Power BI) surfaces as a high-ranked cluster.

- [ ] **Step 4: Confirm it is git-ignored**

Run: `git check-ignore Aspiration.md && echo "ignored OK"`
Expected: prints `Aspiration.md` then `ignored OK` (the generated file won't be committed).

---

## Notes

R2 completes the roadmap from the original save-posting spec (`#3` scraper, R1 Anthropic/tailoring, R3 stale-flagging, R2 aspiration file). No further roadmap items remain.
