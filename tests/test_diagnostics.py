from pathlib import Path

from repoforge.diagnostics import DiagnosticEngine
from repoforge.models import (
    CheckResult,
    GateStatus,
    ReleaseStatus,
    RepositoryFingerprint,
    VerificationReport,
)


def _verification(repo: Path, output: str) -> VerificationReport:
    fingerprint = RepositoryFingerprint(
        str(repo),
        ["Python"],
        [],
        ["Python"],
        [],
        ["pytest"],
        [],
        [],
        [],
        None,
        None,
        1,
        1,
    )
    check = CheckResult("python-tests", GateStatus.FAIL, 1, 10, stdout=output)
    return VerificationReport(
        fingerprint,
        [check],
        ReleaseStatus.NOT_VERIFIED,
        ["python-tests"],
        [],
        "test",
    )


def test_missing_tests_is_reported(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print(1)\n", encoding="utf-8")
    _, findings = DiagnosticEngine(tmp_path).run()
    assert any(x.code == "NO_TESTS" for x in findings)


def test_diagnoses_missing_runtime_dependency(tmp_path: Path) -> None:
    _, findings = DiagnosticEngine(tmp_path).run(
        _verification(tmp_path, "ModuleNotFoundError: No module named 'pydantic'")
    )
    assert findings[-1].code == "RUNTIME_DEPENDENCY_MISSING"


def test_diagnoses_real_test_failure(tmp_path: Path) -> None:
    _, findings = DiagnosticEngine(tmp_path).run(
        _verification(tmp_path, "AssertionError: expected comparison")
    )
    assert findings[-1].code == "TEST_FAILURE"
