# Job-Search
Library of Sources and Scripts to leverage LLM to help customize my resume for specific job postings.

Commit a resume.md file and add postings of interest to the postings directoty

Run the scanner.py and the LLM will tailor the resume to the job posting.

## Saving postings

To capture a job posting, paste its URL to Claude Code (or say "save this
posting" with the tab open). Claude reads it from your logged-in Chrome —
handling LinkedIn / Workday / company pages that a plain scraper can't — and
writes `Postings/<Title> - <Company>.txt` with a metadata header:

    ---
    title: ...
    company: ...
    location: ...
    source_url: ...
    date_scraped: YYYY-MM-DD
    ---

Then run `Scanner.py` as usual to summarize and tailor.

