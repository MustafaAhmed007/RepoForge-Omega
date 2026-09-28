from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CIWorkflow:
    path: str
    provider: str
    language: str
    commands: list[str]


def discover_ci(repo: Path) -> list[CIWorkflow]:
    out: list[CIWorkflow] = []
    directory = repo / ".github" / "workflows"
    if not directory.is_dir():
        return out
    tokens = ("pytest", "npm ", "pnpm ", "yarn ", "ruff", "go test", "cargo test", "dotnet test", "mvn ")
    for path in sorted(directory.glob("*.y*ml")):
        content = path.read_text(encoding="utf-8", errors="replace")
        commands = [
            line.strip()[2:].strip()
            for line in content.splitlines()
            if line.strip().startswith("- ") and any(token in line for token in tokens)
        ]
        out.append(CIWorkflow(str(path.relative_to(repo)).replace("\\", "/"), "github-actions", "multi", commands))
    return out


def workflow_commands(repo: Path) -> list[str]:
    return sorted({command for workflow in discover_ci(repo) for command in workflow.commands})
