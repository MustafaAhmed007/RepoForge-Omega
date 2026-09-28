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

    commands = dict(RepoForge(tmp_path).discover_checks())

    assert commands["python-tests"][:3] == [str(python.resolve()), "-m", "pytest"]
    assert commands["python-compile"][:3] == [str(python.resolve()), "-m", "compileall"]
