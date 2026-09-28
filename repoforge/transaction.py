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
        self.max_files = max_files
        self.max_patch_bytes = max_patch_bytes
        self._patch_bytes = 0
        self._backup: Path | None = None
        self._touched: list[Path] = []
        self._originals: set[Path] = set()

    def apply(self, patches: list[FilePatch]) -> list[str]:
        if not patches:
            return []

        new_paths = {
            patch.path.replace("\\", "/")
            for patch in patches
            if (self.repo / patch.path).resolve() not in self._originals
        }
        total_paths = {
            str(path.relative_to(self.repo)).replace("\\", "/")
            for path in self._touched
        } | new_paths
        if len(total_paths) > self.max_files:
            raise RuntimeError(
                f"cumulative repair exceeds max_files={self.max_files}"
            )

        patch_bytes = sum(
            len(patch.expected.encode("utf-8"))
            + len(patch.replacement.encode("utf-8"))
            for patch in patches
        )
        if self._patch_bytes + patch_bytes > self.max_patch_bytes:
            raise RuntimeError(
                f"cumulative repair exceeds max_patch_bytes={self.max_patch_bytes}"
            )

        self.patcher.apply(patches, dry_run=True)
        if self._backup is None:
            self._backup = Path(tempfile.mkdtemp(prefix="repoforge-backup-"))

        for patch in patches:
            target = (self.repo / patch.path).resolve()
            if target not in self._originals:
                if target.exists():
                    backup = self._backup / patch.path
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup)
                self._originals.add(target)
            if target not in self._touched:
                self._touched.append(target)

        try:
            changed = self.patcher.apply(patches, dry_run=False)
            self._patch_bytes += patch_bytes
            return changed
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
            elif target.exists() and target in self._originals:
                target.unlink()

        shutil.rmtree(self._backup, ignore_errors=True)
        self._backup = None
        self._touched.clear()
        self._originals.clear()
        self._patch_bytes = 0

    def commit(self) -> None:
        if self._backup is not None:
            shutil.rmtree(self._backup, ignore_errors=True)
            self._backup = None
        self._touched.clear()
        self._originals.clear()
        self._patch_bytes = 0
