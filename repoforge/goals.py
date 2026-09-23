from __future__ import annotations

import uuid
from dataclasses import dataclass, field
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
    return Goal(uuid.uuid4().hex, f"{DEPLOYMENT_READY_GOAL}: {repo.resolve()}", max_iterations=max_iterations)


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
    """Goal state machine. It never upgrades a goal to VERIFIED by model opinion."""

    def __init__(self, repo: Path, max_iterations: int = 3) -> None:
        self.repo = repo.resolve()
        self.goal = deployment_goal(self.repo, max_iterations)
        self.graph = build_deployment_task_graph()

    def start(self) -> Goal:
        self.goal.status = GoalStatus.RUNNING
        return self.goal

    def record_task(self, task_id: str, status: TaskStatus, evidence: list[str] | None = None) -> None:
        self.graph.mark(task_id, status, evidence or [])

    def finalize(self, deterministic_verified: bool, blockers: list[str]) -> Goal:
        self.goal.iteration += 1
        self.goal.evidence.extend(blockers)
        if deterministic_verified and not blockers:
            self.goal.status = GoalStatus.VERIFIED
        elif self.goal.iteration >= self.goal.max_iterations:
            self.goal.status = GoalStatus.BLOCKED
        else:
            self.goal.status = GoalStatus.FAILED
        return self.goal
