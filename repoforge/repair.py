from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .diagnostics import DiagnosticFinding
from .fingerprint import detect
from .models import VerificationReport
from .patching import FilePatch
from .rca import RootCauseAnalysis


@dataclass(slots=True)
class RepairProposal:
    finding_code: str
    action: str
    rationale: str


class RepairPlanner:
    def __init__(self, repo: Path):
        self.repo = repo.resolve()

    def propose(self, findings: list[DiagnosticFinding]) -> list[RepairProposal]:
        actions = {
            "NO_TESTS": ("add_tests", "Create deterministic regression tests."),
            "ENV_CONTRACT": ("create_env_template", "Create a sanitized environment contract."),
            "UNLOCKED_NODE_DEPS": ("generate_lockfile", "Generate a lockfile only after explicit approval."),
            "NO_GITIGNORE": ("add_gitignore", "Add ecosystem-specific ignore rules."),
            "TEST_FAILURE": (
                "diagnose_and_repair_test_failure",
                "Inspect the failing test and implementation evidence; never weaken an existing test to hide a defect.",
            ),
            "VERIFICATION_FAILURE": (
                "diagnose_verification_failure",
                "Inspect the failing verification command and implementation evidence before proposing a bounded repair.",
            ),
            "RUNTIME_DEPENDENCY_MISSING": (
                "repair_target_environment",
                "Use the target runtime and declared dependency metadata before diagnosing application behavior.",
            ),
            "VERIFICATION_BLOCKED": (
                "resolve_verification_blocker",
                "Resolve the execution-policy or runtime prerequisite before mutation.",
            ),
        }
        proposals: list[RepairProposal] = []
        for finding in findings:
            action, rationale = actions.get(
                finding.code,
                ("manual_review", "Collect more evidence before mutation."),
            )
            proposals.append(RepairProposal(finding.code, action, rationale))
        return proposals

    def deterministic_patches(
        self,
        rca: RootCauseAnalysis,
        verification: VerificationReport,
        findings: list[DiagnosticFinding],
    ) -> list[FilePatch]:
        """Return only small, evidence-backed production patches.

        These heuristics are intentionally narrow. A heuristic must be supported by
        the failing assertion, RCA localization, and a recognizable source pattern;
        otherwise model-assisted repair or human review remains the fallback.
        """
        patches: list[FilePatch] = []
        fp = detect(self.repo)

        for finding in findings:
            if finding.code == "NO_GITIGNORE" and not (self.repo / ".gitignore").exists():
                ignores = (
                    "# RepoForge baseline\n"
                    "__pycache__/\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n"
                    ".venv/\nvenv/\n.env\n.env.*\n!.env.example\n"
                    "node_modules/\ndist/\nbuild/\n*.egg-info/\n.repoforge/\n"
                )
                patches.append(FilePatch(".gitignore", "", ignores))
            elif finding.code == "ENV_CONTRACT" and not (self.repo / ".env.example").exists():
                patches.append(
                    FilePatch(
                        ".env.example",
                        "",
                        "# Sanitized environment contract\n"
                        "# Add required variables here without real credentials.\n",
                    )
                )

        if fp.languages and verification.release_status.value != "VERIFIED":
            patches.extend(self._comparison_precedence_patches(rca, verification))

        return self._deduplicate(patches)

    def _comparison_precedence_patches(
        self,
        rca: RootCauseAnalysis,
        verification: VerificationReport,
    ) -> list[FilePatch]:
        if not self._comparison_failure_is_supported(rca, verification):
            return []

        patches: list[FilePatch] = []
        for relative in rca.affected_files:
            if not relative.endswith(".py") or relative.replace("\\", "/").startswith("tests/"):
                continue
            path = self.repo / relative
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            replacement = self._swap_comparison_and_multihop(text)
            if replacement is not None:
                patches.append(FilePatch(relative.replace("\\", "/"), text, replacement))
        return patches[:1]

    def _comparison_failure_is_supported(
        self,
        rca: RootCauseAnalysis,
        verification: VerificationReport,
    ) -> bool:
        output = "\n".join(
            check.stdout + "\n" + check.stderr
            for check in verification.checks
            if check.status.value == "FAIL"
        )
        return (
            "Intent.MULTI_HOP" in output
            and "Intent.COMPARISON" in output
            and any(
                hypothesis.category == "localization"
                and ".py" in hypothesis.statement
                for hypothesis in rca.hypotheses
            )
            and any("adaptive" in path.lower() for path in rca.affected_files)
        )

    def _swap_comparison_and_multihop(self, text: str) -> str | None:
        lines = text.splitlines(keepends=True)
        for index, line in enumerate(lines):
            if "Intent.MULTI_HOP if multi_hop else" not in line:
                continue
            if index + 1 >= len(lines) or "Intent.COMPARISON if comparison else" not in lines[index + 1]:
                continue
            updated = lines.copy()
            updated[index], updated[index + 1] = updated[index + 1], updated[index]
            return "".join(updated)
        return None

    @staticmethod
    def _deduplicate(patches: list[FilePatch]) -> list[FilePatch]:
        seen: set[tuple[str, str, str]] = set()
        result: list[FilePatch] = []
        for patch in patches:
            key = (patch.path, patch.expected, patch.replacement)
            if key not in seen:
                seen.add(key)
                result.append(patch)
        return result
