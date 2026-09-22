from pathlib import Path
from repoforge.autopilot import Autopilot
from repoforge.config import ForgeConfig

def test_autopilot_runs_without_mutation(tmp_path:Path)->None:
    (tmp_path/'main.py').write_text('print(1)\n',encoding='utf-8')
    result=Autopilot(ForgeConfig.for_repo(tmp_path)).run()
    assert result.findings>0
    assert result.patched==[]
