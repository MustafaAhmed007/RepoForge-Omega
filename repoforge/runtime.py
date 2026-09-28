from __future__ import annotations

from pathlib import Path
import sys


def _existing(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def discover_python(repo: Path) -> tuple[list[str], str]:
    """Return the safest Python command available for the target repository."""
    repo = repo.resolve()
    candidates = [
        repo / ".venv" / "Scripts" / "python.exe",
        repo / "venv" / "Scripts" / "python.exe",
        repo / ".venv" / "bin" / "python",
        repo / "venv" / "bin" / "python",
    ]
    target = _existing(candidates)
    if target is not None:
        return [str(target)], "target-venv"

    return [sys.executable], "repoforge-runtime"


def discover_node_runner(repo: Path) -> tuple[str, str]:
    """Choose the repository's declared package-manager runner."""
    repo = repo.resolve()
    if (repo / "pnpm-lock.yaml").exists():
        return "pnpm", "pnpm-lock"
    if (repo / "yarn.lock").exists():
        return "yarn", "yarn-lock"
    if (repo / "package-lock.json").exists():
        return "npm", "package-lock"
    return "npm", "default"


def discover_runtime(repo: Path) -> dict[str, str]:
    python, python_source = discover_python(repo)
    node, node_source = discover_node_runner(repo)
    return {
        "python_executable": python[0],
        "python_source": python_source,
        "node_runner": node,
        "node_source": node_source,
    }
