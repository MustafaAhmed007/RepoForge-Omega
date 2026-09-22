from pathlib import Path
from repoforge.diagnostics import DiagnosticFinding
from repoforge.repair import RepairPlanner

def test_repair_planner_is_deterministic(tmp_path: Path):
    findings=[DiagnosticFinding('NO_TESTS','medium','missing tests','x','add tests')]
    proposals=RepairPlanner(tmp_path).propose(findings)
    assert len(proposals)==1
    assert proposals[0].action=='add_tests'
