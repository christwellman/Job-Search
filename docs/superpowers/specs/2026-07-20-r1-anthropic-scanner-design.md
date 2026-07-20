# Design: R1 — Anthropic Migration + Leveled-Up Tailoring + PDF

**Date:** 2026-07-20
**Status:** Approved (design), pending implementation plan
**Builds on:** [2026-07-20-save-posting-workflow-design.md](./2026-07-20-save-posting-workflow-design.md) (roadmap item R1)

---

## Context

`Scanner.py` currently calls OpenAI (`gpt-4o-mini`) twice per posting — a summary and a resume tailoring — writing both to `Customized Resumes/`. `markdown_to_pdf.py` converts one hardcoded resume to PDF. The repo `venv` is a broken symlink (points at an Intel Python 3.12 absent on this arm64 Mac), so nothing that needs third-party packages runs today.

This spec migrates the tooling to Anthropic (Claude), levels up the tailoring, generalizes the PDF converter, and rebuilds the environment.

### Decisions locked during brainstorming

| Decision | Choice |
|---|---|
| Provider | Anthropic (Claude) |
| Summary model | `claude-haiku-4-5` (cheap, fast — summaries are simple) |
| Tailoring model | `claude-sonnet-5` (near-Opus quality where it matters) |
| Scope | Core **+** generalize `markdown_to_pdf.py` |
| `listModels.py` | **Delete** |
| Frontmatter | Scanner parses posting YAML headers (from `#3`); legacy header-less postings still work |
| Reference material | Tailoring draws on `Reference/Action words` and `Reference/Resume Statements.md` |
| ATS gap | Tailored resume gets an appended "ATS Keyword Coverage" checklist |

---

## Architecture / file plan

| File | Change | Responsibility |
|---|---|---|
| `postings.py` | **New** | All posting-format logic: `parse_posting(text) -> (meta, body)`, plus `render_posting` and `sanitize_filename` **moved here** from `save_posting.py`. Single home for the format. |
| `save_posting.py` | Modify | Import `render_posting` / `sanitize_filename` from `postings.py` instead of defining them. Behavior unchanged. |
| `Scanner.py` | Rewrite | Anthropic client; Haiku summary + Sonnet tailoring; parse frontmatter; improved prompts; inject Reference material; append keyword coverage. |
| `markdown_to_pdf.py` | Rewrite | CLI: `python markdown_to_pdf.py <resume.md> [out.pdf]` → PDF beside the source; intermediate HTML to a temp file. |
| `requirements.txt` | **New** | Pin `anthropic`, `python-dotenv`, `markdown`, `weasyprint`, `tqdm`. |
| `listModels.py` | **Delete** | OpenAI-only helper, no longer needed. |
| `.env` | User edits | Add `ANTHROPIC_API_KEY`. Old `OPENAI_*` vars left in place but unused. |
| `venv/` | Rebuild | Recreate with Homebrew `python3`; `pip install -r requirements.txt`. |

### `postings.py` interface

```python
FIELDS = ("title", "company", "location", "source_url", "date_scraped")

def sanitize_filename(title: str, company: str) -> str: ...
def render_posting(meta: dict, body: str) -> str: ...          # moved from save_posting.py
def parse_posting(text: str) -> tuple[dict, str]:
    """Split a posting file into (metadata dict, body).
    If the text has no leading `---` YAML block, returns ({}, text.strip())."""
```

`parse_posting` reads a leading `---`-fenced block of `key: value` lines (the exact shape `render_posting` writes — no external YAML dependency needed; a simple line parser suffices) and returns the remaining body. Header-less legacy postings yield `({}, whole_text)`.

### Scanner flow (per posting, unchanged threading)

1. Read the posting file, `parse_posting` → `meta`, `body`.
2. **Summary** (`claude-haiku-4-5`): system = career specialist; user = the same scan-summary task as today, over `body` (+ `meta` when present). ~1024 max tokens.
3. **Tailoring** (`claude-sonnet-5`): system = expert resume writer + ATS specialist; user = the resume, the parsed posting (title/company/location + body), and the two Reference files as source phrasing. Instructions (tightened from today's 16-rule block): position experience against the posting's needs; reuse the posting's exact keywords; quantify; active voice; **never fabricate** experience, titles, or dates; output Markdown; end with an **"## ATS Keyword Coverage"** section listing the posting's key terms and whether each is now reflected. ~8000 max tokens (non-streaming — well under the SDK timeout).
4. Write `Customized Resumes/summary_<file>` and `Customized Resumes/Chris Twellman - <file>.md` as today.

One shared `anthropic.Anthropic()` client (thread-safe) is reused across the pool. The SDK auto-retries 429/5xx. Prompts avoid "CRITICAL: YOU MUST" phrasing — Claude follows instructions literally, so terse, clear directives produce better output than aggressive ones. Extended thinking is left off (the tailoring prompt is explicit; keeps latency and cost predictable).

### `markdown_to_pdf.py`

`argparse`: required `input` path, optional `output` (defaults to the input path with a `.pdf` extension). Read the Markdown, convert with `markdown`, wrap in HTML linking `Resume.css`, write the intermediate HTML to a `tempfile` (not the repo), render with WeasyPrint. Print the output path.

---

## Configuration & environment

- **`.env`:** `Scanner.py`'s required-vars check becomes `["ANTHROPIC_API_KEY"]`. The user adds the key; Claude never sees it.
- **Auth:** `anthropic.Anthropic()` resolves the key from `ANTHROPIC_API_KEY` (loaded via `python-dotenv`, matching the current pattern).
- **venv rebuild:** delete the broken `venv/`, create a fresh one with Homebrew `python3`, `pip install -r requirements.txt`. `venv/` stays git-ignored.

---

## Risks

- **WeasyPrint system libraries (pango/cairo).** These were present when the PDF last worked, so the rebuild should run. If PDF generation errors on a missing native lib, the fix is `brew install pango` — called out in the plan as a conditional step, not run silently.
- **API key availability.** The live end-to-end test is blocked until the user adds `ANTHROPIC_API_KEY` to `.env`. The plan gates the run step on that.

---

## Testing / verification

- **`postings.py`:** unit tests (stdlib `unittest`) for `parse_posting` — a full 5-field header round-trips with `render_posting`; a header-less string returns `({}, text)`; a partial header parses present keys. Re-run the existing `save_posting` tests to confirm the import move didn't break anything.
- **`markdown_to_pdf.py`:** run it on a real customized resume; confirm a non-empty PDF is produced at the expected path and no `resume.html` is left in the repo root.
- **Scanner (live):** after the user adds `ANTHROPIC_API_KEY`, run against the `Data Analyst - GitHub` posting saved in `#3`; confirm a summary and a tailored resume (with the ATS Keyword Coverage section) are written, the frontmatter was parsed (no `---` leakage into the prompt), and a legacy header-less posting still processes.

---

## Out of scope

R2 (Aspiration/gap file) and R3 (stale-posting flagging) remain separate future specs. The "ATS Keyword Coverage" section produced here is the data R2 will aggregate.
