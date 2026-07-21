# Job-Search - Content Index

**Repository:** https://github.com/christwellman/Job-Search  
**Branch:** `main`

*Tools to tailor a resume to specific job postings using Claude — capture postings, tailor and ATS-score resumes, export PDFs, flag stale postings, and track skill gaps.*

## Retrieval Method

```bash
curl -s "https://api.github.com/repos/OWNER/REPO/contents/PATH?ref=BRANCH" \
  -H "Accept: application/vnd.github+json" | \
  python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())"
```

---

### Pipeline scripts

| Description | Path |
|-------------|------|
| Tailor resumes to postings — Haiku summary + Sonnet tailoring + ATS keyword-coverage table | `Scanner.py` |
| Write a scraped posting to `Postings/` (called by the save-posting skill) | `save_posting.py` |
| Posting file format — `parse_posting` / `render_posting` / `sanitize_filename` | `postings.py` |
| Convert a Markdown resume to PDF | `markdown_to_pdf.py` |
| Flag and (with `--archive`) move postings older than N months into `Archive/` | `stale.py` |
| Build `Aspiration.md` from the ATS-coverage gaps in tailored resumes | `aspirations.py` |

### Tests

| Description | Path |
|-------------|------|
| Tests for `postings.py` | `test_postings.py` |
| Tests for `save_posting.py` | `test_save_posting.py` |
| Tests for `markdown_to_pdf.py` | `test_markdown_to_pdf.py` |
| Tests for `stale.py` | `test_stale.py` |
| Tests for `aspirations.py` | `test_aspirations.py` |

### Skill

| Description | Path |
|-------------|------|
| save-posting — paste a job URL, Claude reads it from logged-in Chrome and writes a frontmatter-tagged posting | `.claude/skills/save-posting/SKILL.md` |

### Docs

| Description | Path |
|-------------|------|
| Per-feature design specs | `docs/superpowers/specs/` |
| Per-feature implementation plans | `docs/superpowers/plans/` |

### Other

| Description | Path |
|-------------|------|
| Usage guide | `README.md` |
| Python dependencies | `requirements.txt` |
| License | `LICENSE.md` |

> Note: `Postings/`, `Customized Resumes/`, `Archive/`, `Resume.md`, `Resume.css`, `Aspiration.md`, and `*.pdf` are git-ignored personal content and are not part of the tracked repository.

---
*Regenerated 2026-07-21 to reflect the current codebase.*
