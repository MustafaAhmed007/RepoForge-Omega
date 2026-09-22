from __future__ import annotations

from dataclasses import dataclass

from .config import ForgeConfig
from .engine import RepoForge
from .memory import MemoryStore
from .patching import FilePatch, SafePatcher
from .pipeline import Pipeline
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


class Autopilot:
    def __init__(self, config: ForgeConfig):
        self.config = config

    def run(self, patches: list[FilePatch] | None = None) -> AutopilotResult:
        _, findings, proposals = Pipeline(self.config).inspect()
        planner = RepairPlanner(self.config.repo)
        candidate_patches = patches if patches is not None else planner.deterministic_patches(findings)
        patched: list[str] = []
        rolled_back = False

        if candidate_patches and not self.config.dry_run:
            transaction = RepairTransaction(self.config.repo)
            try:
                patched = transaction.apply(candidate_patches)
                verification = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
                if verification.release_status.value == "NOT VERIFIED":
                    transaction.rollback()
                    rolled_back = True
                    patched = []
                else:
                    transaction.commit()
            except Exception:
                transaction.rollback()
                rolled_back = True
        else:
            patched = SafePatcher(self.config.repo).apply(candidate_patches, dry_run=True)

        verification = RepoForge(self.config.repo).verify(self.config.timeout_seconds)
        readiness = assess(self.config.repo)
        MemoryStore(self.config.repo / ".repoforge" / "events.jsonl").append(
            "autopilot",
            verification.release_status.value,
            f"{len(findings)} findings",
            f"{len(patched)} patches applied or validated; rollback={rolled_back}",
        )
        return AutopilotResult(
            len(findings), len(proposals), patched, verification.release_status.value,
            readiness, rolled_back, 1,
        )
