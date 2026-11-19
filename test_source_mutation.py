import pytest
import organize_files as app
def test_in_place_source_edits_preserve_both_files(tmp_path,monkeypatch):
    src=tmp_path/'note.txt';src.write_text('original')
    dest=tmp_path/'copy.txt';copy=app.shutil.copyfileobj
    def edit_after_copy(source,output):
        copy(source,output)
        src.write_text('original plus new content')
    monkeypatch.setattr(app.shutil,'copyfileobj',edit_after_copy)
    with pytest.raises(OSError,match='content changed'):app._move_no_replace(src,dest)
    assert src.read_text()=='original plus new content'
    assert dest.read_text()=='original'
