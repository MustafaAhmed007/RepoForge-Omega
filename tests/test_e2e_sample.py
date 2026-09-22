from pathlib import Path
from repoforge.pipeline import Pipeline
from repoforge.config import ForgeConfig

def test_end_to_end_sample_project(tmp_path:Path)->None:
    source=Path(__file__).parents[1]/'examples'/'sample_project'
    target=tmp_path/'sample'
    for item in source.iterdir():
        if item.is_file():
            target.mkdir(parents=True,exist_ok=True)
            (target/item.name).write_text(item.read_text(encoding='utf-8'),encoding='utf-8')
    fp,findings,proposals=Pipeline(ForgeConfig.for_repo(target)).inspect(tmp_path/'report')
    assert 'Python' in fp.languages
    assert findings
    assert proposals
