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

## Housekeeping

Flag postings older than 6 months (using each posting's `date_scraped`, or its
file date for older files):

    ./venv/bin/python stale.py            # report only — changes nothing
    ./venv/bin/python stale.py --archive  # move the flagged groups into Archive/
    ./venv/bin/python stale.py --months 3 # use a different threshold

Each flagged posting is moved together with its summary and tailored resume.
It never deletes, and never overwrites a file already in `Archive/`.
