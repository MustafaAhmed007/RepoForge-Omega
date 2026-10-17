from pathlib import Path

import pytest

from repoforge.fingerprint import detect


def test_detects_python_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "main.py").write_bytes(b"print('ok')\n")
    fp = detect(tmp_path)
    assert "Python" in fp.languages
    assert "main.py" in fp.entry_points


def test_detects_python_tests_directory(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    fp = detect(tmp_path)
    assert "pytest" in fp.test_systems


def test_ignores_repoforge_and_generated_artifacts(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_bytes(b"print('ok')\n")
    (tmp_path / ".repoforge").mkdir()
    (tmp_path / ".repoforge" / "report.json").write_text("{}", encoding="utf-8")
    (tmp_path / "demo.egg-info").mkdir()
    (tmp_path / "demo.egg-info" / "PKG-INFO").write_text("metadata", encoding="utf-8")

    fp = detect(tmp_path)

    assert fp.file_count == 1
    assert fp.total_bytes == len("print('ok')\n".encode("utf-8"))


def test_detect_handles_malformed_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"name": "broken", invalid json}',
        encoding="utf-8",
    )

    fp = detect(tmp_path)

    assert "Node.js" in fp.package_managers
    assert fp.file_count == 1


@pytest.mark.parametrize("package_json", ["null", "[]", '"text"', "42"])
def test_detect_handles_non_object_package_json(tmp_path: Path, package_json: str) -> None:
    (tmp_path / "package.json").write_text(package_json, encoding="utf-8")

    fp = detect(tmp_path)

    assert "Node.js" in fp.package_managers
    assert fp.file_count == 1


def test_detect_handles_invalid_package_metadata_fields(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": null, "devDependencies": [], "scripts": "invalid"}',
        encoding="utf-8",
    )

    fp = detect(tmp_path)

    assert "Node.js" in fp.package_managers
    assert fp.file_count == 1


def test_detects_valid_package_metadata(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18.0.0"}, '
        '"devDependencies": {"vite": "^5.0.0"}, '
        '"scripts": {"build": "vite build", "test": "vitest"}}',
        encoding="utf-8",
    )

    fp = detect(tmp_path)

    assert "Node.js" in fp.package_managers
    assert "React" in fp.frameworks
    assert "Vite" in fp.frameworks
    assert "npm build" in fp.build_systems
    assert "npm test" in fp.test_systems
    assert fp.file_count == 1

