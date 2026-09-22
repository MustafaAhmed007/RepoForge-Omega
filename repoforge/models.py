from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

class GateStatus(str, Enum):
    PASS='PASS'; FAIL='FAIL'; SKIP='SKIP'; BLOCKED='BLOCKED'

class ReleaseStatus(str, Enum):
    VERIFIED='VERIFIED'; NOT_VERIFIED='NOT VERIFIED'; BLOCKED='BLOCKED'

@dataclass(slots=True)
class CheckResult:
    name: str
    status: GateStatus
    exit_code: int | None
    duration_ms: int
    stdout: str = ''
    stderr: str = ''
    command: list[str] = field(default_factory=list)
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data=asdict(self); data['status']=self.status.value; return data

@dataclass(slots=True)
class RepositoryFingerprint:
    path: str
    languages: list[str]
    frameworks: list[str]
    package_managers: list[str]
    build_systems: list[str]
    test_systems: list[str]
    deployment_targets: list[str]
    entry_points: list[str]
    environment_files: list[str]
    git_branch: str | None
    git_commit: str | None
    file_count: int
    total_bytes: int

    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(slots=True)
class VerificationReport:
    fingerprint: RepositoryFingerprint
    checks: list[CheckResult]
    release_status: ReleaseStatus
    blockers: list[str]
    recommendations: list[str]
    execution_id: str

    def to_dict(self) -> dict[str, Any]:
        return {'execution_id':self.execution_id,'fingerprint':self.fingerprint.to_dict(),'checks':[c.to_dict() for c in self.checks],'release_status':self.release_status.value,'blockers':self.blockers,'recommendations':self.recommendations}
