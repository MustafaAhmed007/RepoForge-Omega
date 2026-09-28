from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from .patching import FilePatch
from .config import ForgeConfig
from .engine import RepoForge
from .evidence import EvidenceBundle, EvidenceItem
from .rca import RootCauseAnalysis, RootCauseAnalysisEngine
from .reviewer import IndependentReviewer
from .transaction import RepairTransaction


@dataclass(slots=True)
class RepairAttempt:
    number: int
    patches: list[str]
    status: str
    rca_confidence: float
    review_approved: bool
    reason: str = ""


@dataclass(slots=True)
class RepairLoopResult:
    verified: bool
    attempts: list[RepairAttempt] = field(default_factory=list)
    rca: RootCauseAnalysis | None = None


class RepairLoop:
    def __init__(self, config: ForgeConfig) -> None:
        self.config = config

    def run(self, patch_provider) -> RepairLoopResult:
        attempts: list[RepairAttempt] = []
        forge = RepoForge(self.config.repo)

        for number in range(1, self.config.max_repair_attempts + 1):
            verification = forge.verify(self.config.timeout_seconds)
            if verification.release_status.value == "VERIFIED":
                return RepairLoopResult(True, attempts)

            evidence = EvidenceBundle(verification.execution_id)
            rca = RootCauseAnalysisEngine(self.config.repo).analyze(verification, evidence)
            patches = patch_provider(rca, verification, evidence)

            if not patches:
                attempts.append(
                    RepairAttempt(number, [], "NO_PATCH", rca.confidence, False)
                )
                return RepairLoopResult(False, attempts, rca)

            if self.config.dry_run:
                attempts.append(
                    RepairAttempt(
                        number,
                        [p.path for p in patches],
                        "DRY_RUN",
                        rca.confidence,
                        False,
                    )
                )
                return RepairLoopResult(False, attempts, rca)

            transaction = RepairTransaction(
                self.config.repo,
                max_files=self.config.max_files_changed,
                max_patch_bytes=self.config.max_patch_bytes,
                allow_dirty_files=self.config.allow_dirty_files,
            )

            try:
                changed = transaction.apply(patches)
                after = forge.verify(self.config.timeout_seconds)
                post_evidence = EvidenceBundle(after.execution_id)
                post_evidence.add(
                    EvidenceItem(
                        "verification",
                        "post-repair",
                        "\n".join(
                            f"{check.name}: {check.status.value} exit={check.exit_code}"
                            for check in after.checks
                        ),
                    )
                )
                RootCauseAnalysisEngine(self.config.repo).analyze(after, post_evidence)
                review = IndependentReviewer(self.config.repo).review(
                    post_evidence, changed
                )

                if after.release_status.value == "VERIFIED" and review.approved:
                    transaction.commit()
                    attempts.append(
                        RepairAttempt(
                            number, changed, "VERIFIED", rca.confidence, True
                        )
                    )
                    return RepairLoopResult(True, attempts, rca)

                transaction.rollback()
                attempts.append(
                    RepairAttempt(
                        number,
                        changed,
                        "ROLLED_BACK",
                        rca.confidence,
                        review.approved,
                        "Verification or independent review failed.",
                    )
                )
            except Exception as exc:
                transaction.rollback()
                attempts.append(
                    RepairAttempt(number, [], "ERROR", rca.confidence, False, str(exc))
                )

        return RepairLoopResult(
            False,
            attempts,
            rca if "rca" in locals() else None,
        )
