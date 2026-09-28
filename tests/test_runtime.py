from pathlib import Path

from repoforge.runtime import discover_python, discover_runtime


def test_prefers_target_venv(tmp_path: Path) -> None:
    target = tmp_path / ".venv" / "Scripts"
    target.mkdir(parents=True)
    python = target / "python.exe"
    python.write_text("", encoding="utf-8")

    command, source = discover_python(tmp_path)

    assert command == [str(python.resolve())]
    assert source == "target-venv"


def test_runtime_reports_fallback(tmp_path: Path) -> None:
    runtime = discover_runtime(tmp_path)

    assert runtime["python_source"] == "repoforge-runtime"
