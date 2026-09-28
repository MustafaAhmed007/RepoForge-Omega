from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .models import VerificationReport
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

    def run(
        self,
        patch_provider: Callable[[RootCauseAnalysis, VerificationReport, EvidenceBundle], list[FilePatch]],
    ) -> RepairLoopResult:
        attempts: list[RepairAttempt] = []
        forge = RepoForge(self.config.repo)
        transaction = RepairTransaction(
            self.config.repo,
            max_files=self.config.max_files_changed,
            max_patch_bytes=self.config.max_patch_bytes,
            allow_dirty_files=self.config.allow_dirty_files,
        )
        committed = False

        try:
            for number in range(1, self.config.max_repair_attempts + 1):
                verification = forge.verify(self.config.timeout_seconds)
                if verification.release_status.value == "VERIFIED":
                    if not self._review_and_commit(transaction, verification, attempts):
                        transaction.rollback()
                        return RepairLoopResult(False, attempts)
                    committed = True
                    return RepairLoopResult(True, attempts)

                evidence = EvidenceBundle(verification.execution_id)
                rca = RootCauseAnalysisEngine(self.config.repo).analyze(verification, evidence)
                patches = patch_provider(rca, verification, evidence)

                if not patches:
                    attempts.append(
                        RepairAttempt(number, [], "NO_PATCH", rca.confidence, False)
                    )
                    transaction.rollback()
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
                    transaction.rollback()
                    return RepairLoopResult(False, attempts, rca)

                changed = transaction.apply(patches)
                attempts.append(
                    RepairAttempt(
                        number,
                        changed,
                        "APPLIED",
                        rca.confidence,
                        False,
                    )
                )

            final = forge.verify(self.config.timeout_seconds)
            if final.release_status.value != "VERIFIED":
                reason = "Repair budget exhausted; required verification checks still fail."
                if final.blockers:
                    reason += " Blockers: " + ", ".join(final.blockers)
                if attempts:
                    attempts[-1].reason = reason
                    attempts[-1].status = "ROLLED_BACK"
                transaction.rollback()
                return RepairLoopResult(False, attempts, rca if "rca" in locals() else None)

            if not self._review_and_commit(transaction, final, attempts):
                transaction.rollback()
                return RepairLoopResult(False, attempts, rca if "rca" in locals() else None)

            committed = True
            if attempts:
                attempts[-1].status = "VERIFIED"
                attempts[-1].review_approved = True
            return RepairLoopResult(True, attempts, rca if "rca" in locals() else None)
        except Exception as exc:
            transaction.rollback()
            if attempts:
                attempts[-1].status = "ERROR"
                attempts[-1].reason = str(exc)
            return RepairLoopResult(False, attempts, rca if "rca" in locals() else None)
        finally:
            if not committed:
                transaction.rollback()

    def _review_and_commit(
        self,
        transaction: RepairTransaction,
        verification: VerificationReport,
        attempts: list[RepairAttempt],
    ) -> bool:
        evidence = EvidenceBundle(verification.execution_id)
        evidence.add(
            EvidenceItem(
                "verification",
                "final",
                "\n".join(
                    f"{check.name}: {check.status.value} exit={check.exit_code}"
                    for check in verification.checks
                ),
            )
        )
        changed = [path for attempt in attempts for path in attempt.patches]
        review = IndependentReviewer(self.config.repo).review(evidence, changed)
        if review.approved:
            transaction.commit()
            return True
        if attempts:
            attempts[-1].reason = "Independent review rejected the candidate."
            attempts[-1].review_approved = False
        return False
