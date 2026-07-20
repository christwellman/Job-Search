import datetime
import json
import tempfile
import unittest
from pathlib import Path

import save_posting as sp


class TestSanitizeFilename(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            sp.sanitize_filename("Senior BizOps Manager", "Netflix"),
            "Senior BizOps Manager - Netflix.txt",
        )

    def test_illegal_chars_become_spaces(self):
        # slash, colon, pipe, etc. are replaced with a space, not deleted
        self.assertEqual(
            sp.sanitize_filename("Manager, Data/Analytics", "1Password"),
            "Manager, Data Analytics - 1Password.txt",
        )

    def test_whitespace_collapsed_and_trimmed(self):
        self.assertEqual(
            sp.sanitize_filename("  Lead   Analyst  ", "  Acme  "),
            "Lead Analyst - Acme.txt",
        )


class TestRenderPosting(unittest.TestCase):
    def test_full_frontmatter_and_body(self):
        meta = {
            "title": "BizOps Lead",
            "company": "OpenAI",
            "location": "Remote (US)",
            "source_url": "https://example.com/job/1",
            "date_scraped": "2026-07-20",
        }
        out = sp.render_posting(meta, "  Do great work.  ")
        expected = (
            "---\n"
            "title: BizOps Lead\n"
            "company: OpenAI\n"
            "location: Remote (US)\n"
            "source_url: https://example.com/job/1\n"
            "date_scraped: 2026-07-20\n"
            "---\n"
            "\n"
            "Do great work.\n"
        )
        self.assertEqual(out, expected)

    def test_missing_fields_are_empty_never_missing(self):
        out = sp.render_posting({"title": "X", "company": "Y"}, "body")
        self.assertIn("location: \n", out)
        self.assertIn("source_url: \n", out)
        self.assertIn("date_scraped: \n", out)


class TestRun(unittest.TestCase):
    def _data(self, **over):
        d = {
            "meta": {"title": "BizOps Lead", "company": "OpenAI"},
            "body": "body text",
            "force": False,
        }
        d.update(over)
        return d

    def test_writes_file_and_defaults_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = sp.run(self._data(), Path(tmp))
            self.assertEqual(result["status"], "saved")
            path = Path(result["path"])
            self.assertTrue(path.exists())
            text = path.read_text()
            self.assertIn(f"date_scraped: {datetime.date.today().isoformat()}\n", text)

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = sp.run(self._data(), Path(tmp))
            Path(first["path"]).write_text("ORIGINAL")
            result = sp.run(self._data(), Path(tmp))
            self.assertEqual(result["status"], "exists")
            self.assertEqual(Path(result["path"]).read_text(), "ORIGINAL")

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = sp.run(self._data(), Path(tmp))
            Path(first["path"]).write_text("ORIGINAL")
            result = sp.run(self._data(force=True), Path(tmp))
            self.assertEqual(result["status"], "saved")
            self.assertNotEqual(Path(result["path"]).read_text(), "ORIGINAL")


if __name__ == "__main__":
    unittest.main()
