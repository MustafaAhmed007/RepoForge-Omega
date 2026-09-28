from __future__ import annotations

import uuid
from pathlib import Path

from .adapters import discover_checks
from .fingerprint import detect
from .models import CheckResult, GateStatus, ReleaseStatus, RepositoryFingerprint, VerificationReport
from .runner import run_check


class RepoForge:
    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()

    def fingerprint(self) -> RepositoryFingerprint:
        return detect(self.repo)

    def discover_checks(self) -> list[tuple[str, list[str]]]:
        return [(check.name, check.command) for check in discover_checks(self.repo)]

    def verify(self, timeout_s: int = 120) -> VerificationReport:
        fp = self.fingerprint()
        checks = [run_check(name, command, self.repo, timeout_s) for name, command in self.discover_checks()]
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
        blockers = [c.name for c in checks if c.status in {GateStatus.FAIL, GateStatus.BLOCKED}]
        if any(c.status == GateStatus.BLOCKED for c in checks):
            status = ReleaseStatus.BLOCKED
        elif blockers:
            status = ReleaseStatus.NOT_VERIFIED
        else:
            status = ReleaseStatus.VERIFIED
        recommendations: list[str] = []
        if not fp.test_systems:
            recommendations.append("Add deterministic tests appropriate to the detected application.")
        if fp.runtime.get("python_source") == "repoforge-runtime":
            recommendations.append(
                "No target Python virtual environment was detected; verification used RepoForge's interpreter."
            )
        return VerificationReport(fp, checks, status, blockers, recommendations, uuid.uuid4().hex)
