from organize_files import scan_and_group
def test_recursive_scan_does_not_reprocess_case_variant_output_folder(tmp_path):
    folder=tmp_path/'documents';folder.mkdir();(folder/'note.txt').write_text('keep')
    (tmp_path/'new.txt').write_text('new')
    groups=scan_and_group(tmp_path,recursive=True)
    assert groups['Documents']==[tmp_path/'new.txt']
