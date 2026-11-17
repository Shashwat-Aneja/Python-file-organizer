from organize_files import main, scan_and_group


def test_excluded_nested_directories_remain_untouched(tmp_path):
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "generated.txt").write_text("generated")
    (tmp_path / "notes.txt").write_text("notes")
    groups = scan_and_group(tmp_path, recursive=True, exclude_directories=["build"])
    assert [p.name for p in groups["Documents"]] == ["notes.txt"]
    assert main([str(tmp_path), "--recursive", "--exclude-dir", "build"]) == 0
    assert (tmp_path / "build" / "generated.txt").read_text() == "generated"
    assert (tmp_path / "Documents" / "notes.txt").read_text() == "notes"
