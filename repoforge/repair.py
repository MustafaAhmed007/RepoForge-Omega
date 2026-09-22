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
        }
        return [
            RepairProposal(code, *actions.get(code, ("manual_review", "Collect more evidence before mutation.")))
            for code in (f.code for f in findings)
        ]

    def deterministic_patches(self, findings: list[DiagnosticFinding]) -> list[FilePatch]:
        patches: list[FilePatch] = []
        fp = detect(self.repo)
        for finding in findings:
            if finding.code == "NO_GITIGNORE" and not (self.repo / ".gitignore").exists():
                ignores = "# RepoForge baseline\n__pycache__/\n.pytest_cache/\n.venv/\n.env\n.env.*\n!.env.example\nnode_modules/\ndist/\nbuild/\n"
                patches.append(FilePatch(".gitignore", "", ignores))
            elif finding.code == "ENV_CONTRACT" and not (self.repo / ".env.example").exists():
                patches.append(FilePatch(".env.example", "", "# Sanitized environment contract\n# Add required variables here without real credentials.\n"))
        if not fp.languages:
            return patches
        return patches
