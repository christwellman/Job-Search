# Design: R2 — Aspiration / Gap File (`aspirations.py`)

**Date:** 2026-07-21
**Status:** Approved (design), pending implementation plan
**Builds on:** [2026-07-20-save-posting-workflow-design.md](./2026-07-20-save-posting-workflow-design.md) (roadmap item R2), [2026-07-20-r1-anthropic-scanner-design.md](./2026-07-20-r1-anthropic-scanner-design.md)

---

## Context

R1 made `Scanner.py` append an `## ATS Keyword Coverage` table to every tailored resume in `Customized Resumes/Chris Twellman - <name>.md`. Each row is `| <keyword> | <coverage> |`, where coverage begins with `yes`, `partial`, or `missing` (often followed by parenthetical or em-dash detail). R2 mines those tables to build an **Aspiration file** — the recurring skills, tools, certifications, and education the user does not yet fully have across the jobs they've pursued.

The gap terms are free-text and posting-specific ("Consulting", "Management consulting experience (top firm)", "2+ years consulting" are one gap phrased three ways), so a raw exact-string frequency count is noisy. The design pairs deterministic parsing with one LLM call that clusters and categorizes.

### Decisions locked during brainstorming

| Decision | Choice |
|---|---|
| Generation | Deterministic parse **+** one Claude **Haiku** call to cluster synonyms, categorize, and rank |
| Gap sources | Both **missing** and **partial** rows |
| Categories | Certifications & Education / Tools & Technologies / Skills & Capabilities |
| Ranking | By recurrence — how many distinct postings a cluster appears in |
| Output | `Aspiration.md` at repo root, regenerated fresh each run |
| Scope | All tailored resumes that contain a coverage section (older section-less files skipped) |

---

## `aspirations.py`

```
./venv/bin/python aspirations.py
```

Lazy Anthropic client, gated on `ANTHROPIC_API_KEY` (same pattern as `Scanner.py`). Uses `claude-haiku-4-5` for the synthesis (light clustering task; cheap).

### 1. Deterministic collection (stdlib, testable)

- `parse_coverage(md_text) -> list[(keyword, cls)]`:
  - Find the `## ATS Keyword Coverage` section; return `[]` if absent.
  - For each markdown table row after it (until the next `## ` heading), split on `|`, take cell 0 = keyword, cell 1 = coverage.
  - Skip the header row (coverage cell doesn't start with yes/partial/missing) and the `---` separator row.
  - Classify by the leading word of the coverage cell via `^\s*(yes|partial|missing)\b` (case-insensitive). Keep only rows classified `partial` or `missing`, returning `(keyword, cls)`.
- `collect_gaps(resumes_dir) -> list[dict]`:
  - Iterate `Chris Twellman - *.md`, run `parse_coverage` on each, and gather `{"keyword", "cls", "source"}` where `source` is the job name (the filename stem with the leading `Chris Twellman - ` stripped).

### 2. LLM synthesis (one Haiku call)

Build a plain-text list of the collected gaps — one line each, `[missing|partial] <keyword>  (from: <job>)` — and send it to Haiku with instructions to:
- cluster synonymous / closely-related items into a single named gap;
- assign each cluster to one category: **Certifications & Education**, **Tools & Technologies**, or **Skills & Capabilities**;
- rank clusters within each category by the number of distinct source postings they appear in (most-recurring first);
- tag each cluster **Acquire** (predominantly `missing`) or **Strengthen** (predominantly `partial`);
- output clean Markdown suitable to save directly as `Aspiration.md`, with the three categories as `##` sections and a short one-line intro.

Write the returned Markdown to `Aspiration.md` (overwrite). Print a summary: `N gap mentions across M postings → Aspiration.md`.

### 3. Empty / error handling

- If `collect_gaps` finds nothing (no resume has a coverage section yet), print a clear message, make **no** API call, and write no file.
- Wrap the API call; on failure log the error and exit non-zero without overwriting an existing `Aspiration.md`.

---

## Wiring

- **`.gitignore`:** add `Aspiration.md` (personal generated artifact, like the resumes and PDFs).
- **README:** add an "Aspiration file" section — what it does, that it reads the tailored resumes' coverage tables, and `./venv/bin/python aspirations.py`.

---

## Testing / verification

- **Unit (`test_aspirations.py`, stdlib `unittest`):**
  - `parse_coverage` — a sample with a coverage table returns only the `partial`/`missing` rows with correct classes; header wording variants (`Keyword / Term`, `Keyword/Term`) both parse; coverage detail (`partial (…)`, `missing — …`, `yes (Tableau)`) classifies on the leading word; the header and `---` separator rows are excluded; text with no `## ATS Keyword Coverage` section returns `[]`; a following `## ` heading stops parsing.
  - `collect_gaps` — with a tmp dir of two `Chris Twellman - *.md` files (one with a section, one without), returns the gaps from the first with `source` = the stripped job name, and ignores the section-less file.
- **Live run:** with `ANTHROPIC_API_KEY` present, run `./venv/bin/python aspirations.py` against the real `Customized Resumes/`; confirm `Aspiration.md` is written with the three category sections, clusters ranked by recurrence, Acquire/Strengthen tags, and that a term appearing as `missing` in multiple postings (e.g. consulting) surfaces as a high-ranked cluster.

---

## Out of scope (YAGNI)

No "interest" flag (every scanned posting counts); no history/trend tracking across runs; no dedup against an "already learning" list; no non-LLM fallback. Regenerate on demand. R2 is the last roadmap item from the original save-posting spec.
