import pytest
import organize_files as organizer


def test_concurrent_writer_is_preserved_and_move_retries(tmp_path, monkeypatch):
    source = tmp_path / "notes.txt"
    source.write_text("source data")
    destination = tmp_path / "Documents"
    original = organizer._move_no_replace
    calls = []
    def interleave(src, dest):
        if not calls:
            dest.write_text("concurrent data")
        calls.append(dest)
        return original(src, dest)
    monkeypatch.setattr(organizer, "_move_no_replace", interleave)
    result = organizer.safe_move(source, destination)
    assert (destination / "notes.txt").read_text() == "concurrent data"
    assert (destination / "notes(1).txt").read_text() == "source data"
    assert result["destination"].endswith("notes(1).txt")
    assert not source.exists()


def test_partial_copy_failure_preserves_source_and_cleans_destination(tmp_path, monkeypatch):
    source = tmp_path / "notes.txt"
    source.write_text("important source")
    def fail(src, out):
        out.write(b"partial")
        raise OSError("disk full")
    monkeypatch.setattr(organizer.shutil, "copyfileobj", fail)
    with pytest.raises(OSError, match="disk full"):
        organizer.safe_move(source, tmp_path / "Documents")
    assert source.read_text() == "important source"
    assert not (tmp_path / "Documents" / "notes.txt").exists()
