from organize_files import categorize, safe_move, scan_and_group


def test_hidden_files_are_excluded_by_default(tmp_path):
    visible = tmp_path / "notes.txt"
    hidden = tmp_path / ".private.txt"
    visible.write_text("visible", encoding="utf-8")
    hidden.write_text("hidden", encoding="utf-8")

    groups = scan_and_group(tmp_path)

    assert groups["Documents"] == [visible]


def test_include_hidden_flag_adds_hidden_files(tmp_path):
    visible = tmp_path / "notes.txt"
    hidden = tmp_path / ".private.txt"
    visible.write_text("visible", encoding="utf-8")
    hidden.write_text("hidden", encoding="utf-8")

    groups = scan_and_group(tmp_path, include_hidden=True)

    assert set(groups["Documents"]) == {visible, hidden}


def test_dry_run_does_not_create_destination_folder(tmp_path, capsys):
    source = tmp_path / "photo.png"
    destination = tmp_path / "Images"
    source.write_bytes(b"image")

    safe_move(source, destination, dry_run=True)

    assert source.exists()
    assert not destination.exists()
    assert "[dry-run]" in capsys.readouterr().out


def test_safe_move_uses_a_suffix_when_name_collides(tmp_path):
    source = tmp_path / "report.pdf"
    destination = tmp_path / "PDFs"
    destination.mkdir()
    (destination / "report.pdf").write_text("existing", encoding="utf-8")
    source.write_text("new", encoding="utf-8")

    safe_move(source, destination)

    assert not source.exists()
    assert (destination / "report(1).pdf").read_text(encoding="utf-8") == "new"
    assert (destination / "report.pdf").read_text(encoding="utf-8") == "existing"


def test_categorize_is_case_insensitive(tmp_path):
    assert categorize(tmp_path / "PHOTO.PNG") == "Images"


def test_cli_rejects_a_missing_target_directory(tmp_path, monkeypatch, capsys):
    from organize_files import main

    missing = tmp_path / "does-not-exist"
    monkeypatch.setattr("sys.argv", ["organize_files.py", str(missing)])

    import pytest

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
    assert "target directory does not exist" in capsys.readouterr().err

def test_version_flag_prints_version_and_exits(monkeypatch, capsys):
    import pytest
    from organize_files import main

    monkeypatch.setattr("sys.argv", ["organize_files.py", "--version"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == "Python File Organizer 1.0.0"



def test_symbolic_links_are_excluded_from_scans(tmp_path):
    target = tmp_path / "actual.txt"
    target.write_text("content", encoding="utf-8")
    link = tmp_path / "linked.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("Symbolic links are not supported on this platform")

    groups = scan_and_group(tmp_path)

    assert target in groups["Documents"]
    assert all(link not in files for files in groups.values())
