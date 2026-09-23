from __future__ import annotations

from dataclasses import dataclass

from .autopilot import Autopilot
from .config import ForgeConfig
from .goals import GoalRunner
from .hooks import HookBus
from .models import ReleaseStatus
from .pipeline import Pipeline
from .tasks import TaskStatus


@dataclass(slots=True)
class OrchestrationResult:
    goal_id: str
    goal_status: str
    verification_status: str
    readiness: object
    iterations: int
    patched: list[str]


class Orchestrator:
    """Unified control plane around the deterministic engineering core."""

    def __init__(self, config: ForgeConfig) -> None:
        self.config = config
        self.hooks = HookBus()

    def run(self) -> OrchestrationResult:
        goal = GoalRunner(self.config.repo, self.config.max_goal_iterations)
        goal.start()
        self.hooks.emit("session_start", goal=goal.goal.id, repo=str(self.config.repo))

        _, findings, _ = Pipeline(self.config).inspect()
        goal.record_task("discover", TaskStatus.PASSED, [f"{len(findings)} findings collected"])
        goal.record_task("diagnose", TaskStatus.PASSED)
        self.hooks.emit("after_task", task="diagnose", findings=len(findings))

        result = Autopilot(self.config).run()
        for task_id in ("plan", "repair"):
            goal.record_task(task_id, TaskStatus.PASSED, [f"autopilot proposals={result.proposals}"])

        passed = result.verification_status == ReleaseStatus.VERIFIED.value
        for task_id in ("verify", "review", "security"):
            goal.record_task(task_id, TaskStatus.PASSED if passed else TaskStatus.FAILED)
        goal.record_task("release", TaskStatus.PASSED if result.readiness.ready else TaskStatus.FAILED)

        final = goal.finalize(
            passed and result.readiness.ready,
            [] if passed else [result.verification_status],
        )
        self.hooks.emit("after_verify", status=result.verification_status)
        self.hooks.emit("session_end", goal=final.id, status=final.status.value)
        return OrchestrationResult(
            final.id, final.status.value, result.verification_status,
            result.readiness, final.iteration, result.patched,
        )
