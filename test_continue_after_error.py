import json
import organize_files as app
def test_continue_moves_other_files_and_reports_failure(tmp_path,monkeypatch):
    (tmp_path/'a.txt').write_text('a');(tmp_path/'b.txt').write_text('b')
    move=app.safe_move
    def fail_first(src,*args,**kwargs):
        if src.name=='a.txt':raise OSError('denied')
        return move(src,*args,**kwargs)
    monkeypatch.setattr(app,'safe_move',fail_first)
    report=tmp_path/'audit.json'
    assert app.main([str(tmp_path),'--continue-on-error','--report-json',str(report)])==1
    assert (tmp_path/'a.txt').exists()
    assert (tmp_path/'Documents'/'b.txt').read_text()=='b'
    assert json.loads(report.read_text())['summary']=={'total':2,'planned':0,'moved':1,'failed':1}
