"""Build Aspiration.md from the ATS Keyword Coverage tables in tailored resumes.

Reads every `Customized Resumes/Chris Twellman - *.md`, collects the skills, tools,
and certifications marked `missing` or `partial`, and asks Claude to cluster,
categorize, and rank them into an aspiration/gap plan.

Usage:
    python aspirations.py
"""
import logging
import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")

RESUMES_DIR = SCRIPT_DIR / "Customized Resumes"
OUTPUT_PATH = SCRIPT_DIR / "Aspiration.md"
SYNTH_MODEL = "claude-haiku-4-5"
RESUME_PREFIX = "Chris Twellman - "

_COVERAGE_RE = re.compile(r"^\s*(yes|partial|missing)\b", re.I)
_client = None


def get_client() -> anthropic.Anthropic:
    """Construct the Anthropic client lazily so importing this module needs no key."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def parse_coverage(md_text: str) -> list[tuple[str, str]]:
    lines = md_text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("## ats keyword coverage"):
            start = i
            break
    if start is None:
        return []

    results = []
    for ln in lines[start + 1:]:
        s = ln.strip()
        if s.startswith("## "):  # next section
            break
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        keyword, coverage = cells[0], cells[1]
        m = _COVERAGE_RE.match(coverage)
        if not m:  # skips the header ("Coverage") and separator ("---") rows
            continue
        cls = m.group(1).lower()
        if cls in ("partial", "missing"):
            results.append((keyword, cls))
    return results


def collect_gaps(resumes_dir: Path) -> list[dict]:
    gaps = []
    for path in sorted(resumes_dir.glob("Chris Twellman - *.md")):
        job = path.stem
        if job.startswith(RESUME_PREFIX):
            job = job[len(RESUME_PREFIX):]
        for keyword, cls in parse_coverage(path.read_text(encoding="utf-8", errors="ignore")):
            gaps.append({"keyword": keyword, "cls": cls, "source": job})
    return gaps


def synthesize(gaps: list[dict]) -> str:
    gap_block = "\n".join(
        f"[{g['cls']}] {g['keyword']}  (from: {g['source']})" for g in gaps
    )
    response = get_client().messages.create(
        model=SYNTH_MODEL,
        max_tokens=2000,
        system=(
            "You are a career development advisor. You turn a raw list of resume gaps "
            "into a clear, prioritized development plan."
        ),
        messages=[{
            "role": "user",
            "content": (
                "Below is a list of skills, tools, certifications, and requirements that "
                "recurred across job postings I pursued, each marked 'missing' (I lack it) "
                "or 'partial' (I have it but it reads weak), with the job it came from.\n\n"
                "Produce a Markdown aspiration/gap plan:\n"
                "- Cluster synonymous or closely-related items into a single named gap.\n"
                "- Group clusters under exactly these three '## ' sections: "
                "'Certifications & Education', 'Tools & Technologies', 'Skills & Capabilities'.\n"
                "- Within each section, rank clusters by how many distinct jobs they appear in "
                "(most-recurring first) and show that count.\n"
                "- Tag each cluster 'Acquire' (mostly missing) or 'Strengthen' (mostly partial).\n"
                "- Start with a one-line intro. Output only the Markdown, no preamble.\n\n"
                f"<gaps>\n{gap_block}\n</gaps>"
            ),
        }],
    )
    return "".join(b.text for b in response.content if b.type == "text")


def main() -> None:
    gaps = collect_gaps(RESUMES_DIR)
    if not gaps:
        print(
            "No ATS Keyword Coverage sections found in Customized Resumes/. "
            "Run Scanner.py on some postings first."
        )
        return
    if not os.getenv("ANTHROPIC_API_KEY"):
        logging.error("Missing environment variable: ANTHROPIC_API_KEY (add it to .env)")
        raise SystemExit(1)

    try:
        markdown = synthesize(gaps)
    except Exception as e:
        logging.error(f"Error synthesizing aspiration file: {e}")
        raise SystemExit(1)

    OUTPUT_PATH.write_text(markdown.strip() + "\n", encoding="utf-8")
    sources = {g["source"] for g in gaps}
    print(f"{len(gaps)} gap mentions across {len(sources)} postings -> {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
