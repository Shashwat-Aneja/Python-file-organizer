import os,pytest
import organize_files as app

def test_inclusive_modification_age_window(tmp_path,monkeypatch):
    paths=[]
    for name,stamp in [('old',1),('middle',50),('new',90)]:
        p=tmp_path/(name+'.txt');p.write_text('x');os.utime(p,(stamp,stamp));paths.append(p)
    monkeypatch.setattr(app.time,'time',lambda:100)
    assert app.scan_and_group(tmp_path,min_age_seconds=20,max_age_seconds=50)['Documents']==[paths[1]]
    with pytest.raises(ValueError):app.scan_and_group(tmp_path,min_age_seconds=60,max_age_seconds=50)
