from pathlib import Path

import pytest

from repoforge.patching import FilePatch
from repoforge.transaction import RepairTransaction


def test_transaction_rolls_back_on_failure(tmp_path: Path):
    target = tmp_path / "x.txt"
    target.write_text("before", encoding="utf-8")
    tx = RepairTransaction(tmp_path)
    tx.apply([FilePatch("x.txt", "before", "after")])
    assert target.read_text(encoding="utf-8") == "after"
    tx.rollback()
    assert target.read_text(encoding="utf-8") == "before"


def test_transaction_rolls_back_all_iterations(tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text("one\ntwo\n", encoding="utf-8")
    transaction = RepairTransaction(tmp_path, max_files=2, max_patch_bytes=1000)

    transaction.apply([FilePatch("module.py", "one\ntwo\n", "ONE\ntwo\n")])
    transaction.apply([FilePatch("module.py", "ONE\ntwo\n", "ONE\nTWO\n")])

    assert target.read_text(encoding="utf-8") == "ONE\nTWO\n"
    transaction.rollback()

    assert target.read_text(encoding="utf-8") == "one\ntwo\n"


def test_transaction_enforces_cumulative_file_limit(tmp_path: Path) -> None:
    (tmp_path / "one.py").write_text("one\n", encoding="utf-8")
    (tmp_path / "two.py").write_text("two\n", encoding="utf-8")
    transaction = RepairTransaction(tmp_path, max_files=1, max_patch_bytes=1000)

    transaction.apply([FilePatch("one.py", "one\n", "ONE\n")])

    with pytest.raises(RuntimeError, match="cumulative repair exceeds max_files"):
        transaction.apply([FilePatch("two.py", "two\n", "TWO\n")])

    transaction.rollback()
    assert (tmp_path / "one.py").read_text(encoding="utf-8") == "one\n"
    assert (tmp_path / "two.py").read_text(encoding="utf-8") == "two\n"


def test_transaction_enforces_cumulative_patch_bytes(tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text("one\ntwo\n", encoding="utf-8")
    transaction = RepairTransaction(tmp_path, max_files=2, max_patch_bytes=20)

    transaction.apply([FilePatch("module.py", "one\ntwo\n", "ONE\ntwo\n")])

    with pytest.raises(RuntimeError, match="cumulative repair exceeds max_patch_bytes"):
        transaction.apply([FilePatch("module.py", "ONE\ntwo\n", "ONE\nTWO\n")])

    transaction.rollback()
    assert target.read_text(encoding="utf-8") == "one\ntwo\n"
