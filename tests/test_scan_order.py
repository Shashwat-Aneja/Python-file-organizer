from pathlib import Path

from organize_files import scan_and_group


def test_non_recursive_scan_order_is_casefolded_and_stable(tmp_path):
    (tmp_path / "z.txt").write_text("z", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "A.txt").write_text("upper", encoding="utf-8")

    groups = scan_and_group(tmp_path)

    assert [path.name for path in groups["Documents"]] == ["A.txt", "a.txt", "z.txt"]


def test_recursive_scan_order_uses_relative_paths(tmp_path):
    (tmp_path / "z-folder").mkdir()
    (tmp_path / "a-folder").mkdir()
    (tmp_path / "z-folder" / "second.txt").write_text("second", encoding="utf-8")
    (tmp_path / "a-folder" / "first.txt").write_text("first", encoding="utf-8")

    groups = scan_and_group(tmp_path, recursive=True)

    assert [
        path.relative_to(tmp_path).as_posix()
        for path in groups["Documents"]
    ] == ["a-folder/first.txt", "z-folder/second.txt"]
