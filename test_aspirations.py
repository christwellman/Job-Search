import tempfile
import unittest
from pathlib import Path

import aspirations as a

SAMPLE = """# Resume

Some content.

## ATS Keyword Coverage

| Keyword / Term | Coverage |
|---|---|
| SQL | yes |
| Power BI | missing |
| Data storytelling | yes (examples) |
| Consulting | missing (no top-firm experience) |
| Mentoring | partial (implied, not explicit) |

## Some Other Section

| x | y |
"""


class TestParseCoverage(unittest.TestCase):
    def test_returns_only_missing_and_partial(self):
        got = a.parse_coverage(SAMPLE)
        self.assertEqual(got, [
            ("Power BI", "missing"),
            ("Consulting", "missing"),
            ("Mentoring", "partial"),
        ])

    def test_no_section_returns_empty(self):
        self.assertEqual(a.parse_coverage("# Resume\n\nno coverage table here"), [])

    def test_header_variant_and_stops_at_next_heading(self):
        text = (
            "## ATS Keyword Coverage\n"
            "| Keyword/Term | Coverage |\n"
            "|---|---|\n"
            "| Alteryx | missing |\n"
            "## Next\n"
            "| Leaked | missing |\n"
        )
        self.assertEqual(a.parse_coverage(text), [("Alteryx", "missing")])


class TestCollectGaps(unittest.TestCase):
    def test_collects_strips_prefix_and_skips_sectionless(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "Chris Twellman - Data Analyst - GitHub.md").write_text(SAMPLE)
            (d / "Chris Twellman - Old Format - Legacy.md").write_text("# Resume\n\nno table\n")
            gaps = a.collect_gaps(d)
            self.assertEqual(len(gaps), 3)
            self.assertTrue(all(g["source"] == "Data Analyst - GitHub" for g in gaps))
            self.assertEqual(
                {g["keyword"] for g in gaps}, {"Power BI", "Consulting", "Mentoring"}
            )


if __name__ == "__main__":
    unittest.main()
