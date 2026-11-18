import os
from pathlib import Path
from organize_files import scan_and_group


def test_recursive_scan_never_enters_excluded_hidden_or_output_directories(tmp_path, monkeypatch):
    for name in ("build", ".git", "Documents"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "private.txt").write_text("leave untouched")
    (tmp_path / "notes.txt").write_text("notes")
    original = os.scandir
    def guarded(path):
        assert Path(path).name not in {"build", ".git", "Documents"}
        return original(path)
    monkeypatch.setattr(os, "scandir", guarded)
    groups = scan_and_group(tmp_path, recursive=True, exclude_directories=["build"])
    assert [p.name for p in groups["Documents"]] == ["notes.txt"]
