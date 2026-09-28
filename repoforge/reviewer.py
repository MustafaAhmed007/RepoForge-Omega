from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .evidence import EvidenceBundle
from .providers import ModelRequest, provider_for_role


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    severity: str
    category: str
    statement: str
    evidence: str


@dataclass(slots=True)
class IndependentReview:
    approved: bool
    findings: list[ReviewFinding]
    reviewer: str
    evidence_digest: str


class IndependentReviewer:
    """A separate evidence-only gate. Model review is optional; deterministic review is always available."""

    def __init__(self, repo: Path):
        self.repo = repo.resolve()

    def _deterministic(self, evidence: EvidenceBundle, changed_files: list[str]) -> IndependentReview:
        findings: list[ReviewFinding] = []
        for path in changed_files:
            if path.replace("\\", "/").startswith("tests/"):
                findings.append(
                    ReviewFinding(
                        "high", "test-mutation",
                        "Existing test files must not be changed by autonomous repair.",
                        path,
                    )
                )
        try:
            diff = subprocess.run(
                ["git", "diff", "--check"],
                cwd=self.repo,
                text=True,
                capture_output=True,
                check=False,
            )
            if diff.returncode != 0:
                findings.append(
                    ReviewFinding("high", "diff-invalid", "Git reports whitespace or patch-format errors.", diff.stdout + diff.stderr)
                )
        except OSError as exc:
            findings.append(ReviewFinding("high", "git-unavailable", "Could not independently inspect the patch.", str(exc)))

        if not any(item.kind == "failure" for item in evidence.items):
            findings.append(
                ReviewFinding("high", "missing-evidence", "Independent reviewer received no verification evidence.", evidence.digest())
            )

        return IndependentReview(
            not any(item.severity == "high" for item in findings),
            findings,
            "deterministic-reviewer",
            evidence.digest(),
        )

    def review(self, evidence: EvidenceBundle, changed_files: list[str]) -> IndependentReview:
        deterministic = self._deterministic(evidence, changed_files)
        if not deterministic.approved:
            return deterministic

        provider = provider_for_role("review")
        if getattr(provider, "name", "disabled") == "disabled":
            return deterministic

        response = provider.complete(
            ModelRequest(
                "You are an independent software reviewer. You are not the repair agent. Judge only supplied evidence.",
                "Return JSON: {approved:boolean, findings:[{severity,category,statement,evidence}]}",
                json.dumps({
                    "evidence": evidence.for_reviewer(),
                    "changed_files": changed_files,
                    "rules": [
                        "Do not trust the repair agent.",
                        "Do not invent test results.",
                        "Reject unsupported root causes.",
                        "Reject weakened existing tests.",
                        "Reject insufficient evidence.",
                    ],
                }),
            )
        )
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return IndependentReview(
                False,
                [ReviewFinding("high", "invalid-review", "Independent model reviewer returned invalid JSON.", response.text[:1000])],
                provider.name,
                evidence.digest(),
            )

        findings = [
            ReviewFinding(
                str(item.get("severity", "high")),
                str(item.get("category", "unknown")),
                str(item.get("statement", "")),
                str(item.get("evidence", "")),
            )
            for item in data.get("findings", [])
            if isinstance(item, dict)
        ]
        approved = deterministic.approved and bool(data.get("approved", False)) and not any(
            finding.severity == "high" for finding in findings
        )
        return IndependentReview(approved, findings, provider.name, evidence.digest())
