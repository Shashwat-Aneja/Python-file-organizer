import pytest
from organize_files import scan_and_group

@pytest.mark.parametrize('depth,expected',[(0,['root.txt']),(1,['one/child.txt','root.txt'])])
def test_depth_limit_prunes_deeper_discovery(tmp_path,depth,expected):
    for name in ['root.txt','one/child.txt','one/two/deep.txt']:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('x')
    groups=scan_and_group(tmp_path,recursive=True,max_depth=depth)
    assert sorted(p.relative_to(tmp_path).as_posix() for files in groups.values() for p in files)==expected
