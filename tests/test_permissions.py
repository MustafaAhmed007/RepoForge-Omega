from pathlib import Path
import pytest
from repoforge.permissions import PermissionPolicy


def test_write_requires_explicit_permission(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        PermissionPolicy().authorize_write(tmp_path, tmp_path / "x.txt")
