import organize_files as app

def test_simulated_mount_boundary_is_pruned_before_files_are_organized(tmp_path,monkeypatch):
    for name in ['mounted/private.txt','nested/public.txt']:
        p=tmp_path/name;p.parent.mkdir();p.write_text('x')
    monkeypatch.setattr(app,'same_filesystem',lambda path,device:path.name!='mounted')
    assert app.main([str(tmp_path),'--recursive','--one-file-system'])==0
    assert (tmp_path/'mounted'/'private.txt').exists()
    assert (tmp_path/'Documents'/'public.txt').exists()
