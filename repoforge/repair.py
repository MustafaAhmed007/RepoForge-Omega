from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .diagnostics import DiagnosticFinding
from .fingerprint import detect
from .patching import FilePatch


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

    def deterministic_patches(self, findings: list[DiagnosticFinding]) -> list[FilePatch]:
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
        if not fp.languages:
            return patches
        return patches
