import os,subprocess,sys
import pytest
from pathlib import Path

@pytest.mark.skipif(not hasattr(os,'mkfifo') or not hasattr(os,'O_NONBLOCK'),reason='POSIX nonblocking FIFO support required')
def test_fifo_replacement_cannot_block_move_open(tmp_path):
    source=tmp_path/'source.txt';os.mkfifo(source);destination=tmp_path/'dest.txt'
    script="from pathlib import Path;from organize_files import _move_no_replace;import sys\ntry:_move_no_replace(Path(sys.argv[1]),Path(sys.argv[2]))\nexcept ValueError:print('rejected nonregular source')\nelse:raise AssertionError('FIFO was accepted')"
    result=subprocess.run([sys.executable,'-c',script,str(source),str(destination)],cwd=Path(__file__).parent,text=True,capture_output=True,timeout=3)
    assert result.returncode==0 and 'rejected nonregular source' in result.stdout
    assert source.exists() and not destination.exists()
