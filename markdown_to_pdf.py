"""Convert a Markdown resume to PDF: python markdown_to_pdf.py <input.md> [out.pdf]."""
import argparse
import tempfile
from pathlib import Path

import markdown
from weasyprint import HTML

SCRIPT_DIR = Path(__file__).resolve().parent
CSS_PATH = SCRIPT_DIR / "Resume.css"


def build_html(md_text: str, css_href: str) -> str:
    body = markdown.markdown(md_text)
    return (
        f'<html><head><link rel="stylesheet" type="text/css" href="{css_href}">'
        f"</head><body>{body}</body></html>"
    )


def convert(input_path: Path, output_path: Path) -> Path:
    md_text = input_path.read_text(encoding="utf-8")
    html = build_html(md_text, CSS_PATH.as_uri())
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(html)
        tmp_path = tmp.name
    try:
        HTML(tmp_path).write_pdf(str(output_path))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Markdown resume to PDF.")
    parser.add_argument("input", help="Path to the Markdown resume")
    parser.add_argument("output", nargs="?", help="Output PDF (defaults to <input>.pdf)")
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".pdf")
    convert(input_path, output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
