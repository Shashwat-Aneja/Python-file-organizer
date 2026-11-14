import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from organize_files import safe_move


class MoveReportingTests(unittest.TestCase):
    def test_failed_move_does_not_claim_success(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source = target / "report.txt"
            source.write_text("preserve", encoding="utf-8")
            output = io.StringIO()
            with patch("organize_files.shutil.move", side_effect=PermissionError("denied")):
                with contextlib.redirect_stdout(output):
                    with self.assertRaises(PermissionError):
                        safe_move(source, target / "Documents")
            self.assertNotIn("Move:", output.getvalue())
            self.assertEqual(source.read_text(encoding="utf-8"), "preserve")


    def test_direct_move_rejects_symlink_source(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            real = target / "real.txt"
            real.write_text("original", encoding="utf-8")
            link = target / "linked.txt"
            link.symlink_to(real)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                safe_move(link, target / "Documents")
            self.assertTrue(link.is_symlink())
            self.assertEqual(real.read_text(encoding="utf-8"), "original")


if __name__ == "__main__":
    unittest.main()
