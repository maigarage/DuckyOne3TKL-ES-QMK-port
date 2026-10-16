# SPDX-License-Identifier: GPL-2.0-or-later
"""Existing source checkouts must never be reset or replaced to repair setup."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import sources


class SourceReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.meta = self.root / ".git"
        self.meta.mkdir()
        self.url = "https://github.com/qmk/qmk_firmware.git"
        self.sha = "1" * 40
        (self.meta / "HEAD").write_text(self.sha + "\n")
        (self.meta / "config").write_text('[remote "origin"]\n\turl = ' + self.url + '\n')
        (self.root / "local-edit.c").write_text("Do not overwrite this edit.\n")

    def test_matching_checkout_reused_without_network_or_mutation(self):
        with patch.object(sources, "git", side_effect=AssertionError("No Git subprocess expected")):
            sources.checkout(self.root, self.url, self.sha, ["quantum"])
        self.assertEqual((self.root / "local-edit.c").read_text(), "Do not overwrite this edit.\n")

    def test_wrong_revision_refused_without_reset(self):
        with patch.object(sources, "git", side_effect=AssertionError("No Git subprocess expected")):
            with self.assertRaisesRegex(RuntimeError, "Unexpected revision"):
                sources.checkout(self.root, self.url, "2" * 40, ["quantum"])
        self.assertEqual((self.meta / "HEAD").read_text().strip(), self.sha)

    def test_wrong_origin_refused_without_replacement(self):
        with patch.object(sources, "git", side_effect=AssertionError("No Git subprocess expected")):
            with self.assertRaisesRegex(RuntimeError, "Unexpected source origin"):
                sources.checkout(self.root, "https://example.org/other.git", self.sha, ["quantum"])

    def test_unborn_checkout_metadata_can_be_resumed(self):
        (self.meta / "HEAD").write_text("ref: refs/heads/master\n")
        self.assertIsNone(sources.revision_at(self.root))


if __name__ == "__main__":
    unittest.main()
