from pathlib import Path
from repoforge.engine import RepoForge
from repoforge.evidence import EvidenceBundle
from repoforge.rca import RootCauseAnalysisEngine
def test_rca_reports_no_failure_when_verified(tmp_path: Path):
    (tmp_path/"pyproject.toml").write_text("[project]\nname='x'\n",encoding="utf-8")
    (tmp_path/"main.py").write_text("print('ok')\n",encoding="utf-8")
    (tmp_path/"tests").mkdir()
    (tmp_path/"tests"/"test_ok.py").write_text("def test_ok(): assert True\n",encoding="utf-8")
    v=RepoForge(tmp_path).verify()
    r=RootCauseAnalysisEngine(tmp_path).analyze(v,EvidenceBundle(v.execution_id))
    assert r.failure=="No failing deterministic checks."
