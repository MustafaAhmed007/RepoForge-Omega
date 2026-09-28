from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .fingerprint import detect
from .models import VerificationReport


@dataclass(slots=True)
class Readiness:
    ready: bool
    blockers: list[str]
    checks: dict[str, bool]


def assess(
    repo: Path,
    verification: VerificationReport | None = None,
) -> Readiness:
    fp = detect(repo)
    checks = {
        "recognized_project": bool(fp.languages),
        "tests_detected": bool(fp.test_systems),
        "build_detected": bool(fp.build_systems),
        "deployment_target_detected": bool(fp.deployment_targets),
    }

    blockers = [
        name
        for name, ok in checks.items()
        if not ok and name in {"recognized_project", "tests_detected"}
    ]

    if verification is not None:
        blockers.extend(
            check.name
            for check in verification.checks
            if check.required and check.status.value in {"FAIL", "BLOCKED"}
        )

    # A repository cannot be declared ready when deterministic verification
    # is not VERIFIED, regardless of structural fingerprint checks.
    if verification is not None and verification.release_status.value != "VERIFIED":
        ready = False
    else:
        ready = not blockers

    return Readiness(
        ready=ready,
        blockers=list(dict.fromkeys(blockers)),
        checks=checks,
    )
