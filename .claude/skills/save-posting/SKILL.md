---
name: save-posting
description: Use when the user pastes a job-posting URL or says "save this posting" — reads the posting from their logged-in Chrome and writes a clean, metadata-tagged file into Postings/.
---

# Save Posting

Save a job posting from a URL into `Postings/` as a frontmatter-tagged `.txt`
file that `Scanner.py` can consume. Built for LinkedIn / Workday / iCIMS /
company career pages, which are JavaScript-rendered and login-gated — so read
them through the user's already-logged-in Chrome, not an HTTP fetch.

## Trigger

- The user pastes a job URL, or
- The user says "save this posting" while a job tab is open.

## Steps

1. **Load browser tools** (if deferred): one `ToolSearch` call for
   `tabs_context_mcp, tabs_create_mcp, navigate, read_page, get_page_text`.
2. **Find or open the posting.** Call `tabs_context_mcp`. If the posting tab
   is already open, use it; otherwise open the URL in a new tab.
3. **Read the rendered page** with `get_page_text` (fall back to `read_page`).
4. **Detect a wall.** If the text is blank, a login/"sign in" page, or an
   anti-bot challenge, STOP and ask the user to log in or navigate to the
   posting in Chrome, then retry. Offer: they can paste the description text
   directly instead.
5. **Extract fields** from the rendered text:
   - `title`, `company`, `location` (use `Remote` when stated; leave empty if
     genuinely absent — never guess), and the **full job-description body**.
   - `source_url` = the posting's URL.
   - Strip boilerplate: site nav, cookie/consent banners, "Apply now" / "Save
     job" controls, related-jobs sidebars, and footers.
6. **Write the file.** Write the JSON payload to a scratchpad file (avoids
   quoting problems with long bodies), then pipe it to the writer:

       python3 save_posting.py < /path/to/payload.json

   The payload is `{"meta": {"title": ..., "company": ..., "location": ...,
   "source_url": ...}, "body": "<cleaned description>"}`.
7. **Handle duplicates.** If the writer returns `{"status": "exists", ...}`,
   tell the user a posting with that name already exists and ask whether to
   overwrite. Only on a yes, re-run with `"force": true` in the payload.
8. **Confirm and stop.** Report `title / company / location / saved path`. Do
   NOT auto-run tailoring — saving is a deliberate, standalone step.

## Notes

- The writer defaults `date_scraped` to today and owns filename sanitizing —
  do not construct the path yourself.
- The repo `venv` is currently broken; `save_posting.py` is standard-library
  only, so run it with `python3`.
- If one page lists multiple postings, ask which one (or use the one in focus).
- For a posting delivered as a PDF, read it if reachable; otherwise ask the
  user to paste the text.
