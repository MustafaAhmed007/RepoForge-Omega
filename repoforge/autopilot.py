from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import ForgeConfig
from .diagnostics import DiagnosticFinding
from .engine import RepoForge
from .memory import MemoryStore
from .models import VerificationReport
from .patching import FilePatch
from .pipeline import Pipeline
from .providers import ModelRequest, provider_from_environment
from .readiness import Readiness, assess
from .repair import RepairPlanner
from .repair_loop import RepairLoop
from .rca import RootCauseAnalysis
from .evidence import EvidenceBundle


@dataclass(slots=True)
class AutopilotResult:
    findings: int
    proposals: int
    patched: list[str]
    verification_status: str
    readiness: Readiness
    rolled_back: bool = False
    iterations: int = 1


def _failure_paths(verification: VerificationReport) -> list[str]:
    paths: list[str] = []
    pattern = re.compile(r"(?m)^\s*([A-Za-z0-9_./\\:-]+\.py):\d+")
    for check in verification.checks:
        if check.status.value not in {"FAIL", "BLOCKED"}:
            continue
        for match in pattern.finditer(check.stdout + "\n" + check.stderr):
            candidate = match.group(1).replace("\\", "/")
            if candidate not in paths:
                paths.append(candidate)
    return paths


def _model_patches(
    repo: Path,
    findings: list[DiagnosticFinding],
    verification: VerificationReport,
) -> list[FilePatch]:
    provider = provider_from_environment()
    if getattr(provider, "name", "disabled") == "disabled" or not findings:
        return []

    relevant: dict[str, str] = {}
    paths = _failure_paths(verification)
    candidates = (
        "pyproject.toml",
        "package.json",
        "main.py",
        "src/index.ts",
        "src/index.js",
        *paths,
    )
    for candidate in candidates:
        path = repo / candidate
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            if len(text) <= 30_000:
                relevant[candidate] = text

    for root in (repo / "tests", repo / "adaptive_rag", repo / "src"):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            relative = str(path.relative_to(repo)).replace("\\", "/")
            if relative in relevant:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if len(text) <= 20_000 and sum(map(len, relevant.values())) + len(text) <= 100_000:
                relevant[relative] = text

    response = provider.complete(
        ModelRequest(
            "You are a repair agent. Return ONLY JSON patches. Never modify existing tests. Use only supplied evidence.",
            "Find the smallest production-code change that addresses the observed failure.",
            json.dumps({
                "findings": [asdict(f) for f in findings],
                "verification": verification.to_dict(),
                "files": relevant,
            }),
        )
    )
    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return []

    patches: list[FilePatch] = []
    for item in data.get("patches", []) if isinstance(data, dict) else []:
        if isinstance(item, dict) and all(k in item for k in ("path", "expected", "replacement")):
            patches.append(
                FilePatch(str(item["path"]), str(item["expected"]), str(item["replacement"]))
            )
    return patches


class Autopilot:
    def __init__(self, config: ForgeConfig):
        self.config = config

    def run(self, patches: list[FilePatch] | None = None) -> AutopilotResult:
        baseline = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
        _, findings, proposals = Pipeline(self.config).inspect(verification=baseline)
        planner = RepairPlanner(self.config.repo)

        def provider(rca: RootCauseAnalysis, verification: VerificationReport, evidence: EvidenceBundle) -> list[FilePatch]:
            deterministic = planner.deterministic_patches(findings)
            if deterministic:
                return deterministic
            if patches is not None:
                return patches
            try:
                return _model_patches(self.config.repo, findings, verification)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                return []

        loop = RepairLoop(self.config)
        result = loop.run(provider)

        final = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
        readiness = assess(self.config.repo)
        changed: list[str] = []
        rolled_back = False
        for attempt in result.attempts:
            changed.extend(attempt.patches)
            rolled_back = rolled_back or attempt.status == "ROLLED_BACK"
        if result.verified and result.attempts:
            # Only the successful attempt remains as a committed mutation.
            changed = result.attempts[-1].patches

        MemoryStore(self.config.repo / ".repoforge" / "events.jsonl").append(
            "autopilot",
            final.release_status.value,
            f"{len(findings)} findings",
            f"{len(changed)} files changed; attempts={len(result.attempts)}; rollback={rolled_back}",
        )
        return AutopilotResult(
            len(findings),
            len(proposals),
            changed if result.verified else [],
            final.release_status.value,
            readiness,
            rolled_back,
            len(result.attempts) or 1,
        )
