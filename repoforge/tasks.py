from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


_SUCCESS = {TaskStatus.PASSED, TaskStatus.SKIPPED}


@dataclass(slots=True)
class Task:
    id: str
    title: str
    role: str
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    evidence: list[str] = field(default_factory=list)


class TaskGraph:
    def __init__(self, tasks: Iterable[Task] = ()) -> None:
        self.tasks: dict[str, Task] = {}
        for task in tasks:
            self.add(task)

    def add(self, task: Task) -> None:
        if task.id in self.tasks:
            raise ValueError(f"Duplicate task: {task.id}")
        if task.id in task.depends_on:
            raise ValueError("Task cannot depend on itself")
        missing = [dependency for dependency in task.depends_on if dependency not in self.tasks]
        if missing:
            raise ValueError(f"Unknown task dependencies for {task.id}: {missing}")
        self.tasks[task.id] = task

    def ready(self) -> list[Task]:
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
            and all(self.tasks[d].status in _SUCCESS for d in task.depends_on)
        ]

    def mark(self, task_id: str, status: TaskStatus, evidence: Iterable[str] = ()) -> None:
        task = self.tasks[task_id]
        task.status = status
        task.evidence.extend(evidence)

    def blocked(self) -> list[Task]:
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
            and any(
                self.tasks[d].status in {TaskStatus.FAILED, TaskStatus.BLOCKED}
                for d in task.depends_on
            )
        ]

    def complete(self) -> bool:
        return bool(self.tasks) and all(
            task.status in {
                TaskStatus.PASSED,
                TaskStatus.SKIPPED,
                TaskStatus.FAILED,
                TaskStatus.BLOCKED,
            }
            for task in self.tasks.values()
        )

    def successful(self) -> bool:
        return self.complete() and all(task.status in _SUCCESS for task in self.tasks.values())
