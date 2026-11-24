from organize_files import main

def test_exclusions_win_over_include_patterns_and_leave_inputs_untouched(tmp_path):
    for name in ['keep.csv','skip.csv','other.txt']:(tmp_path/name).write_text(name)
    assert main([str(tmp_path),'--include-pattern','*.csv','--exclude-pattern','skip*'])==0
    assert (tmp_path/'Data'/'keep.csv').exists()
    assert (tmp_path/'skip.csv').read_text()=='skip.csv' and (tmp_path/'other.txt').exists()
