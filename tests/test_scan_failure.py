import organize_files


def test_scan_failure_is_reported_without_traceback(tmp_path, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise PermissionError("access denied")
    monkeypatch.setattr(organize_files, "scan_and_group", fail)
    assert organize_files.main([str(tmp_path)]) == 1
    assert "could not scan target directory" in capsys.readouterr().err
