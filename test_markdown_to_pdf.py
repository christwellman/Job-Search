import unittest

import markdown_to_pdf as mp


class TestBuildHtml(unittest.TestCase):
    def test_renders_markdown_and_links_css(self):
        html = mp.build_html("# Hi\n\nsome text", "file:///x/Resume.css")
        self.assertTrue(html.startswith("<html>"))
        self.assertIn("<h1>Hi</h1>", html)
        self.assertIn('href="file:///x/Resume.css"', html)
        self.assertIn("some text", html)


if __name__ == "__main__":
    unittest.main()
