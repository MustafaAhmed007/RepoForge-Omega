from pathlib import Path
from repoforge.readiness import assess

def test_readiness_blocks_unknown_empty_repo(tmp_path:Path):
    result=assess(tmp_path)
    assert not result.ready
    assert 'recognized_project' in result.blockers
