# Design: R3 — Stale-Posting Flagging (`stale.py`)

**Date:** 2026-07-20
**Status:** Approved (design), pending implementation plan
**Builds on:** [2026-07-20-save-posting-workflow-design.md](./2026-07-20-save-posting-workflow-design.md) (roadmap item R3), [2026-07-20-r1-anthropic-scanner-design.md](./2026-07-20-r1-anthropic-scanner-design.md)

---

## Context

Postings accumulate in `Postings/*.txt`, each spawning two derived files in `Customized Resumes/` — `summary_<name>.txt` and `Chris Twellman - <name>.md` (the names `Scanner.py` writes). Over time old, no-longer-relevant postings pile up. R3 adds a housekeeping tool that finds postings older than a threshold and helps move them (with their derived files) into the existing `Archive/`.

### Decisions locked during brainstorming

| Decision | Choice |
|---|---|
| Action | Report by default; `--archive` flag moves after review. Never deletes. |
| Unit flagged/moved | The posting **plus its derived files**, as one group |
| Age source | `date_scraped` frontmatter if present, else file mtime (report which was used) |
| Threshold | 6 months, calendar-accurate; `--months N` overrides |
| Delivery | A stdlib-only Python CLI (`stale.py`) |
| Also in scope | Update README; run a full-pipeline verification |

---

## `stale.py`

```
python stale.py             # report stale groups; change nothing
python stale.py --archive   # move stale groups into Archive/
python stale.py --months 3  # override the 6-month threshold
```

No third-party dependencies — reuses `postings.parse_posting`. Runs under the venv or system `python3`.

### Age determination (per posting)

`effective_date(path) -> (date, source)`:
1. Read the posting, `parse_posting` → `meta`. If `meta["date_scraped"]` is a valid ISO date, use it (`source="date_scraped"`).
2. Otherwise use the file's mtime date (`source="mtime"`).

A posting is **stale** when its effective date is strictly before `months_ago(today, N)`. `months_ago` does calendar month subtraction (clamping the day to the target month's length), not a fuzzy day count.

### Grouping

For a stale `Postings/<name>.txt`, the group also includes whichever of these exist:
- `Customized Resumes/summary_<name>.txt`
- `Customized Resumes/Chris Twellman - <stem>.md`  (where `<stem>` = `<name>` with `.txt` → `.md`)

Moving the group together prevents orphaned summaries/resumes.

### Report (default)

For each stale group, print: posting name, age (e.g. `8 months (via date_scraped)`), and the derived files that would move. End with a total count. No files change.

### `--archive`

Move every file in each stale group into `Archive/` (created if missing), preserving filenames, via `shutil.move`. **Never deletes.** If a same-named file already exists in `Archive/`, **skip** that file (no overwrite) and report the skip. Print each moved path and a summary. The two-step flow (review bare, then re-run with `--archive`) is the safety mechanism.

### Structure (clean + testable)

Pure helpers, each unit-tested with `unittest` + tmp dirs:
- `months_ago(d: date, n: int) -> date`
- `effective_date(path: Path) -> (date, str)`
- `derived_paths(posting_name: str, resumes_dir: Path) -> list[Path]`
- `find_stale(postings_dir, resumes_dir, cutoff, today) -> list[dict]`
- `archive_group(group: dict, archive_dir: Path) -> list[Path]`

`main()` wires `argparse` (`--months` default 6, `--archive`) to these and does the printing.

---

## README update

Add a short "Housekeeping" section documenting `stale.py` (report vs `--archive`, the `--months` override, and that it never deletes).

---

## Testing / verification

- **Unit (`test_stale.py`, stdlib `unittest`):**
  - `months_ago` — e.g. `months_ago(2026-07-20, 6) == 2026-01-20`; day-clamp case (`2026-03-31` minus 1 month → `2026-02-28`).
  - `effective_date` — a posting with a `date_scraped` header returns that date + `"date_scraped"`; a header-less posting returns its mtime date + `"mtime"`.
  - `derived_paths` — returns only the derived files that actually exist.
  - `find_stale` — with tmp dirs, a posting dated 8 months ago is flagged; one dated today is not; the flagged group includes its existing derived files.
  - `archive_group` — moves posting + derived into a tmp Archive/; a pre-existing same-named file in Archive/ is left untouched and the source is skipped (not moved, not overwritten).
- **Live full-pipeline check:** exercise the whole chain end to end —
  1. a posting is present in `Postings/` (reuse the saved `Data Analyst - GitHub`),
  2. `Scanner.py` produces its summary + tailored resume,
  3. `markdown_to_pdf.py` renders that tailored resume to PDF,
  4. `stale.py` (bare) reports, and `stale.py --archive` moves a **throwaway fixture posting** given an old `date_scraped` (plus a matching derived file) into `Archive/` — proving real files move and non-stale files are untouched. Remove the fixture afterward so it doesn't linger in `Archive/`.

---

## Out of scope (YAGNI)

No scheduling/cron; no scanning `Customized Resumes/` for orphans independent of postings; no deletion. On-demand and posting-driven. R2 (Aspiration/gap file) remains a separate future spec.
