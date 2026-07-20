import datetime
import os
import tempfile
import unittest
from pathlib import Path

import stale


class TestMonthsAgo(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(stale.months_ago(datetime.date(2026, 7, 20), 6), datetime.date(2026, 1, 20))

    def test_year_wrap(self):
        self.assertEqual(stale.months_ago(datetime.date(2026, 3, 15), 6), datetime.date(2025, 9, 15))

    def test_day_clamp(self):
        self.assertEqual(stale.months_ago(datetime.date(2026, 3, 31), 1), datetime.date(2026, 2, 28))


class TestEffectiveDate(unittest.TestCase):
    def test_uses_date_scraped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.txt"
            p.write_text("---\ntitle: X\ndate_scraped: 2025-01-15\n---\n\nbody\n")
            d, src = stale.effective_date(p)
            self.assertEqual(d, datetime.date(2025, 1, 15))
            self.assertEqual(src, "date_scraped")

    def test_falls_back_to_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "y.txt"
            p.write_text("Plain posting, no header.\n")
            ts = datetime.datetime(2020, 6, 1).timestamp()
            os.utime(p, (ts, ts))
            d, src = stale.effective_date(p)
            self.assertEqual(d, datetime.date(2020, 6, 1))
            self.assertEqual(src, "mtime")


class TestDerivedPaths(unittest.TestCase):
    def test_only_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            resumes = Path(tmp)
            (resumes / "summary_Role - Co.txt").write_text("s")
            # the tailored .md is intentionally absent
            got = stale.derived_paths("Role - Co.txt", resumes)
            self.assertEqual([p.name for p in got], ["summary_Role - Co.txt"])


class TestFindStale(unittest.TestCase):
    def test_flags_old_not_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            postings = Path(tmp) / "Postings"; postings.mkdir()
            resumes = Path(tmp) / "Resumes"; resumes.mkdir()
            (postings / "Old - Co.txt").write_text("---\ntitle: Old\ndate_scraped: 2025-01-01\n---\n\nb\n")
            (postings / "New - Co.txt").write_text("---\ntitle: New\ndate_scraped: 2026-07-01\n---\n\nb\n")
            (resumes / "Chris Twellman - Old - Co.md").write_text("r")
            today = datetime.date(2026, 7, 20)
            cutoff = stale.months_ago(today, 6)  # 2026-01-20
            groups = stale.find_stale(postings, resumes, cutoff, today)
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["posting"].name, "Old - Co.txt")
            self.assertEqual([p.name for p in groups[0]["derived"]], ["Chris Twellman - Old - Co.md"])


class TestArchiveGroup(unittest.TestCase):
    def test_moves_and_skips_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            postings = Path(tmp) / "Postings"; postings.mkdir()
            archive = Path(tmp) / "Archive"; archive.mkdir()
            posting = postings / "Old - Co.txt"; posting.write_text("body")
            derived = postings / "Chris Twellman - Old - Co.md"; derived.write_text("resume")
            # pre-existing collision for the derived file
            (archive / "Chris Twellman - Old - Co.md").write_text("ORIGINAL")
            group = {"posting": posting, "derived": [derived]}
            moved = stale.archive_group(group, archive)
            # posting moved
            self.assertTrue((archive / "Old - Co.txt").exists())
            self.assertFalse(posting.exists())
            # colliding derived left untouched, source not moved
            self.assertEqual((archive / "Chris Twellman - Old - Co.md").read_text(), "ORIGINAL")
            self.assertTrue(derived.exists())
            self.assertEqual([p.name for p in moved], ["Old - Co.txt"])


if __name__ == "__main__":
    unittest.main()
