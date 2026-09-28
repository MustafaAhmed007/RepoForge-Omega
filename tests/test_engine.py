from __future__ import annotations

import sys
from pathlib import Path

from repoforge.engine import RepoForge


def test_python_checks_use_active_interpreter(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()

    checks = RepoForge(tmp_path).discover_checks()

    commands = {name: command for name, command in checks}
    assert commands["python-tests"][:3] == [sys.executable, "-m", "pytest"]
    assert commands["python-compile"][:3] == [sys.executable, "-m", "compileall"]
