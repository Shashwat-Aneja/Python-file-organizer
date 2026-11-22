import os,pytest
import organize_files as app
def test_age_filter_preserves_recent_files_and_selects_old_files(tmp_path,monkeypatch):
    old=tmp_path/'old.txt';old.write_text('old');recent=tmp_path/'recent.txt';recent.write_text('recent')
    os.utime(old,(90000,90000));os.utime(recent,(99999,99999))
    monkeypatch.setattr(app.time,'time',lambda:100000)
    assert app.scan_and_group(tmp_path,min_age_seconds=3600)['Documents']==[old]
@pytest.mark.parametrize('age',[float('nan'),float('inf'),-1,True])
def test_invalid_age_rejected_before_discovery(tmp_path,age):
    with pytest.raises(ValueError,match='min_age_seconds'):app.scan_and_group(tmp_path,min_age_seconds=age)
def test_cli_invalid_age_has_controlled_usage_error(tmp_path):
    with pytest.raises(SystemExit) as exc:app.main([str(tmp_path),'--older-than-days','nan'])
    assert exc.value.code==2
