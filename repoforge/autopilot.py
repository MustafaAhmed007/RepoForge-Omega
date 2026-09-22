from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import ForgeConfig
from .diagnostics import DiagnosticFinding
from .engine import RepoForge
from .memory import MemoryStore
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


def _model_patches(repo: Path, findings: list[DiagnosticFinding]) -> list[FilePatch]:
    provider = provider_from_environment()
    if getattr(provider, "name", "disabled") == "disabled":
        return []
    relevant: dict[str, str] = {}
    for _finding in findings:
        for candidate in ("pyproject.toml", "package.json", "main.py", "src/index.ts", "src/index.js"):
            path = repo / candidate
            if path.exists() and candidate not in relevant:
                text = path.read_text(encoding="utf-8", errors="replace")
                if len(text) <= 30000:
                    relevant[candidate] = text
    response = provider.complete(ModelRequest(
        system="Return ONLY JSON with a patches array. Each patch must contain path, expected, replacement. Never use destructive commands or secrets.",
        prompt="Generate minimal patches for the supplied findings. Do not invent missing evidence.",
        context=json.dumps({"findings": [{"code": f.code, "severity": f.severity, "message": f.message, "evidence": f.evidence} for f in findings], "files": relevant}),
    ))
    data = json.loads(response.text)
    return [FilePatch(str(p["path"]), str(p["expected"]), str(p["replacement"])) for p in data.get("patches", [])]


class Autopilot:
    def __init__(self, config: ForgeConfig):
        self.config = config

    def run(self, patches: list[FilePatch] | None = None) -> AutopilotResult:
        _, findings, proposals = Pipeline(self.config).inspect()
        planner = RepairPlanner(self.config.repo)
        candidate_patches = patches if patches is not None else planner.deterministic_patches(findings)
        if not candidate_patches:
            try:
                candidate_patches = _model_patches(self.config.repo, findings)
            except Exception as exc:
                MemoryStore(self.config.repo / ".repoforge" / "events.jsonl").append("model", "error", str(exc), "model repair skipped")

        patched: list[str] = []
        rolled_back = False
        if candidate_patches and not self.config.dry_run:
            transaction = RepairTransaction(self.config.repo)
            try:
                patched = transaction.apply(candidate_patches)
                verification = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
                if verification.release_status.value != "VERIFIED":
                    transaction.rollback(); rolled_back = True; patched = []
                else:
                    transaction.commit()
            except Exception:
                transaction.rollback(); rolled_back = True
        elif candidate_patches:
            SafePatcher(self.config.repo).apply(candidate_patches, dry_run=True)

        verification = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
        readiness = assess(self.config.repo)
        MemoryStore(self.config.repo / ".repoforge" / "events.jsonl").append(
            "autopilot", verification.release_status.value,
            f"{len(findings)} findings", f"{len(patched)} patches applied; rollback={rolled_back}",
        )
        return AutopilotResult(len(findings), len(proposals), patched, verification.release_status.value, readiness, rolled_back, 1)
