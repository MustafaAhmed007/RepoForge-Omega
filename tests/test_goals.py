from pathlib import Path
import json

from repoforge.goals import GoalRunner
from repoforge.models import ReleaseStatus
from repoforge.tasks import TaskStatus


def test_deployment_goal_verifies_only_with_evidence(tmp_path: Path) -> None:
    runner = GoalRunner(tmp_path)
    runner.start()
    for task_id in ("discover", "diagnose", "plan", "repair", "verify", "review", "security", "release"):
        runner.record_task(task_id, TaskStatus.PASSED)
    result = runner.finalize(True, [])
    assert result.statement.startswith("make any given repository deployment-ready")
    assert result.status.value == "VERIFIED"
    state = json.loads((tmp_path / ".repoforge" / "goal.json").read_text(encoding="utf-8"))
    assert state["goal"]["status"] == "VERIFIED"


def test_blockers_prevent_verification(tmp_path: Path) -> None:
    runner = GoalRunner(tmp_path, max_iterations=1)
    runner.start()
    for task_id in ("discover", "diagnose", "plan", "repair", "verify", "review", "security", "release"):
        runner.record_task(task_id, TaskStatus.PASSED)
    result = runner.finalize(False, [ReleaseStatus.BLOCKED.value])
    assert result.status.value == "BLOCKED"


def test_invalid_iteration_budget_is_rejected(tmp_path: Path) -> None:
    try:
        GoalRunner(tmp_path, max_iterations=0)
    except ValueError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("expected invalid iteration budget to fail")
