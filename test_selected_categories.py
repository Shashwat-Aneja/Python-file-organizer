import json
from organize_files import main
def test_only_requested_categories_are_moved_and_audited(tmp_path):
    (tmp_path/'note.txt').write_text('note');(tmp_path/'data.csv').write_text('keep')
    report=tmp_path/'audit.json'
    assert main([str(tmp_path),'--category','Documents','--report-json',str(report)])==0
    assert (tmp_path/'Documents'/'note.txt').read_text()=='note'
    assert (tmp_path/'data.csv').read_text()=='keep'
    assert json.loads(report.read_text())['summary']['moved']==1
