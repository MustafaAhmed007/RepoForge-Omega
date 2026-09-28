from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config import ForgeConfig
from .diagnostics import DiagnosticFinding
from .engine import RepoForge
from .memory import MemoryStore
from .models import VerificationReport
from .patching import FilePatch, SafePatcher
from .pipeline import Pipeline
from .providers import ModelRequest, provider_from_environment
from .readiness import Readiness, assess
from .repair import RepairPlanner
from .transaction import RepairTransaction


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


def _model_context(
    repo: Path,
    findings: list[DiagnosticFinding],
    verification: VerificationReport,
) -> dict[str, str]:
    relevant: dict[str, str] = {}
    paths = _failure_paths(verification)

    for candidate in (
        "pyproject.toml",
        "package.json",
        "main.py",
        "src/index.ts",
        "src/index.js",
        *paths,
    ):
        path = repo / candidate
        if path.is_file() and candidate not in relevant:
            content = path.read_text(encoding="utf-8", errors="replace")
            if len(content) <= 30_000:
                relevant[candidate] = content

    if any(f.code == "TEST_FAILURE" for f in findings):
        for root in (repo / "adaptive_rag", repo / "src", repo / "tests"):
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*.py")):
                relative = str(path.relative_to(repo)).replace("\\", "/")
                if relative in relevant:
                    continue
                content = path.read_text(encoding="utf-8", errors="replace")
                if len(content) > 20_000:
                    continue
                if sum(len(value) for value in relevant.values()) + len(content) > 100_000:
                    break
                relevant[relative] = content

    return relevant


def _model_patches(
    repo: Path,
    findings: list[DiagnosticFinding],
    verification: VerificationReport,
) -> list[FilePatch]:
    provider = provider_from_environment()
    if getattr(provider, "name", "disabled") == "disabled" or not findings:
        return []

    context = _model_context(repo, findings, verification)
    response = provider.complete(
        ModelRequest(
            system=(
                "Return ONLY JSON with a patches array. Each patch must contain path, expected, replacement. "
                "Use only evidence in the supplied repository context. Never use commands, secrets, or destructive operations. "
                "Do not modify existing tests merely to make them pass. Prefer the smallest production-code fix that addresses "
                "the observed failure. Keep changes bounded and compatible with the detected project."
            ),
            prompt=(
                "Diagnose the supplied findings and propose minimal patches. "
                "For TEST_FAILURE, preserve the existing test contract and repair the implementation rather than weakening the test."
            ),
            context=json.dumps(
                {
                    "findings": [
                        {
                            "code": f.code,
                            "severity": f.severity,
                            "message": f.message,
                            "evidence": f.evidence,
                        }
                        for f in findings
                    ],
                    "verification": verification.to_dict(),
                    "files": context,
                }
            ),
        )
    )

    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return []

    raw_patches = data.get("patches", []) if isinstance(data, dict) else []
    if not isinstance(raw_patches, list):
        return []

    patches: list[FilePatch] = []
    for patch in raw_patches:
        if not isinstance(patch, dict):
            continue
        if not all(key in patch for key in ("path", "expected", "replacement")):
            continue
        patches.append(
            FilePatch(
                str(patch["path"]),
                str(patch["expected"]),
                str(patch["replacement"]),
            )
        )
    return patches


class Autopilot:
    def __init__(self, config: ForgeConfig):
        self.config = config

    def run(self, patches: list[FilePatch] | None = None) -> AutopilotResult:
        baseline = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
        _, findings, proposals = Pipeline(self.config).inspect(verification=baseline)
        planner = RepairPlanner(self.config.repo)
        candidate_patches = (
            patches if patches is not None else planner.deterministic_patches(findings)
        )

        if not candidate_patches and findings:
            try:
                candidate_patches = _model_patches(self.config.repo, findings, baseline)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                MemoryStore(self.config.repo / ".repoforge" / "events.jsonl").append(
                    "model",
                    "error",
                    "model patch generation failed",
                    "model repair skipped",
                )

        patched: list[str] = []
        rolled_back = False
        if candidate_patches and not self.config.dry_run:
            transaction = RepairTransaction(
                self.config.repo,
                max_files=self.config.max_files_changed,
                max_patch_bytes=self.config.max_patch_bytes,
                allow_dirty_files=self.config.allow_dirty_files,
            )
            try:
                patched = transaction.apply(candidate_patches)
                verification = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
                if verification.release_status.value != "VERIFIED":
                    transaction.rollback()
                    rolled_back = True
                    patched = []
                else:
                    transaction.commit()
            except Exception:
                transaction.rollback()
                rolled_back = True
        elif candidate_patches:
            SafePatcher(
                self.config.repo,
                max_files=self.config.max_files_changed,
                max_patch_bytes=self.config.max_patch_bytes,
                allow_dirty_files=self.config.allow_dirty_files,
            ).apply(candidate_patches, dry_run=True)

        verification = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
        readiness = assess(self.config.repo)
        MemoryStore(self.config.repo / ".repoforge" / "events.jsonl").append(
            "autopilot",
            verification.release_status.value,
            f"{len(findings)} findings",
            f"{len(patched)} patches applied; rollback={rolled_back}",
        )
        return AutopilotResult(
            len(findings),
            len(proposals),
            patched,
            verification.release_status.value,
            readiness,
            rolled_back,
            1,
        )
