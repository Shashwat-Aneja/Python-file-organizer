import json
import organize_files as organizer


def test_completed_moves_are_reported_when_a_later_move_fails(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    report = tmp_path / "report.json"
    original = organizer.safe_move
    def move(src, *args, **kwargs):
        if src.name == "b.txt":
            raise PermissionError("denied")
        return original(src, *args, **kwargs)
    monkeypatch.setattr(organizer, "safe_move", move)
    assert organizer.main([str(tmp_path), "--report-json", str(report)]) == 1
    data = json.loads(report.read_text())
    assert data["summary"]["moved"] == 1
    assert data["actions"][0]["source"].endswith("a.txt")
    assert (tmp_path / "b.txt").read_text() == "b"
