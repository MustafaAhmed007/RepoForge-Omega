from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

from .agents import AgentRole
from .tasks import Task, TaskGraph, TaskStatus


class GoalStatus(str, Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass(slots=True)
class Goal:
    id: str
    statement: str
    status: GoalStatus = GoalStatus.PLANNED
    iteration: int = 0
    max_iterations: int = 3
    evidence: list[str] = field(default_factory=list)


DEPLOYMENT_READY_GOAL = "make any given repository deployment-ready"


def deployment_goal(repo: Path, max_iterations: int = 3) -> Goal:
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    return Goal(
        uuid.uuid4().hex,
        f"{DEPLOYMENT_READY_GOAL}: {repo.resolve()}",
        max_iterations=max_iterations,
    )


def build_deployment_task_graph() -> TaskGraph:
    graph = TaskGraph()
    graph.add(Task("discover", "Discover repository and runtime surface", AgentRole.DISCOVER.value))
    graph.add(Task("diagnose", "Collect deterministic diagnostics", AgentRole.DIAGNOSE.value, ["discover"]))
    graph.add(Task("plan", "Build bounded repair plan", AgentRole.PLAN.value, ["diagnose"]))
    graph.add(Task("repair", "Apply approved safe repairs", AgentRole.REPAIR.value, ["plan"]))
    graph.add(Task("verify", "Run deterministic verification", AgentRole.TEST.value, ["repair"]))
    graph.add(Task("review", "Independently review evidence", AgentRole.REVIEW.value, ["verify"]))
    graph.add(Task("security", "Run security and secret gates", AgentRole.SECURITY.value, ["review"]))
    graph.add(Task("release", "Evaluate deployment readiness", AgentRole.RELEASE.value, ["security"]))
    return graph


class GoalRunner:
    """Bounded goal state machine with a durable JSON snapshot per run."""

    def __init__(self, repo: Path, max_iterations: int = 3) -> None:
        self.repo = repo.resolve()
        self.goal = deployment_goal(self.repo, max_iterations)
        self.graph = build_deployment_task_graph()
        self.state_path = self.repo / ".repoforge" / "goal.json"

    def start(self) -> Goal:
        self.goal.status = GoalStatus.RUNNING
        self.persist()
        return self.goal

    def record_task(
        self, task_id: str, status: TaskStatus, evidence: list[str] | None = None
    ) -> None:
        self.graph.mark(task_id, status, evidence or [])
        self.persist()

    def finalize(self, deterministic_verified: bool, blockers: list[str]) -> Goal:
        self.goal.iteration += 1
        self.goal.evidence.extend(blockers)
        if deterministic_verified and not blockers and self.graph.successful():
            self.goal.status = GoalStatus.VERIFIED
        elif self.goal.iteration >= self.goal.max_iterations:
            self.goal.status = GoalStatus.BLOCKED
        else:
            self.goal.status = GoalStatus.FAILED
        self.persist()
        return self.goal

    def persist(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "goal": asdict(self.goal),
            "tasks": {
                task_id: {
                    "title": task.title,
                    "role": task.role,
                    "depends_on": task.depends_on,
                    "status": task.status.value,
                    "evidence": task.evidence,
                }
                for task_id, task in self.graph.tasks.items()
            },
        }
        self.state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
