from pathlib import Path
import pytest
from repoforge.patching import FilePatch,PatchError,SafePatcher

def test_patch_requires_expected_content(tmp_path:Path):
    target=tmp_path/'a.txt'; target.write_text('old',encoding='utf-8')
    SafePatcher(tmp_path).apply([FilePatch('a.txt','old','new')],dry_run=False)
    assert target.read_text(encoding='utf-8')=='new'
    with pytest.raises(PatchError): SafePatcher(tmp_path).apply([FilePatch('a.txt','wrong','x')],dry_run=True)
