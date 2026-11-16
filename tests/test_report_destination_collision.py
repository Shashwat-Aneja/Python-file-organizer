import json
import pytest
from organize_files import main


@pytest.mark.parametrize("dry_run", [False, True])
def test_report_path_cannot_overwrite_moved_input(tmp_path, dry_run):
    source = tmp_path / "notes.txt"
    source.write_text("irreplaceable")
    report = tmp_path / "Documents" / "notes.txt"
    args = [str(tmp_path), "--report-json", str(report)]
    if dry_run:
        args.append("--dry-run")
    assert main(args) == 0
    action = json.loads(report.read_text())["actions"][0]
    assert action["destination"] == str(report.with_name("notes(1).txt"))
    if dry_run:
        assert source.read_text() == "irreplaceable"
    else:
        assert report.with_name("notes(1).txt").read_text() == "irreplaceable"
