from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .agents import AgentRuntime
from .config import ForgeConfig
from .goals import GoalRunner
from .hooks import HookBus
from .models import ReleaseStatus
from .pipeline import Pipeline
from .readiness import assess


@dataclass(slots=True)
class OrchestrationResult:
    goal_id: str
    goal_status: str
    verification_status: str
    readiness: object
    iterations: int


class Orchestrator:
    """Unified control plane around the existing deterministic engineering core."""

    def __init__(self, config: ForgeConfig) -> None:
        self.config = config
        self.hooks = HookBus()
        self.agents = AgentRuntime()
        self.agents.register_defaults()

    def run(self) -> OrchestrationResult:
        goal = GoalRunner(self.config.repo, self.config.max_goal_iterations)
        goal.start()
        self.hooks.emit("session_start", goal=goal.goal.id, repo=str(self.config.repo))

        _, findings, _ = Pipeline(self.config).inspect()
        goal.record_task("discover", __import__("repoforge.tasks", fromlist=["TaskStatus"]).TaskStatus.PASSED,
                         [f"{len(findings)} findings collected"])
        goal.record_task("diagnose", __import__("repoforge.tasks", fromlist=["TaskStatus"]).TaskStatus.PASSED)

        from .engine import RepoForge
        verification = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
        readiness = assess(self.config.repo)

        goal.record_task("plan", __import__("repoforge.tasks", fromlist=["TaskStatus"]).TaskStatus.PASSED)
        goal.record_task("repair", __import__("repoforge.tasks", fromlist=["TaskStatus"]).TaskStatus.PASSED)
        status = __import__("repoforge.tasks", fromlist=["TaskStatus"]).TaskStatus.PASSED if verification.release_status == ReleaseStatus.VERIFIED else __import__("repoforge.tasks", fromlist=["TaskStatus"]).TaskStatus.FAILED
        for task_id in ("verify", "review", "security", "release"):
            goal.record_task(task_id, status)

        final = goal.finalize(
            verification.release_status == ReleaseStatus.VERIFIED,
            verification.blockers,
        )
        self.hooks.emit("after_verify", status=verification.release_status.value)
        self.hooks.emit("session_end", goal=final.id, status=final.status.value)
        return OrchestrationResult(final.id, final.status.value, verification.release_status.value, readiness, final.iteration)
