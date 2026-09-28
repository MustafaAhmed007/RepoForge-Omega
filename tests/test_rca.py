from pathlib import Path

from repoforge.engine import RepoForge
from repoforge.evidence import EvidenceBundle
from repoforge.rca import RootCauseAnalysisEngine


def test_rca_reports_no_failure_when_verified(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\n", encoding="utf-8"
    )
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text(
        "def test_ok(): assert True\n", encoding="utf-8"
    )
    verification = RepoForge(tmp_path).verify()
    analysis = RootCauseAnalysisEngine(tmp_path).analyze(
        verification, EvidenceBundle(verification.execution_id)
    )
    assert analysis.failure == "No failing deterministic checks."


def test_rca_traces_test_import_to_production_module(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\n", encoding="utf-8"
    )
    package = tmp_path / "sample"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "planner.py").write_text(
        "def build_plan(query):\n    return query\n", encoding="utf-8"
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_planner.py").write_text(
        "from sample.planner import build_plan\n\n"
        "def test_comparison():\n"
        "    assert build_plan('x') == 'wrong'\n",
        encoding="utf-8",
    )

    verification = RepoForge(tmp_path).verify()
    analysis = RootCauseAnalysisEngine(tmp_path).analyze(
        verification, EvidenceBundle(verification.execution_id)
    )

    assert "sample/planner.py" in analysis.affected_files
    assert any(
        hypothesis.category == "localization"
        and "sample/planner.py" in hypothesis.evidence
        for hypothesis in analysis.hypotheses
    )
