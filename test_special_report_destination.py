import os,stat
import pytest
from organize_files import main
@pytest.mark.skipif(not hasattr(os,'mkfifo'),reason='FIFO support required')
def test_fifo_audit_destination_is_not_replaced_and_files_are_not_moved(tmp_path):
    report=tmp_path/'audit.json';os.mkfifo(report)
    source=tmp_path/'note.txt';source.write_text('keep')
    assert main([str(tmp_path),'--report-json',str(report)])==1
    assert stat.S_ISFIFO(report.stat().st_mode)
    assert source.read_text()=='keep' and not (tmp_path/'Documents').exists()
