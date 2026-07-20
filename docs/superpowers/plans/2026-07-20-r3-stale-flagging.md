# R3 — Stale-Posting Flagging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `stale.py` — a CLI that reports postings older than a threshold (with their derived files) and, on `--archive`, moves those groups into `Archive/`; never deletes.

**Architecture:** A stdlib-only module of pure helpers (`months_ago`, `effective_date`, `derived_paths`, `find_stale`, `archive_group`) that reuse `postings.parse_posting`; `main()` wires argparse to them. Unit-tested with `unittest`; verified live across the full pipeline.

**Tech Stack:** Python 3.11 standard library only (`argparse`, `calendar`, `datetime`, `shutil`, `pathlib`, `unittest`). Reuses local `postings.py`.

## Global Constraints

- No new dependencies — stdlib only. Runs under `./venv/bin/python` or system `python3`.
- Never delete. `--archive` only moves; a name collision in `Archive/` is skipped, never overwritten.
- Threshold default 6 months, `--months N` override; staleness uses calendar-accurate month math.
- Age source per posting: `date_scraped` frontmatter if a valid ISO date, else file mtime — and the report states which.
- A stale group = the posting plus its existing `summary_<name>.txt` and `Chris Twellman - <stem>.md` derived files.

---

### Task 1: `stale.py` — helpers + CLI

**Files:**
- Create: `stale.py`
- Test: `test_stale.py`

**Interfaces:**
- Consumes: `postings.parse_posting`.
- Produces:
  - `months_ago(d, n) -> date`
  - `effective_date(path) -> (date, source)`
  - `derived_paths(posting_name, resumes_dir) -> list[Path]`
  - `find_stale(postings_dir, resumes_dir, cutoff, today) -> list[dict]` (each group dict: `posting`, `date`, `source`, `age_days`, `derived`)
  - `archive_group(group, archive_dir) -> list[Path]` (moved paths; skips collisions)
  - CLI `python stale.py [--months N] [--archive]`

- [ ] **Step 1: Write the failing tests**

Create `test_stale.py`:

```python
import datetime
import os
import tempfile
import unittest
from pathlib import Path

import stale


class TestMonthsAgo(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(stale.months_ago(datetime.date(2026, 7, 20), 6), datetime.date(2026, 1, 20))

    def test_year_wrap(self):
        self.assertEqual(stale.months_ago(datetime.date(2026, 3, 15), 6), datetime.date(2025, 9, 15))

    def test_day_clamp(self):
        self.assertEqual(stale.months_ago(datetime.date(2026, 3, 31), 1), datetime.date(2026, 2, 28))


class TestEffectiveDate(unittest.TestCase):
    def test_uses_date_scraped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("---\ntitle: X\ndate_scraped: 2025-01-15\n---\n\nbody\n")
            d, src = stale.effective_date(p)
            self.assertEqual(d, datetime.date(2025, 1, 15))
            self.assertEqual(src, "date_scraped")

    def test_falls_back_to_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "y.txt"
            p.write_text("Plain posting, no header.\n")
            ts = datetime.datetime(2020, 6, 1).timestamp()
            os.utime(p, (ts, ts))
            d, src = stale.effective_date(p)
            self.assertEqual(d, datetime.date(2020, 6, 1))
            self.assertEqual(src, "mtime")


class TestDerivedPaths(unittest.TestCase):
    def test_only_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            resumes = Path(tmp)
            (resumes / "summary_Role - Co.txt").write_text("s")
            # the tailored .md is intentionally absent
            got = stale.derived_paths("Role - Co.txt", resumes)
            self.assertEqual([p.name for p in got], ["summary_Role - Co.txt"])


class TestFindStale(unittest.TestCase):
    def test_flags_old_not_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            postings = Path(tmp) / "Postings"; postings.mkdir()
            resumes = Path(tmp) / "Resumes"; resumes.mkdir()
            (postings / "Old - Co.txt").write_text("---\ntitle: Old\ndate_scraped: 2025-01-01\n---\n\nb\n")
            (postings / "New - Co.txt").write_text("---\ntitle: New\ndate_scraped: 2026-07-01\n---\n\nb\n")
            (resumes / "Chris Twellman - Old - Co.md").write_text("r")
            today = datetime.date(2026, 7, 20)
            cutoff = stale.months_ago(today, 6)  # 2026-01-20
            groups = stale.find_stale(postings, resumes, cutoff, today)
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["posting"].name, "Old - Co.txt")
            self.assertEqual([p.name for p in groups[0]["derived"]], ["Chris Twellman - Old - Co.md"])


class TestArchiveGroup(unittest.TestCase):
    def test_moves_and_skips_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            postings = Path(tmp) / "Postings"; postings.mkdir()
            archive = Path(tmp) / "Archive"; archive.mkdir()
            posting = postings / "Old - Co.txt"; posting.write_text("body")
            derived = postings / "Chris Twellman - Old - Co.md"; derived.write_text("resume")
            # pre-existing collision for the derived file
            (archive / "Chris Twellman - Old - Co.md").write_text("ORIGINAL")
            group = {"posting": posting, "derived": [derived]}
            moved = stale.archive_group(group, archive)
            # posting moved
            self.assertTrue((archive / "Old - Co.txt").exists())
            self.assertFalse(posting.exists())
            # colliding derived left untouched, source not moved
            self.assertEqual((archive / "Chris Twellman - Old - Co.md").read_text(), "ORIGINAL")
            self.assertTrue(derived.exists())
            self.assertEqual([p.name for p in moved], ["Old - Co.txt"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_stale -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'stale'`.

- [ ] **Step 3: Create `stale.py`**

```python
"""Flag postings older than a threshold and (optionally) archive them.

Usage:
    python stale.py             # report stale groups; change nothing
    python stale.py --archive   # move stale groups into Archive/
    python stale.py --months 3  # override the 6-month threshold
"""
import argparse
import calendar
import datetime
import shutil
from pathlib import Path

from postings import parse_posting

SCRIPT_DIR = Path(__file__).resolve().parent
POSTINGS_DIR = SCRIPT_DIR / "Postings"
RESUMES_DIR = SCRIPT_DIR / "Customized Resumes"
ARCHIVE_DIR = SCRIPT_DIR / "Archive"


def months_ago(d: datetime.date, n: int) -> datetime.date:
    month_index = d.month - 1 - n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def effective_date(path: Path) -> tuple[datetime.date, str]:
    meta, _ = parse_posting(path.read_text(encoding="utf-8", errors="ignore"))
    ds = meta.get("date_scraped")
    if ds:
        try:
            return datetime.date.fromisoformat(ds), "date_scraped"
        except ValueError:
            pass
    mtime = datetime.date.fromtimestamp(path.stat().st_mtime)
    return mtime, "mtime"


def derived_paths(posting_name: str, resumes_dir: Path) -> list[Path]:
    stem = posting_name[:-4] if posting_name.endswith(".txt") else posting_name
    candidates = [
        resumes_dir / f"summary_{posting_name}",
        resumes_dir / f"Chris Twellman - {stem}.md",
    ]
    return [p for p in candidates if p.exists()]


def find_stale(postings_dir: Path, resumes_dir: Path,
               cutoff: datetime.date, today: datetime.date) -> list[dict]:
    groups = []
    for posting in sorted(postings_dir.glob("*.txt")):
        date, source = effective_date(posting)
        if date < cutoff:
            groups.append({
                "posting": posting,
                "date": date,
                "source": source,
                "age_days": (today - date).days,
                "derived": derived_paths(posting.name, resumes_dir),
            })
    return groups


def archive_group(group: dict, archive_dir: Path) -> list[Path]:
    archive_dir.mkdir(parents=True, exist_ok=True)
    moved = []
    for path in [group["posting"], *group["derived"]]:
        target = archive_dir / path.name
        if target.exists():
            print(f"  skip (already in Archive): {path.name}")
            continue
        shutil.move(str(path), str(target))
        moved.append(target)
    return moved


def _age_label(age_days: int, source: str) -> str:
    return f"{age_days // 30} months (via {source})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Flag postings older than N months.")
    parser.add_argument("--months", type=int, default=6, help="Staleness threshold (default 6)")
    parser.add_argument("--archive", action="store_true", help="Move stale groups into Archive/")
    args = parser.parse_args()

    today = datetime.date.today()
    cutoff = months_ago(today, args.months)
    groups = find_stale(POSTINGS_DIR, RESUMES_DIR, cutoff, today)

    if not groups:
        print(f"No postings older than {args.months} months.")
        return

    print(f"{len(groups)} posting(s) older than {args.months} months:\n")
    for g in groups:
        print(f"- {g['posting'].name}  [{_age_label(g['age_days'], g['source'])}]")
        for d in g["derived"]:
            print(f"    derived: {d.name}")

    if args.archive:
        print("\nArchiving...")
        total = 0
        for g in groups:
            total += len(archive_group(g, ARCHIVE_DIR))
        print(f"Moved {total} file(s) to Archive/.")
    else:
        print("\nRun again with --archive to move these into Archive/.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest test_stale -v`
Expected: PASS (8 tests OK).

- [ ] **Step 5: Smoke-test the CLI (read-only) on the real repo**

Run: `python3 stale.py`
Expected: either `No postings older than 6 months.` or a list of stale groups — either is valid; it must not error and must not modify any files.

- [ ] **Step 6: Commit**

```bash
git add stale.py test_stale.py
git commit -m "feat: add stale.py to flag and archive old postings"
```

---

### Task 2: README housekeeping section

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: `stale.py` (Task 1).
- Produces: user docs.

- [ ] **Step 1: Add the section**

Append to `README.md` (after the PDF section):

```markdown
## Housekeeping

Flag postings older than 6 months (using each posting's `date_scraped`, or its
file date for older files):

    ./venv/bin/python stale.py            # report only — changes nothing
    ./venv/bin/python stale.py --archive  # move the flagged groups into Archive/
    ./venv/bin/python stale.py --months 3 # use a different threshold

Each flagged posting is moved together with its summary and tailored resume.
It never deletes, and never overwrites a file already in `Archive/`.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document stale.py housekeeping command"
```

---

### Task 3: Full-pipeline live verification

**Files:** none (verification only; uses a throwaway fixture that is removed at the end).

**Interfaces:**
- Consumes: `Scanner.py`, `markdown_to_pdf.py`, `stale.py`, the saved `Data Analyst - GitHub` posting.
- Produces: evidence the whole chain works and that `stale.py --archive` moves real files.

- [ ] **Step 1: Confirm the pipeline's earlier stages still work**

Run:
```bash
ls "Customized Resumes/Chris Twellman - Data Analyst - GitHub.md" \
   "Customized Resumes/summary_Data Analyst - GitHub.txt"
./venv/bin/python markdown_to_pdf.py "Customized Resumes/Chris Twellman - Data Analyst - GitHub.md" \
   "/private/tmp/claude-501/-Users-christwellman-Projects-Job-Search/a470a4ad-93ca-4a8b-b3ce-baf453b596be/scratchpad/pipeline_github.pdf"
test -s "/private/tmp/claude-501/-Users-christwellman-Projects-Job-Search/a470a4ad-93ca-4a8b-b3ce-baf453b596be/scratchpad/pipeline_github.pdf" && echo "PDF OK"
```
Expected: both files listed, then `Wrote ...` and `PDF OK`. (If the GitHub outputs are missing, run `./venv/bin/python Scanner.py` first.)

- [ ] **Step 2: Create a throwaway stale fixture**

Run:
```bash
printf -- '---\ntitle: Fixture Role\ncompany: ZZ Test\nlocation: Remote\nsource_url: https://example.test/1\ndate_scraped: 2024-01-01\n---\n\nOld fixture posting body.\n' \
  > "Postings/Fixture Role - ZZ Test.txt"
printf 'tailored fixture\n' > "Customized Resumes/Chris Twellman - Fixture Role - ZZ Test.md"
echo "fixture created"
```
Expected: `fixture created`. (`Postings/` and `Customized Resumes/` are git-ignored, so this leaves no repo trace.)

- [ ] **Step 3: Report (read-only) and confirm the fixture is flagged**

Run: `python3 stale.py`
Expected: the output lists `Fixture Role - ZZ Test.txt  [... months (via date_scraped)]` with `derived: Chris Twellman - Fixture Role - ZZ Test.md`. Note whether any *real* postings are also listed (older files flagged by mtime are legitimate — that is correct behavior, not a bug).

- [ ] **Step 4: Archive and verify the move**

If Step 3 listed **only** the fixture, run `python3 stale.py --archive`. If it also listed real postings you don't want moved, instead archive just the fixture explicitly:
```bash
mv "Postings/Fixture Role - ZZ Test.txt" "Archive/Fixture Role - ZZ Test.txt"
mv "Customized Resumes/Chris Twellman - Fixture Role - ZZ Test.md" "Archive/Chris Twellman - Fixture Role - ZZ Test.md"
```
Then verify:
```bash
test -e "Archive/Fixture Role - ZZ Test.txt" \
  && test -e "Archive/Chris Twellman - Fixture Role - ZZ Test.md" \
  && test ! -e "Postings/Fixture Role - ZZ Test.txt" \
  && echo "archive move verified"
```
Expected: `archive move verified` — the group moved into `Archive/` and left `Postings/` clean.

- [ ] **Step 5: Remove the fixture from Archive/**

Run:
```bash
rm -f "Archive/Fixture Role - ZZ Test.txt" "Archive/Chris Twellman - Fixture Role - ZZ Test.md"
test ! -e "Archive/Fixture Role - ZZ Test.txt" && echo "fixture cleaned up"
```
Expected: `fixture cleaned up` — no throwaway files linger anywhere.

---

## Notes for later (roadmap)

R2 (Aspiration/gap file) remains the last roadmap item — it aggregates the `## ATS Keyword Coverage` sections `Scanner.py` writes. Separate future spec.
