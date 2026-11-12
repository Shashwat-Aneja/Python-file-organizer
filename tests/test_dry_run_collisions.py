import json

from organize_files import main, safe_move


def test_dry_run_reserves_names_for_recursive_duplicate_basenames(tmp_path):
    first = tmp_path / "a" / "report.txt"
    second = tmp_path / "b" / "report.txt"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    report = tmp_path / "plan.json"

    assert main([str(tmp_path), "--recursive", "--dry-run", "--report-json", str(report)]) == 0

    data = json.loads(report.read_text(encoding="utf-8"))
    destinations = [action["destination"] for action in data["actions"]]
    assert str(tmp_path / "Documents" / "report.txt") in destinations
    assert str(tmp_path / "Documents" / "report(1).txt") in destinations
    assert len(set(destinations)) == len(destinations)
    assert first.exists() and second.exists()
    assert not (tmp_path / "Documents").exists()


def test_dry_run_reservations_respect_existing_collision_suffixes(tmp_path):
    destination = tmp_path / "Documents"
    destination.mkdir()
    (destination / "report.txt").write_text("old", encoding="utf-8")
    (destination / "report(1).txt").write_text("older", encoding="utf-8")
    source_a = tmp_path / "a" / "report.txt"
    source_b = tmp_path / "b" / "report.txt"
    source_a.parent.mkdir()
    source_b.parent.mkdir()
    source_a.write_text("a", encoding="utf-8")
    source_b.write_text("b", encoding="utf-8")
    reserved = set()

    first = safe_move(source_a, destination, dry_run=True, reserved_destinations=reserved)
    second = safe_move(source_b, destination, dry_run=True, reserved_destinations=reserved)

    assert first["destination"] == str(destination / "report(2).txt")
    assert second["destination"] == str(destination / "report(3).txt")
    assert source_a.exists() and source_b.exists()
