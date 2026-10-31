import tempfile
import unittest
from pathlib import Path

from organize_files import scan_and_group


class FileSizeFilterTests(unittest.TestCase):
    def test_size_bounds_are_inclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "small.txt").write_bytes(b"abc")
            (target / "medium.txt").write_bytes(b"12345")
            (target / "large.txt").write_bytes(b"1234567")

            groups = scan_and_group(target, min_size_bytes=5, max_size_bytes=7)

            self.assertEqual(
                {path.name for path in groups["Documents"]},
                {"medium.txt", "large.txt"},
            )

    def test_minimum_size_excludes_smaller_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "small.txt").write_bytes(b"x")
            (target / "large.txt").write_bytes(b"longer")

            groups = scan_and_group(target, min_size_bytes=2)

            self.assertEqual([path.name for path in groups["Documents"]], ["large.txt"])

    def test_invalid_size_bounds_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with self.assertRaisesRegex(ValueError, "non-negative"):
                scan_and_group(target, min_size_bytes=-1)
            with self.assertRaisesRegex(ValueError, "cannot exceed"):
                scan_and_group(target, min_size_bytes=10, max_size_bytes=5)


if __name__ == "__main__":
    unittest.main()
