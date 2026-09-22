from dataclasses import dataclass, field
from pathlib import Path

@dataclass(slots=True)
class ForgeConfig:
    repo: Path
    timeout_seconds: int = 120
    dry_run: bool = True
    max_repair_attempts: int = 3
    excluded_dirs: set[str] = field(default_factory=lambda: {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'dist', 'build'})

    @classmethod
    def for_repo(cls, repo: Path, **kwargs: object) -> 'ForgeConfig':
        return cls(repo=repo.resolve(), **kwargs)
