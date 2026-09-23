from __future__ import annotations

from dataclasses import dataclass

from .autopilot import Autopilot
from .config import ForgeConfig
from .goals import GoalRunner
from .hooks import HookBus
from .models import ReleaseStatus
from .pipeline import Pipeline
from .readiness import assess
from .secrets import scan as scan_secrets
from .tasks import TaskStatus


@dataclass(slots=True)
class OrchestrationResult:
    goal_id: str
    goal_status: str
    verification_status: str
    readiness: object
    iterations: int
    patched: list[str]
    blockers: list[str]


class Orchestrator:
    """Unified control plane around the deterministic engineering core."""

    def __init__(self, config: ForgeConfig) -> None:
        self.config = config
        self.hooks = HookBus()

    def run(self) -> OrchestrationResult:
        goal = GoalRunner(self.config.repo, self.config.max_goal_iterations)
        goal.start()
        self.hooks.emit("session_start", goal=goal.goal.id, repo=str(self.config.repo))

        _, findings, proposals = Pipeline(self.config).inspect()
        goal.record_task("discover", TaskStatus.PASSED, ["repository fingerprint collected"])
        goal.record_task("diagnose", TaskStatus.PASSED, [f"{len(findings)} findings collected"])
        self.hooks.emit("after_task", task="diagnose", findings=len(findings))

        goal.record_task(
            "plan",
            TaskStatus.PASSED,
            [f"{len(proposals)} repair proposals generated"],
        )

        self.hooks.emit("before_task", task="repair")
        result = Autopilot(self.config).run()
        if result.rolled_back:
            goal.record_task("repair", TaskStatus.FAILED, ["repair verification failed; transaction rolled back"])
        elif result.patched:
            goal.record_task("repair", TaskStatus.PASSED, [f"{len(result.patched)} files changed"])
        else:
            goal.record_task("repair", TaskStatus.SKIPPED, ["no repository mutation required"])

        passed = result.verification_status == ReleaseStatus.VERIFIED.value
        goal.record_task(
            "verify",
            TaskStatus.PASSED if passed else TaskStatus.FAILED,
            [f"verification status={result.verification_status}"],
        )

        # Review is an independent post-run diagnostic pass, not a relabeling of verification.
        _, review_findings, _ = Pipeline(self.config).inspect()
        review_blockers = [f.code for f in review_findings if f.severity == "high"]
        review_ok = not review_blockers
        goal.record_task(
            "review",
            TaskStatus.PASSED if review_ok else TaskStatus.FAILED,
            [f"post-run findings={len(review_findings)}"],
        )

        secret_findings = scan_secrets(self.config.repo)
        security_ok = not secret_findings
        goal.record_task(
            "security",
            TaskStatus.PASSED if security_ok else TaskStatus.FAILED,
            [f"secret findings={len(secret_findings)}"],
        )

        readiness = assess(self.config.repo)
        release_ok = passed and review_ok and security_ok and readiness.ready
        goal.record_task(
            "release",
            TaskStatus.PASSED if release_ok else TaskStatus.FAILED,
            [f"readiness blockers={len(readiness.blockers)}"],
        )

        blockers = list(result.readiness.blockers)
        blockers.extend(review_blockers)
        if secret_findings:
            blockers.append(f"secrets:{len(secret_findings)}")
        if result.verification_status != ReleaseStatus.VERIFIED.value:
            blockers.append(result.verification_status)

        final = goal.finalize(release_ok, blockers)
        self.hooks.emit("after_verify", status=result.verification_status)
        self.hooks.emit("session_end", goal=final.id, status=final.status.value)
        return OrchestrationResult(
            final.id,
            final.status.value,
            result.verification_status,
            readiness,
            final.iteration,
            result.patched,
            blockers,
        )
