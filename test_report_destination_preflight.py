from organize_files import main
def test_directory_report_fails_before_any_move(tmp_path):
    (tmp_path/'note.txt').write_text('keep');(tmp_path/'report').mkdir()
    assert main([str(tmp_path),'--report-json',str(tmp_path/'report')])==1
    assert (tmp_path/'note.txt').read_text()=='keep'
    assert not (tmp_path/'Documents').exists()
def test_report_parent_file_fails_before_any_move(tmp_path):
    (tmp_path/'note.txt').write_text('keep');(tmp_path/'blocked').write_text('file')
    assert main([str(tmp_path),'--report-json',str(tmp_path/'blocked'/'report.json')])==1
    assert (tmp_path/'note.txt').exists()
