import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from organize_files import main


class MoveFailureTests(unittest.TestCase):
    def test_blocked_category_directory_returns_error_without_losing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source = target / "notes.txt"
            source.write_text("important", encoding="utf-8")
            (target / "Documents").write_text("occupied", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
                status = main([str(target)])
            self.assertEqual(status, 1)
            self.assertIn("could not move", stderr.getvalue())
            self.assertEqual(source.read_text(encoding="utf-8"), "important")
            self.assertEqual((target / "Documents").read_text(encoding="utf-8"), "occupied")


if __name__ == "__main__":
    unittest.main()
