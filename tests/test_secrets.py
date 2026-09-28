from pathlib import Path

from repoforge.secrets import scan


def test_secret_scanner_finds_private_key_marker(tmp_path: Path) -> None:
    (tmp_path / "sample.txt").write_text(
        "-----BEGIN PRIVATE KEY-----\n",
        encoding="utf-8",
    )
    findings = scan(tmp_path)
    assert findings and findings[0].kind == "PRIVATE_KEY"


def test_secret_scanner_does_not_skip_env_files(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "API_KEY='this-is-a-realistic-secret-value'\n",
        encoding="utf-8",
    )
    findings = scan(tmp_path)
    assert findings and findings[0].path == ".env"
