from organize_files import scan_and_group, main

def test_opt_in_casefold_and_exclusion_priority(tmp_path):
    a=tmp_path/'Report.TXT';a.write_text('a')
    b=tmp_path/'private.TXT';b.write_text('b')
    assert not scan_and_group(tmp_path,include_patterns=['*.txt'])
    selected=scan_and_group(tmp_path,include_patterns=['*.txt'],exclude_patterns=['PRIVATE.*'],ignore_pattern_case=True)
    assert selected['Documents']==[a]
    assert main([str(tmp_path),'--dry-run','--include-pattern','*.txt','--ignore-pattern-case'])==0
    assert a.exists() and b.exists()


def test_expanding_case_characters_preserve_glob_semantics(tmp_path):
    sharp=tmp_path/'ß.txt';sharp.write_text('a')
    s=tmp_path/'s.txt';s.write_text('b')
    selected=scan_and_group(tmp_path,exclude_patterns=['[ß].txt'],ignore_pattern_case=True)
    assert selected['Documents']==[s]
    selected=scan_and_group(tmp_path,include_patterns=['?.TXT'],ignore_pattern_case=True)
    assert set(selected['Documents'])=={sharp,s}
