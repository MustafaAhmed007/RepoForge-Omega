from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class FilePatch:
    path: str
    expected: str
    replacement: str


class PatchError(RuntimeError):
    pass


class SafePatcher:
    def __init__(
        self,
        repo: Path,
        *,
        max_files: int = 5,
        max_patch_bytes: int = 100_000,
        allow_dirty_files: bool = False,
    ):
        self.repo = repo.resolve()
        self.max_files = max_files
        self.max_patch_bytes = max_patch_bytes
        self.allow_dirty_files = allow_dirty_files

    def _git_dirty(self, relative: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", relative],
                cwd=self.repo,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError:
            return False
        return bool(result.stdout.strip())

    def _validate(self, patches: list[FilePatch]) -> list[tuple[FilePatch, Path]]:
        if len(patches) > self.max_files:
            raise PatchError(f"patch set exceeds max_files={self.max_files}")

        seen: set[str] = set()
        validated: list[tuple[FilePatch, Path]] = []
        total_bytes = 0

        for patch in patches:
            relative = patch.path.replace("\\", "/")
            is_windows_absolute = len(relative) >= 2 and relative[1] == ":"
            if (
                not relative
                or relative in {".", ".."}
                or relative.startswith("/")
                or relative.startswith("../")
                or is_windows_absolute
            ):
                raise PatchError(f"unsafe patch path: {patch.path}")
            if relative in seen:
                raise PatchError(f"duplicate patch path: {patch.path}")
            seen.add(relative)

            target = (self.repo / relative).resolve()
            if self.repo not in target.parents:
                raise PatchError(f"path escapes repository: {patch.path}")
            if any(
                part in {".git", ".venv", "venv", "node_modules", ".repoforge"}
                for part in target.parts
            ):
                raise PatchError(f"protected generated/runtime path: {patch.path}")
            if target.name.endswith(".egg-info"):
                raise PatchError(f"protected generated path: {patch.path}")

            if target.exists() and not target.is_file():
                raise PatchError(f"patch target is not a regular file: {patch.path}")
            if target.exists() and not self.allow_dirty_files and self._git_dirty(relative):
                raise PatchError(f"target has pre-existing git changes: {patch.path}")

            if relative.startswith("tests/") and target.exists():
                raise PatchError(f"existing tests are protected from mutation: {patch.path}")

            current = target.read_text(encoding="utf-8") if target.exists() else ""
            if current != patch.expected:
                raise PatchError(f"precondition mismatch: {patch.path}")

            total_bytes += len(patch.expected.encode("utf-8")) + len(
                patch.replacement.encode("utf-8")
            )
            if total_bytes > self.max_patch_bytes:
                raise PatchError(f"patch set exceeds max_patch_bytes={self.max_patch_bytes}")

            if "\x00" in patch.replacement:
                raise PatchError(f"binary content is not allowed: {patch.path}")

            validated.append((patch, target))

        return validated

    def apply(self, patches: list[FilePatch], dry_run: bool = True) -> list[str]:
        validated = self._validate(patches)
        changed = [patch.path for patch, _ in validated]

        if not dry_run:
            for patch, target in validated:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(patch.replacement, encoding="utf-8")

        return changed
