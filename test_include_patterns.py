import pytest
from organize_files import scan_and_group, main

def test_patterns_compose_with_recursive_and_extension_filters(tmp_path):
    for name in ['reports/a.csv', 'reports/b.json', 'other/a.csv', '.hidden/a.csv', 'Data/old.csv']:
        p = tmp_path / name; p.parent.mkdir(exist_ok=True); p.write_text('x')
    groups = scan_and_group(tmp_path, recursive=True, include_patterns=['reports/*'], exclude_extensions=['json'])
    assert [p.relative_to(tmp_path).as_posix() for paths in groups.values() for p in paths] == ['reports/a.csv']

def test_invalid_pattern_fails_before_moving(tmp_path):
    p = tmp_path / 'a.txt'; p.write_text('x')
    with pytest.raises(SystemExit):
        main([str(tmp_path), '--include-pattern', ' '])
    assert p.exists()
