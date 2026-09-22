from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .fingerprint import detect

@dataclass(slots=True)
class Readiness:
    ready: bool
    blockers: list[str]
    checks: dict[str,bool]

def assess(repo:Path)->Readiness:
    fp=detect(repo); checks={
        'recognized_project': bool(fp.languages),
        'tests_detected': bool(fp.test_systems),
        'build_detected': bool(fp.build_systems),
        'deployment_target_detected': bool(fp.deployment_targets),
    }
    blockers=[name for name,ok in checks.items() if not ok and name in {'recognized_project','tests_detected'}]
    return Readiness(not blockers,blockers,checks)
