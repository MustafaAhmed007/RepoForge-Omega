from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .patching import FilePatch, SafePatcher


class RepairTransaction:
    """Filesystem transaction with bounded patching and rollback."""

    def __init__(
        self,
        repo: Path,
        *,
        max_files: int = 5,
        max_patch_bytes: int = 100_000,
        allow_dirty_files: bool = False,
    ) -> None:
        self.repo = repo.resolve()
        self.patcher = SafePatcher(
            self.repo,
            max_files=max_files,
            max_patch_bytes=max_patch_bytes,
            allow_dirty_files=allow_dirty_files,
        )
        self._backup: Path | None = None
        self._touched: list[Path] = []

    def apply(self, patches: list[FilePatch]) -> list[str]:
        if not patches:
            return []

        self.patcher.apply(patches, dry_run=True)
        self._backup = Path(tempfile.mkdtemp(prefix="repoforge-backup-"))

        for patch in patches:
            target = (self.repo / patch.path).resolve()
            if target.exists():
                backup = self._backup / patch.path
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            self._touched.append(target)

        try:
            return self.patcher.apply(patches, dry_run=False)
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
