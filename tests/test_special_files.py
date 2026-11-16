import os
from pathlib import Path
import pytest
from organize_files import safe_move, scan_and_group


def test_scan_ignores_fifo(tmp_path):
    fifo = tmp_path / "queue.txt"
    os.mkfifo(fifo)
    assert not scan_and_group(tmp_path)
    with pytest.raises(ValueError, match="regular file"):
        safe_move(fifo, tmp_path / "Documents")
    assert fifo.exists()


def test_direct_move_rejects_directory(tmp_path):
    source = tmp_path / "nested"
    source.mkdir()
    with pytest.raises(ValueError, match="regular file"):
        safe_move(source, tmp_path / "Others")
    assert source.is_dir()
