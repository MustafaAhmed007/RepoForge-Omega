from __future__ import annotations

import sys
from pathlib import Path

from repoforge.engine import RepoForge


def test_python_checks_use_active_interpreter(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (tmp_path / "sample.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()

    checks = RepoForge(tmp_path).discover_checks()

    commands = {name: command for name, command in checks}
    assert commands["python-tests"][:3] == [sys.executable, "-m", "pytest"]
    assert commands["python-compile"][:3] == [sys.executable, "-m", "compileall"]


def test_python_checks_prefer_target_venv(tmp_path: Path) -> None:
    target = tmp_path / ".venv" / "Scripts"
    target.mkdir(parents=True)
    python = target / "python.exe"
    python.write_text("", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()

    commands = dict(RepoForge(tmp_path).discover_checks())

    assert commands["python-tests"][:3] == [str(python.resolve()), "-m", "pytest"]
    assert commands["python-compile"][:3] == [str(python.resolve()), "-m", "compileall"]


def test_optional_make_check_does_not_block_release(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='sample'\n", encoding="utf-8"
    )
    (tmp_path / "sample.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text(
        "def test_ok(): assert True\n", encoding="utf-8"
    )
    (tmp_path / "Makefile").write_text(
        "test:\n\tpython -m pytest\n", encoding="utf-8"
    )

    report = RepoForge(tmp_path).verify()

    make_checks = [check for check in report.checks if check.name == "make-test"]
    assert make_checks
    assert make_checks[0].required is False


def test_optional_make_check_is_not_a_readiness_blocker(tmp_path: Path) -> None:
    from repoforge.readiness import assess

    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='sample'\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    report = RepoForge(tmp_path).verify()
    readiness = assess(tmp_path, report)

    assert "make-test" not in readiness.blockers
    assert "make-lint" not in readiness.blockers
