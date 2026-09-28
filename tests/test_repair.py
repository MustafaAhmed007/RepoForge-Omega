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
