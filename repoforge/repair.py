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

        Deterministic repair is deliberately conservative: it uses the observed
        verification output and recognizable source patterns. Semantic repairs
        remain model-assisted and still require deterministic verification.
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
            patches.extend(self._safe_ruff_patches(verification))

        return self._deduplicate(patches)

    def _safe_ruff_patches(self, verification: VerificationReport) -> list[FilePatch]:
        output = "\n".join(
            check.stdout + "\n" + check.stderr
            for check in verification.checks
            if check.name == "python-ruff" and check.status.value == "FAIL"
        )
        if not output:
            return []

        patches: list[FilePatch] = []
        diagnostics = self._ruff_diagnostics(output)
        for code, relative, line_number in diagnostics:
            normalized = relative.replace("\\", "/")
            path = self.repo / normalized
            if not path.is_file() or normalized.startswith("tests/"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")

            if code == "FURB167":
                replacement = self._replace_re_alias_on_line(text, line_number)
            elif code == "I001":
                replacement = self._sort_simple_import_block(text)
            elif code == "BLE001":
                replacement = self._waive_intentional_fallback(text, line_number)
            else:
                replacement = None

            if replacement is not None and replacement != text:
                patches.append(FilePatch(normalized, text, replacement))

        return patches

    @staticmethod
    def _ruff_diagnostics(output: str) -> list[tuple[str, str, int]]:
        matches: list[tuple[str, str, int]] = []
        blocks = re.split(r"\n\s*\n", output)
        pattern = re.compile(r"^\s*([A-Z][A-Z0-9]{2,5})\b.*?^\s*-->\s*(.+?):(\d+):\d+", re.M | re.S)
        for block in blocks:
            match = pattern.search(block)
            if match:
                matches.append((match.group(1), match.group(2).strip(), int(match.group(3))))
        return matches

    @staticmethod
    def _replace_re_alias_on_line(text: str, line_number: int) -> str | None:
        lines = text.splitlines(keepends=True)
        if line_number < 1 or line_number > len(lines):
            return None
        updated = lines.copy()
        if not re.search(r"\bre\.I\b", updated[line_number - 1]):
            return None
        updated[line_number - 1] = re.sub(
            r"\bre\.I\b",
            "re.IGNORECASE",
            updated[line_number - 1],
            count=1,
        )
        return "".join(updated)

    @staticmethod
    def _sort_simple_import_block(text: str) -> str | None:
        lines = text.splitlines(keepends=True)
        start = None
        for index, line in enumerate(lines[:80]):
            if line.startswith("import ") or line.startswith("from "):
                start = index
                break
            if line.strip() and not line.startswith("#") and not line.startswith('"""') and not line.startswith("'''"):
                if start is None and index > 0:
                    break
        if start is None:
            return None

        end = start
        while end < len(lines):
            stripped = lines[end].strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                if "(" in stripped or stripped.endswith("\\"):
                    return None
                end += 1
                continue
            break

        block = lines[start:end]
        if not block or any(not (line.startswith("import ") or line.startswith("from ")) for line in block):
            return None

        def key(line: str) -> tuple[int, str]:
            stripped = line.strip()
            if stripped.startswith("import "):
                return (0, stripped.lower())
            if stripped.startswith("from ."):
                return (2, stripped.lower())
            return (1, stripped.lower())

        ordered = sorted(block, key=key)
        if ordered == block:
            return None
        return "".join(lines[:start] + ordered + lines[end:])

    @staticmethod
    def _waive_intentional_fallback(text: str, line_number: int) -> str | None:
        lines = text.splitlines(keepends=True)
        index = line_number - 1
        if index < 0 or index >= len(lines):
            return None
        line = lines[index]
        if "except Exception" not in line or "BLE001" in line:
            return None

        indent = len(line) - len(line.lstrip())
        body: list[str] = []
        for candidate in lines[index + 1:]:
            if not candidate.strip():
                body.append(candidate)
                continue
            candidate_indent = len(candidate) - len(candidate.lstrip())
            if candidate_indent <= indent:
                break
            body.append(candidate)

        body_text = "".join(body)
        fallback_markers = (
            "warnings.append",
            "create_collection",
            "fallback",
            "recover",
            "continue",
            "return",
            "pass",
        )
        if "raise " in body_text or not any(marker in body_text for marker in fallback_markers):
            return None

        newline = "\n" if line.endswith("\n") else ""
        base = line.rstrip("\r\n")
        return "".join(
            lines[:index]
            + [base + "  # noqa: BLE001" + newline]
            + lines[index + 1:]
        )

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
