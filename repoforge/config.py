from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

@dataclass(slots=True)
class ForgeConfig:
    repo: Path
    timeout_seconds: int = 120
    dry_run: bool = True
    max_repair_attempts: int = 3
    max_goal_iterations: int = 3
    excluded_dirs: set[str] = field(default_factory=lambda: {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'dist', 'build'})

    @classmethod
    def for_repo(cls, repo: Path, **kwargs: object) -> 'ForgeConfig':
        options: dict[str, Any] = dict(kwargs)
        return cls(repo=repo.resolve(), **cast(Any, options))
