import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from tqdm import tqdm

from postings import parse_posting

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")

SUMMARY_MODEL = "claude-haiku-4-5"
TAILOR_MODEL = "claude-sonnet-5"
REFERENCE_DIR = SCRIPT_DIR / "Reference"

_client = None


def get_client() -> anthropic.Anthropic:
    """Construct the Anthropic client lazily so importing this module needs no key."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _read_reference(name: str) -> str:
    try:
        return (REFERENCE_DIR / name).read_text(encoding="utf-8")
    except OSError:
        logging.warning(f"Reference file not found: {name}")
        return ""


ACTION_WORDS = _read_reference("Action words")
RESUME_STATEMENTS = _read_reference("Resume Statements.md")


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def _posting_text(meta: dict, body: str) -> str:
    if not meta:
        return body
    header = "\n".join(f"{k}: {v}" for k, v in meta.items() if v)
    return f"{header}\n\n{body}"


def summarize_job_posting(meta: dict, body: str):
    try:
        response = get_client().messages.create(
            model=SUMMARY_MODEL,
            max_tokens=1024,
            system="You are a career placement specialist who finds great opportunities for skilled candidates.",
            messages=[{
                "role": "user",
                "content": (
                    "Summarize this job posting as a concise, scannable bullet list. Include: "
                    "the exact job title; the company; the location (or 'Remote'); 3-5 key "
                    "responsibilities; the required qualifications and experience; and 1-2 "
                    "compelling aspects of the role. Focus on the most relevant details.\n\n"
                    f"{_posting_text(meta, body)}"
                ),
            }],
        )
        return _text(response)
    except Exception as e:
        logging.error(f"Error summarizing job posting: {e}")
        return None


def tailor_resume(resume: str, meta: dict, body: str):
    try:
        response = get_client().messages.create(
            model=TAILOR_MODEL,
            max_tokens=8000,
            system=(
                "You are an expert resume writer and ATS specialist. You rewrite resumes to "
                "match a target job posting while staying strictly truthful."
            ),
            messages=[{
                "role": "user",
                "content": (
                    "Rewrite my resume to target the job posting below.\n\n"
                    "Rules:\n"
                    "- Position my experience as a solution to the posting's needs.\n"
                    "- Reuse the posting's exact keywords, terms, and phrasing where they honestly apply.\n"
                    "- Keep it concise, active voice, and quantify impact where the original supports it.\n"
                    "- Never fabricate experience, skills, employers, titles, or dates. Only reframe what is in my resume.\n"
                    "- Output the full tailored resume in Markdown.\n"
                    "- End with a section '## ATS Keyword Coverage' listing the posting's key terms "
                    "and, for each, whether it is now reflected in the resume (yes / partial / missing).\n\n"
                    "You may draw phrasing from these references, but do not copy any claim my resume "
                    "does not support:\n"
                    f"<action_words>\n{ACTION_WORDS}\n</action_words>\n"
                    f"<resume_statements>\n{RESUME_STATEMENTS}\n</resume_statements>\n\n"
                    f"<resume>\n{resume}\n</resume>\n\n"
                    f"<job_posting>\n{_posting_text(meta, body)}\n</job_posting>"
                ),
            }],
        )
        return _text(response)
    except Exception as e:
        logging.error(f"Error tailoring resume: {e}")
        return None


def process_job_posting(filename, input_folder, output_folder, resume_content):
    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, f"summary_{filename}")
    tailored_resume_path = os.path.join(
        output_folder, f"Chris Twellman - {filename.replace('.txt', '.md')}"
    )
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            raw = f.read()
        if not raw.strip():
            logging.warning(f"Job posting content is empty for file: {filename}")
            return
        meta, body = parse_posting(raw)

        summary = summarize_job_posting(meta, body)
        if not summary:
            logging.warning(f"Skipped (summary failed): {filename}")
            return
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        logging.info(f"Processed: {filename}")

        tailored = tailor_resume(resume_content, meta, body)
        if tailored:
            with open(tailored_resume_path, "w", encoding="utf-8") as f:
                f.write(tailored)
            logging.info(f"Tailored resume created for: {filename}")
        else:
            logging.warning(f"Skipped (tailoring failed): {filename}")
    except Exception as e:
        logging.error(f"Error processing file {filename}: {e}")


def process_job_postings(input_folder, output_folder, resume_path):
    if not os.getenv("ANTHROPIC_API_KEY"):
        logging.error("Missing environment variable: ANTHROPIC_API_KEY (add it to .env)")
        raise SystemExit(1)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    processed = set(f[8:] for f in os.listdir(output_folder) if f.startswith("summary_"))
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_content = f.read()
    if not resume_content.strip():
        logging.error("Resume content is empty.")
        return

    files_to_process = [
        fn for fn in os.listdir(input_folder)
        if fn.endswith(".txt") and fn not in processed
    ]
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(process_job_posting, fn, input_folder, output_folder, resume_content)
            for fn in files_to_process
        ]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Processing job postings"):
            pass


if __name__ == "__main__":
    process_job_postings("Postings", "Customized Resumes", str(SCRIPT_DIR / "Resume.md"))
