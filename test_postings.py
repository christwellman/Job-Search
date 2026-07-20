import unittest

import postings as p


class TestParsePosting(unittest.TestCase):
    def test_roundtrip_full_header(self):
        meta = {
            "title": "BizOps Lead",
            "company": "OpenAI",
            "location": "Remote",
            "source_url": "https://example.com/job/1",
            "date_scraped": "2026-07-20",
        }
        text = p.render_posting(meta, "Body line one.\nBody line two.")
        got_meta, got_body = p.parse_posting(text)
        self.assertEqual(got_meta["title"], "BizOps Lead")
        self.assertEqual(got_meta["company"], "OpenAI")
        self.assertEqual(got_meta["location"], "Remote")
        self.assertEqual(got_meta["source_url"], "https://example.com/job/1")
        self.assertEqual(got_meta["date_scraped"], "2026-07-20")
        self.assertEqual(got_body, "Body line one.\nBody line two.")

    def test_no_header_returns_whole_body(self):
        text = "Just a plain posting.\nNo frontmatter here."
        meta, body = p.parse_posting(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, "Just a plain posting.\nNo frontmatter here.")

    def test_partial_header(self):
        text = "---\ntitle: Analyst\ncompany: Acme\n---\n\nDesc."
        meta, body = p.parse_posting(text)
        self.assertEqual(meta, {"title": "Analyst", "company": "Acme"})
        self.assertEqual(body, "Desc.")

    def test_empty_value_parses_as_empty_string(self):
        text = "---\ntitle: X\nlocation:\n---\n\nB"
        meta, body = p.parse_posting(text)
        self.assertEqual(meta["title"], "X")
        self.assertEqual(meta["location"], "")

    def test_unclosed_header_treated_as_body(self):
        text = "---\ntitle: X\nno closing fence"
        meta, body = p.parse_posting(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, text.strip())


if __name__ == "__main__":
    unittest.main()
