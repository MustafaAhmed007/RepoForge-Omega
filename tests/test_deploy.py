from pathlib import Path

from repoforge.deploy import plan


def test_docker_plan(tmp_path: Path):
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    result = plan(tmp_path)
    assert result.target == "docker"
    assert result.executable is True


def test_unknown_plan_is_not_executable(tmp_path: Path):
    result = plan(tmp_path)
    assert result.executable is False
