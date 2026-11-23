import json
import pytest
from organize_files import main

@pytest.mark.parametrize('dry_run', [True, False])
def test_audit_bytes_reconcile_with_files(tmp_path, dry_run):
    target = tmp_path / 'source'; target.mkdir()
    (target / 'a.txt').write_bytes(b'abc')
    (target / 'b.txt').write_bytes(b'12345')
    report = tmp_path / 'report.json'
    assert main([str(target), '--include-sizes', '--report-json', str(report)] + (['--dry-run'] if dry_run else [])) == 0
    data = json.loads(report.read_text())
    status = 'planned' if dry_run else 'moved'
    assert data['summary'][status + '_bytes'] == 8
    assert sorted(action['size_bytes'] for action in data['actions']) == [3, 5]
    assert (target / 'a.txt').exists() == dry_run

@pytest.mark.parametrize('empty', [True, False])
def test_requested_byte_totals_exist_when_nothing_succeeds(tmp_path, monkeypatch, empty):
    import organize_files
    target = tmp_path / 'source';target.mkdir()
    if not empty:
        (target / 'a.txt').write_text('content')
        def fail(*args, **kwargs):raise OSError('simulated move failure')
        monkeypatch.setattr(organize_files, 'safe_move', fail)
    report = tmp_path / 'report.json'
    assert main([str(target), '--include-sizes', '--report-json', str(report)]) == (0 if empty else 1)
    data = json.loads(report.read_text())
    assert data['summary']['planned_bytes'] == data['summary']['moved_bytes'] == 0
