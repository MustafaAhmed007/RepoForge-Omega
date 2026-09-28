from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .fingerprint import detect
from .models import CheckResult, RepositoryFingerprint, VerificationReport


@dataclass(slots=True)
class DiagnosticFinding:
    code: str
    severity: str
    message: str
    evidence: str
    remediation: str


def _failure_finding(check: CheckResult) -> DiagnosticFinding:
    output = (check.stdout + "\n" + check.stderr).strip()
    if "ModuleNotFoundError" in output or "ImportError" in output:
        return DiagnosticFinding(
            "RUNTIME_DEPENDENCY_MISSING",
            "high",
            f"{check.name} could not start because a target dependency is unavailable.",
            output[-6000:],
            "Use the target repository runtime/environment and install its declared dependencies before diagnosing application failures.",
        )
    if check.status.value == "BLOCKED":
        return DiagnosticFinding(
            "VERIFICATION_BLOCKED",
            "high",
            f"{check.name} was blocked before execution.",
            check.reason or "no execution reason recorded",
            "Resolve the command-policy or runtime prerequisite before attempting a repair.",
        )
    return DiagnosticFinding(
        "TEST_FAILURE" if "test" in check.name else "VERIFICATION_FAILURE",
        "high",
        f"{check.name} completed unsuccessfully.",
        output[-6000:] or (check.reason or f"exit code={check.exit_code}"),
        "Inspect the failing test/check and its implementation evidence. Do not weaken tests merely to make verification pass.",
    )


class DiagnosticEngine:
    def __init__(self, repo: Path):
        self.repo = repo.resolve()

    def run(
        self,
        verification: VerificationReport | None = None,
    ) -> tuple[RepositoryFingerprint, list[DiagnosticFinding]]:
        fp = detect(self.repo)
        findings: list[DiagnosticFinding] = []

        if not fp.languages:
            findings.append(
                DiagnosticFinding(
                    "NO_LANGUAGE",
                    "high",
                    "No recognized source language detected",
                    "fingerprint.languages=[]",
                    "Add or configure a supported project language.",
                )
            )
        if not fp.test_systems:
            findings.append(
                DiagnosticFinding(
                    "NO_TESTS",
                    "medium",
                    "No test system was detected",
                    "fingerprint.test_systems=[]",
                    "Add deterministic tests.",
                )
            )
        if fp.environment_files and ".env.example" not in fp.environment_files and ".env.template" not in fp.environment_files:
            findings.append(
                DiagnosticFinding(
                    "ENV_CONTRACT",
                    "medium",
                    "Environment files exist without a template contract",
                    ",".join(fp.environment_files),
                    "Provide a sanitized environment template.",
                )
            )
        if (self.repo / "package.json").exists() and not any(
            (self.repo / x).exists() for x in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")
        ):
            findings.append(
                DiagnosticFinding(
                    "UNLOCKED_NODE_DEPS",
                    "medium",
                    "Node dependency manifest has no lockfile",
                    "package.json exists",
                    "Commit a package-manager lockfile.",
                )
            )
        if not (self.repo / ".gitignore").exists():
            findings.append(
                DiagnosticFinding(
                    "NO_GITIGNORE",
                    "low",
                    "No .gitignore was detected",
                    ".gitignore missing",
                    "Add an appropriate ignore policy.",
                )
            )

        if verification is not None:
            findings.extend(
                _failure_finding(check)
                for check in verification.checks
                if check.status.value in {"FAIL", "BLOCKED"}
            )

        return fp, findings
