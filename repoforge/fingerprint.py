from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .models import RepositoryFingerprint
from .runtime import discover_runtime

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".repoforge",
    "dist",
    "build",
}
EXT = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".cs": ".NET",
    ".cpp": "C++",
    ".c": "C",
}


def _git(repo: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _ignored_dir(path: Path) -> bool:
    return any(part in IGNORED_DIRS or part.endswith(".egg-info") for part in path.parts)


def detect(repo: Path) -> RepositoryFingerprint:
    repo = repo.resolve()
    langs: set[str] = set()
    pkgs: set[str] = set()
    frameworks: set[str] = set()
    builds: set[str] = set()
    tests: set[str] = set()
    deploy: set[str] = set()
    entry: list[str] = []
    env: list[str] = []
    count = 0
    total = 0

    for p in repo.rglob("*"):
        if _ignored_dir(p) or not p.is_file():
            continue
        count += 1
        try:
            total += p.stat().st_size
        except OSError:
            pass

        if p.suffix.lower() in EXT:
            langs.add(EXT[p.suffix.lower()])

        n = p.name.lower()
        rel = str(p.relative_to(repo))
        if n == "package.json":
            pkgs.add("Node.js")
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            scripts = data.get("scripts", {})
            for key, label in {
                "next": "Next.js",
                "react": "React",
                "vue": "Vue",
                "express": "Express",
                "vite": "Vite",
                "typescript": "TypeScript",
            }.items():
                if key in deps:
                    frameworks.add(label)
            if "build" in scripts:
                builds.add("npm build")
            if "test" in scripts:
                tests.add("npm test")
        elif n in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock"}:
            pkgs.add({"package-lock.json": "npm", "pnpm-lock.yaml": "pnpm", "yarn.lock": "Yarn"}[n])
        elif n in {"pyproject.toml", "requirements.txt", "poetry.lock", "uv.lock"}:
            pkgs.add("Python")
        elif n == "pom.xml":
            pkgs.add("Maven")
            builds.add("Maven")
        elif n in {"build.gradle", "build.gradle.kts"}:
            pkgs.add("Gradle")
            builds.add("Gradle")
        elif n == "go.mod":
            pkgs.add("Go")
            builds.add("Go")
        elif n == "cargo.toml":
            pkgs.add("Cargo")
            builds.add("Cargo")
        elif n == "dockerfile":
            builds.add("Docker")
        elif n in {"vercel.json", "netlify.toml"}:
            deploy.add(n)

        if n.startswith(".env"):
            env.append(rel)

    for filename, label in {
        "pytest.ini": "pytest",
        "playwright.config.ts": "Playwright",
        "cypress.config.ts": "Cypress",
        "jest.config.js": "Jest",
        "vitest.config.ts": "Vitest",
    }.items():
        if (repo / filename).exists():
            tests.add(label)

    if (repo / "tests").is_dir() or (repo / "test").is_dir():
        if "Python" in langs:
            tests.add("pytest")

    for candidate in (
        "main.py",
        "app.py",
        "server.py",
        "src/index.ts",
        "src/index.js",
        "main.go",
        "cmd",
    ):
        if (repo / candidate).exists():
            entry.append(candidate)

    return RepositoryFingerprint(
        str(repo),
        sorted(langs),
        sorted(frameworks),
        sorted(pkgs),
        sorted(builds),
        sorted(tests),
        sorted(deploy),
        sorted(entry),
        sorted(env),
        _git(repo, "branch", "--show-current"),
        _git(repo, "rev-parse", "HEAD"),
        count,
        total,
        discover_runtime(repo),
    )
