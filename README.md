# Job-Search

Tools to tailor a resume to specific job postings using Claude.

## Setup

    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt

Add your Anthropic key to `.env`:

    ANTHROPIC_API_KEY=sk-ant-...

## Saving postings

Paste a job URL to Claude Code (or say "save this posting" with the tab open).
Claude reads it from your logged-in Chrome — handling LinkedIn / Workday /
company pages that a plain scraper can't — and writes
`Postings/<Title> - <Company>.txt` with a metadata header:

    ---
    title: ...
    company: ...
    location: ...
    source_url: ...
    date_scraped: YYYY-MM-DD
    ---

## Tailoring

Put your resume in `Resume.md`, then:

    ./venv/bin/python Scanner.py

For each posting in `Postings/`, this writes a summary and a tailored resume
(with an ATS keyword-coverage checklist) to `Customized Resumes/`. Summaries use
Claude Haiku; tailoring uses Claude Sonnet. Postings without a metadata header
(older files) are still processed.

## PDF

    ./venv/bin/python markdown_to_pdf.py "Customized Resumes/<file>.md"

Writes a PDF beside the source file, styled with `Resume.css`.
