import json
import organize_files


def test_failed_move_has_machine_readable_audit_entry(tmp_path, monkeypatch):
    source = tmp_path / "notes.txt"
    source.write_text("important")
    report = tmp_path / "report.json"
    def fail(*args, **kwargs):
        raise PermissionError("read only")
    monkeypatch.setattr(organize_files, "safe_move", fail)
    assert organize_files.main([str(tmp_path), "--report-json", str(report)]) == 1
    data = json.loads(report.read_text())
    assert data["summary"]["failed"] == 1
    assert data["actions"] == [{"source": str(source), "destination": None, "status": "failed", "error": "read only"}]
    assert source.read_text() == "important"
