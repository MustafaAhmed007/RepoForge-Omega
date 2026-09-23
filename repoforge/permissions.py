from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PermissionPolicy:
    allow_write: bool = False
    allow_network: bool = False
    allow_install: bool = False
    allow_browser: bool = False
    allow_process_spawn: bool = True
    max_files_changed: int = 25

    def authorize_write(self, repo: Path, path: Path) -> None:
        if not self.allow_write:
            raise PermissionError("Repository writes are disabled by policy")
        root = repo.resolve()
        target = path.resolve()
        if root not in target.parents and target != root:
            raise PermissionError("Path escapes repository boundary")

    def authorize_network(self) -> None:
        if not self.allow_network:
            raise PermissionError("Network access is disabled by policy")

    def authorize_install(self) -> None:
        if not self.allow_install:
            raise PermissionError("Dependency installation is disabled by policy")

    def authorize_browser(self) -> None:
        if not self.allow_browser:
            raise PermissionError("Browser automation is disabled by policy")
