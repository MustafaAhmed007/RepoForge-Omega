from pathlib import Path

import pytest

from repoforge.patching import FilePatch, PatchError, SafePatcher


def test_patch_requires_expected_content(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("old", encoding="utf-8")
    SafePatcher(tmp_path).apply([FilePatch("a.txt", "old", "new")], dry_run=False)
    assert target.read_text(encoding="utf-8") == "new"
    with pytest.raises(PatchError):
        SafePatcher(tmp_path).apply([FilePatch("a.txt", "wrong", "x")], dry_run=True)


def test_existing_tests_are_protected(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    target = tests / "test_demo.py"
    target.write_text("def test_ok(): pass\n", encoding="utf-8")

    with pytest.raises(PatchError, match="existing tests are protected"):
        SafePatcher(tmp_path).apply(
            [
                FilePatch(
                    "tests/test_demo.py",
                    "def test_ok(): pass\n",
                    "def test_ok(): assert False\n",
                )
            ],
            dry_run=True,
        )


def test_patch_count_is_bounded(tmp_path: Path) -> None:
    patches = [FilePatch(f"file-{index}.txt", "", "x") for index in range(6)]

    with pytest.raises(PatchError, match="max_files"):
        SafePatcher(tmp_path, max_files=5).apply(patches, dry_run=True)
