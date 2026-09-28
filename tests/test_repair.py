from pathlib import Path

from repoforge.diagnostics import DiagnosticFinding
from repoforge.models import (
    CheckResult,
    GateStatus,
    ReleaseStatus,
    RepositoryFingerprint,
    VerificationReport,
)
from repoforge.rca import Hypothesis, RootCauseAnalysis
from repoforge.readiness import assess
from repoforge.repair import RepairPlanner


def _verification(tmp_path: Path) -> VerificationReport:
    fingerprint = RepositoryFingerprint(
        path=str(tmp_path),
        languages=["Python"],
        frameworks=[],
        package_managers=["Python"],
        build_systems=["Docker"],
        test_systems=["pytest"],
        deployment_targets=[],
        entry_points=[],
        environment_files=[],
        git_branch="test",
        git_commit="abc",
        file_count=3,
        total_bytes=100,
    )
    check = CheckResult(
        "python-tests",
        GateStatus.FAIL,
        1,
        10,
        stdout=(
            "AssertionError: assert <Intent.MULTI_HOP: 'multi_hop'> "
            "is <Intent.COMPARISON: 'comparison'>\n"
            "tests/test_planner.py::test_comparison_is_adaptive"
        ),
    )
    return VerificationReport(
        fingerprint,
        [check],
        ReleaseStatus.NOT_VERIFIED,
        ["python-tests"],
        [],
        "run-1",
    )


def test_repair_planner_is_deterministic(tmp_path: Path):
    findings = [
        DiagnosticFinding("NO_TESTS", "medium", "missing tests", "x", "add tests")
    ]
    proposals = RepairPlanner(tmp_path).propose(findings)
    assert len(proposals) == 1
    assert proposals[0].action == "add_tests"


def test_repair_planner_builds_bounded_comparison_patch(tmp_path: Path):
    (tmp_path / "adaptive_rag").mkdir()
    planner = tmp_path / "adaptive_rag" / "planner.py"
    planner.write_text(
        "intent = (\n"
        "    Intent.CURRENT if freshness else\n"
        "    Intent.MULTI_HOP if multi_hop else\n"
        "    Intent.COMPARISON if comparison else\n"
        "    Intent.FACTUAL\n"
        ")\n",
        encoding="utf-8",
    )
    verification = _verification(tmp_path)
    rca = RootCauseAnalysis(
        "run-1",
        "python-tests failed",
        hypotheses=[
            Hypothesis(
                "Failing test calls production code in 'adaptive_rag/planner.py'.",
                ["tests/test_planner.py::test_comparison_is_adaptive", "adaptive_rag/planner.py"],
                0.85,
                "localization",
            )
        ],
        affected_files=["adaptive_rag/planner.py", "tests/test_planner.py"],
        confidence=0.85,
    )

    patches = RepairPlanner(tmp_path).deterministic_patches(rca, verification, [])

    assert len(patches) == 1
    assert patches[0].path == "adaptive_rag/planner.py"
    assert "Intent.COMPARISON if comparison else" in patches[0].replacement
    assert patches[0].replacement.index("Intent.COMPARISON") < patches[0].replacement.index("Intent.MULTI_HOP")


def test_readiness_cannot_be_ready_when_verification_is_blocked(tmp_path: Path):
    verification = _verification(tmp_path)
    verification.release_status = ReleaseStatus.BLOCKED
    verification.checks.append(
        CheckResult(
            "make-test",
            GateStatus.BLOCKED,
            None,
            0,
            reason="executable not found",
        )
    )

    readiness = assess(tmp_path, verification)

    assert readiness.ready is False
    assert "python-tests" in readiness.blockers
    assert "make-test" in readiness.blockers


def _ruff_verification(tmp_path: Path, output: str) -> VerificationReport:
    fingerprint = RepositoryFingerprint(
        path=str(tmp_path),
        languages=["Python"],
        frameworks=[],
        package_managers=["Python"],
        build_systems=[],
        test_systems=["pytest"],
        deployment_targets=[],
        entry_points=[],
        environment_files=[],
        git_branch="test",
        git_commit="abc",
        file_count=1,
        total_bytes=10,
    )
    check = CheckResult(
        "python-ruff",
        GateStatus.FAIL,
        1,
        10,
        stdout=output,
    )
    return VerificationReport(
        fingerprint,
        [check],
        ReleaseStatus.NOT_VERIFIED,
        ["python-ruff"],
        [],
        "ruff-run",
    )


def test_repair_planner_repairs_safe_ruff_findings(tmp_path: Path):
    research = tmp_path / "adaptive_rag"
    research.mkdir()
    source = research / "research.py"
    source.write_text(
        "import re\n"
        "def run():\n"
        "    text = re.sub('x', 'y', 'x', flags=re.I)\n"
        "    try:\n"
        "        return 1\n"
        "    except Exception as exc:\n"
        "        warnings.append(str(exc))\n",
        encoding="utf-8",
    )
    output = (
        "FURB167 [*] Use of regular expression alias re.I\n"
        "  --> adaptive_rag\\research.py:3:49\n"
        "\n"
        "BLE001 Do not catch blind exception: Exception\n"
        "  --> adaptive_rag\\research.py:6:12\n"
    )
    verification = _ruff_verification(tmp_path, output)

    patches = RepairPlanner(tmp_path).deterministic_patches(
        RootCauseAnalysis("ruff-run", "python-ruff failed"),
        verification,
        [],
    )

    assert len(patches) == 1
    assert "re.IGNORECASE" in patches[0].replacement
    assert "# noqa: BLE001" in patches[0].replacement


def test_repair_planner_repairs_simple_import_order(tmp_path: Path):
    source = tmp_path / "base.py"
    source.write_text(
        "from __future__ import annotations\n"
        "from abc import ABC\n"
        "from collections import Counter\n"
        "import re\n"
        "\n"
        "from ..models import Document\n",
        encoding="utf-8",
    )
    output = (
        "I001 [*] Import block is un-sorted or un-formatted\n"
        " --> base.py:2:1\n"
    )
    verification = _ruff_verification(tmp_path, output)

    patches = RepairPlanner(tmp_path).deterministic_patches(
        RootCauseAnalysis("ruff-run", "python-ruff failed"),
        verification,
        [],
    )

    assert len(patches) == 1
    assert patches[0].replacement.startswith(
        "from __future__ import annotations\nimport re\nfrom abc import ABC\n"
    )


def test_rollback_marks_all_applied_attempts():
    from repoforge.repair_loop import RepairAttempt, RepairLoop

    attempts = [
        RepairAttempt(1, ["planner.py"], "APPLIED", 0.9, False),
        RepairAttempt(2, [], "NO_PATCH", 0.8, False),
    ]

    RepairLoop._mark_rolled_back(attempts, "rollback")

    assert attempts[0].status == "ROLLED_BACK"
    assert attempts[0].reason == "rollback"
    assert attempts[1].status == "NO_PATCH"
