import json
import tempfile
import unittest
from pathlib import Path

from organize_files import main


class FileOrganizerReportTests(unittest.TestCase):
    def test_dry_run_report_is_machine_readable_and_does_not_move_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "input"
            target.mkdir()
            source = target / "notes.txt"
            source.write_text("keep this file", encoding="utf-8")
            report = Path(directory) / "reports" / "plan.json"

            self.assertEqual(main([str(target), "--dry-run", "--report-json", str(report)]), 0)

            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(data["dry_run"])
            self.assertEqual(data["summary"]["total"], 1)
            self.assertEqual(data["summary"]["planned"], 1)
            self.assertEqual(data["actions"][0]["status"], "planned")
            self.assertTrue(source.exists())
            self.assertFalse((target / "Documents" / "notes.txt").exists())

    def test_existing_report_inside_target_is_not_moved(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            source = target / "notes.txt"
            source.write_text("move this file", encoding="utf-8")
            report = target / "report.json"
            report.write_text("old report", encoding="utf-8")

            self.assertEqual(main([str(target), "--report-json", str(report)]), 0)

            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["moved"], 1)
            self.assertTrue(report.exists())
            self.assertFalse(source.exists())
            self.assertTrue((target / "Documents" / "notes.txt").exists())


if __name__ == "__main__":
    unittest.main()
