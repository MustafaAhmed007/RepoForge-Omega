from pathlib import Path
from repoforge.goals import GoalRunner
from repoforge.models import ReleaseStatus


def test_deployment_goal_verifies_only_with_evidence(tmp_path: Path) -> None:
    runner = GoalRunner(tmp_path)
    runner.start()
    result = runner.finalize(True, [])
    assert result.statement.startswith("make any given repository deployment-ready")
    assert result.status.value == "VERIFIED"


def test_blockers_prevent_verification(tmp_path: Path) -> None:
    runner = GoalRunner(tmp_path, max_iterations=1)
    runner.start()
    result = runner.finalize(False, [ReleaseStatus.BLOCKED.value])
    assert result.status.value == "BLOCKED"
