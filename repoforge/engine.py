from __future__ import annotations

import json
import uuid
from pathlib import Path

from .fingerprint import detect
from .models import (
    CheckResult,
    GateStatus,
    ReleaseStatus,
    RepositoryFingerprint,
    VerificationReport,
)
from .runner import run_check
from .runtime import discover_node_runner, discover_python


class RepoForge:
    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()

    def fingerprint(self) -> RepositoryFingerprint:
        return detect(self.repo)

    def discover_checks(self) -> list[tuple[str, list[str]]]:
        fp = self.fingerprint()
        checks: list[tuple[str, list[str]]] = []

        if "Python" in fp.languages:
            python_cmd, _ = discover_python(self.repo)

            if (self.repo / "tests").is_dir() or (self.repo / "pytest.ini").exists():
                checks.append(("python-tests", [*python_cmd, "-m", "pytest"]))

            if (self.repo / "pyproject.toml").exists():
                checks.append(
                    ("python-compile", [*python_cmd, "-m", "compileall", "-q", "."])
                )

            ruff_config = any(
                (self.repo / filename).exists()
                for filename in ("ruff.toml", ".ruff.toml")
            )
            if (self.repo / "pyproject.toml").exists():
                try:
                    pyproject_text = (self.repo / "pyproject.toml").read_text(
                        encoding="utf-8", errors="ignore"
                    )
                    ruff_config = ruff_config or "[tool.ruff" in pyproject_text
                except OSError:
                    pass
            if ruff_config:
                checks.append(("python-ruff", [*python_cmd, "-m", "ruff", "check", "."]))

            if (self.repo / "benchmarks" / "run.py").exists():
                checks.append(
                    ("python-benchmarks", [*python_cmd, "-m", "benchmarks.run"])
                )

        if "JavaScript" in fp.languages or "TypeScript" in fp.languages:
            pkg = self.repo / "package.json"
            if pkg.exists():
                try:
                    scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})
                except (OSError, json.JSONDecodeError):
                    scripts = {}
                runner, _ = discover_node_runner(self.repo)
                for key, cmd in (
                    ("lint", [runner, "run", "lint"]),
                    ("typecheck", [runner, "run", "typecheck"]),
                    ("test", [runner, "test"]),
                    ("build", [runner, "run", "build"]),
                ):
                    if key in scripts:
                        checks.append((f"{runner}-{key}", cmd))

        if "Go" in fp.languages and (self.repo / "go.mod").exists():
            checks += [
                ("go-test", ["go", "test", "./..."]),
                ("go-build", ["go", "build", "./..."]),
            ]
        if "Rust" in fp.languages and (self.repo / "Cargo.toml").exists():
            checks += [("cargo-check", ["cargo", "check"]), ("cargo-test", ["cargo", "test"])]

        return checks

    def verify(self, timeout_s: int = 120) -> VerificationReport:
        fp = self.fingerprint()
        checks = [
            run_check(name, command, self.repo, timeout_s)
            for name, command in self.discover_checks()
        ]
        if not checks:
            checks = [
                CheckResult(
                    "verification",
                    GateStatus.BLOCKED,
                    None,
                    0,
                    reason="no deterministic verification commands discovered",
                )
            ]

        blockers = [
            check.name
            for check in checks
            if check.status in {GateStatus.FAIL, GateStatus.BLOCKED}
        ]
        status = (
            ReleaseStatus.BLOCKED
            if any(check.status == GateStatus.BLOCKED for check in checks)
            else ReleaseStatus.NOT_VERIFIED
            if blockers
            else ReleaseStatus.VERIFIED
        )
        recommendations: list[str] = []
        if not fp.test_systems:
            recommendations.append("Add deterministic tests appropriate to the detected application.")
        if fp.runtime.get("python_source") == "repoforge-runtime":
            recommendations.append(
                "No target Python virtual environment was detected; verification used RepoForge's interpreter."
            )
        return VerificationReport(
            fp,
            checks,
            status,
            blockers,
            recommendations,
            uuid.uuid4().hex,
        )
