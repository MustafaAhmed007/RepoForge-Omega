from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .patching import FilePatch, SafePatcher


class RepairTransaction:
    """Atomic-ish repair transaction with a filesystem backup and rollback."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()
        self._backup: Path | None = None
        self._touched: list[Path] = []

    def apply(self, patches: list[FilePatch]) -> list[str]:
        if not patches:
            return []
        self._backup = Path(tempfile.mkdtemp(prefix="repoforge-backup-"))
        for patch in patches:
            target = (self.repo / patch.path).resolve()
            if target.exists():
                backup = self._backup / patch.path
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            self._touched.append(target)
        try:
            return SafePatcher(self.repo).apply(patches, dry_run=False)
        except Exception:
            self.rollback()
            raise

    def rollback(self) -> None:
        if self._backup is None:
            return
        for target in self._touched:
            backup = self._backup / target.relative_to(self.repo)
            if backup.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
            elif target.exists():
                target.unlink()
        shutil.rmtree(self._backup, ignore_errors=True)
        self._backup = None
        self._touched.clear()

    def commit(self) -> None:
        if self._backup is not None:
            shutil.rmtree(self._backup, ignore_errors=True)
            self._backup = None
        self._touched.clear()
