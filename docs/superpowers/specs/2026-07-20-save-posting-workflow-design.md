# Design: "Save Posting" Workflow + Repo Leveling Roadmap

**Date:** 2026-07-20
**Status:** Approved (design), pending implementation plan
**First build:** Feature #3 — URL → `Postings/` save workflow

---

## Context

This repo helps tailor a resume to specific job postings. Today the flow is:

- Postings are manually copy-pasted into `Postings/*.txt`.
- `Scanner.py` calls OpenAI (`gpt-4o-mini`) to (1) summarize each posting and (2) tailor `Resume.md` to it, writing to `Customized Resumes/`.
- `markdown_to_pdf.py` converts a single hardcoded resume `.md` → PDF.

The user wants to level the repo up with four ideas. This spec **fully designs the first** (the scraper) and captures the other three as a roadmap so nothing is lost. Each roadmap item gets its own spec → plan → build cycle later.

### Decisions locked during brainstorming

| Decision | Choice |
|---|---|
| LLM provider direction | **Migrate to Claude/Anthropic** (applies when Scanner is leveled up; the save workflow itself needs no LLM API) |
| First feature to build | **URL → Postings save workflow** (#3) |
| Primary posting sources | LinkedIn, Workday/iCIMS/Taleo, company career pages — all JS-rendered / login-gated |
| Trigger | Ask Claude Code in chat (paste a URL) |
| Metadata header | **Yes, on new postings only** (no backfill of existing 21) |
| After saving | **Just save + confirm** (no auto-tailor) |

---

## Feature #3 — "Save Posting" workflow (THIS BUILD)

### Why a Claude Code skill, not a Python scraper

The user's sources — LinkedIn, Workday, iCIMS — are JavaScript-rendered and login-gated. A standalone `requests`/`BeautifulSoup` script cannot read them (no auth, no JS execution, anti-bot). Driving the user's **already-logged-in Chrome** via the `claude-in-chrome` tools sidesteps all three problems, and the user chose "ask Claude Code in chat" as the trigger. So the deliverable is a **reusable skill**, not a script.

### Trigger

The user does one of:
- Pastes a job URL in chat, or
- Says "save this posting" while the tab is already open.

### Mechanism

1. `tabs_context_mcp` to see current tabs; open the URL in a new tab (`tabs_create_mcp` / `navigate`) unless the user is already on it.
2. Read the rendered page with `get_page_text` / `read_page`.
3. If the page shows a login wall or blank/blocked content, stop and ask the user to log in (or navigate to the posting) in Chrome, then retry. As a fallback, the user can paste the description text directly.

### Extraction

From the rendered page, extract:
- **title**, **company**, **location** (or "Remote"), and the **full job description body**.
- Strip boilerplate: site nav, cookie banners, "Apply now"/"Save job" chrome, related-jobs sidebars, footers.

### Output

Write to `Postings/<Title> - <Company>.txt` (matches existing naming so `Scanner.py` picks it up; keeps `.txt` so the tailored-resume filename convention in `Scanner.py` still works). Sanitize illegal filename characters.

File contents = YAML frontmatter + cleaned description body:

```
---
title: Senior Business Operations Manager
company: Netflix
location: Remote (US)
source_url: https://jobs.netflix.com/jobs/12345
date_scraped: 2026-07-20
---

<full cleaned job description text>
```

- `date_scraped` uses today's date.
- Fields that can't be found are written as empty (e.g. `location:`), never fabricated.
- The header is **plain text**, so the current `Scanner.py` (which reads the whole file) tolerates it today; the leveled-up Scanner will parse it.

### Behavior after save

Report `title / company / location / saved path`, then stop. No auto-tailoring (deliberate, per decision).

### Edge cases & error handling

- **Duplicate filename exists:** warn and ask before overwriting.
- **Login/blocked page:** ask user to log in in Chrome and retry; offer manual-paste fallback.
- **Multiple postings on one page:** ask which one, or save the one in focus.
- **PDF/attachment postings:** read via the PDF path if reachable; otherwise ask user to paste text.
- **Ambiguous company/title:** make a best guess from the page and show it in the confirmation so the user can correct the filename.

### Packaging

A skill at `.claude/skills/save-posting/SKILL.md` documenting the trigger, the extraction/cleaning rules, the exact frontmatter schema, the filename convention, and the error paths — so behavior is identical every session.

### Testing / verification

Manual end-to-end: run the skill against one real posting from each source class (a Greenhouse/plain page, a LinkedIn page, a Workday page) and verify the saved file has (a) correct frontmatter fields, (b) a clean body with boilerplate removed, (c) a filename that `Scanner.py` accepts. Confirm the duplicate-name and login-wall paths behave as designed.

### Out of scope (YAGNI)

Scheduling, bulk-URL queues, a database, and browser scraping of sites the user isn't logged into. One URL → one clean file, on demand.

---

## Roadmap — the other three ideas (future specs)

These are captured here so the "level up the repo" intent is recorded. Each is its own future brainstorming → spec → plan cycle; details below are direction, not final design.

### R1. Level up resume tailoring + migrate Scanner to Anthropic (Features #1 + provider migration)
Rework `Scanner.py` to call the Anthropic API (Claude) instead of OpenAI, teach it to parse the new posting frontmatter, and improve tailoring quality (explicit keyword/ATS gap matching against the posting, stronger use of `Reference/` action words and resume statements). Add `ANTHROPIC_API_KEY` to `.env`. Likely also generalize `markdown_to_pdf.py` (currently hardcoded to one file) to convert any customized resume.

### R2. Aspiration / gap file (Feature #2)
Across postings the user marks as "interesting," extract recurring **required** skills, tools, certifications, and education, diff them against the resume, and maintain an `Aspiration.md` of gaps ranked by frequency — a data-driven "what to learn/certify next" list. Depends on the frontmatter and clean bodies produced by #3.

### R3. Stale flagging & cleanup (Feature #4)
A helper that scans `Postings/` and `Customized Resumes/`, finds items older than 6 months (using `date_scraped` frontmatter, falling back to file mtime for legacy files), and **suggests** moving them to `Archive/` — flag/suggest only, never auto-delete. Could run on demand or as a periodic check.

---

## Dependency order

```
#3 save-posting (frontmatter + clean bodies)
   → R2 aspiration analysis  (needs structured postings)
   → R3 stale flagging       (needs date_scraped)
R1 Scanner/Anthropic upgrade  (independent; can happen anytime)
```

`#3` first is correct: it produces the structured data the other features rely on.
