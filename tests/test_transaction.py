from pathlib import Path

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
