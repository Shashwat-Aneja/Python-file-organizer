from organize_files import main

def test_byte_budget_fails_before_any_move_or_report_replacement(tmp_path):
    target=tmp_path/'source';target.mkdir();(target/'a.txt').write_bytes(b'123');(target/'b.txt').write_bytes(b'456')
    report=tmp_path/'report.json';report.write_text('keep')
    assert main([str(target),'--max-total-bytes','5','--report-json',str(report)])==1
    assert sorted(p.name for p in target.iterdir())==['a.txt','b.txt'] and report.read_text()=='keep'
    assert main([str(target),'--max-total-bytes','6'])==0
    assert (target/'Documents'/'a.txt').exists() and (target/'Documents'/'b.txt').exists()
