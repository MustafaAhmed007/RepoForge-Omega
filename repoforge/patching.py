from __future__ import annotations
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
    def __init__(self,repo:Path): self.repo=repo.resolve()
    def apply(self,patches:list[FilePatch],dry_run:bool=True)->list[str]:
        changed=[]
        for patch in patches:
            target=(self.repo/patch.path).resolve()
            if self.repo not in target.parents and target != self.repo: raise PatchError(f'path escapes repository: {patch.path}')
            current=target.read_text(encoding='utf-8') if target.exists() else ''
            if current != patch.expected: raise PatchError(f'precondition mismatch: {patch.path}')
            changed.append(patch.path)
        if not dry_run:
            for patch in patches:
                target=self.repo/patch.path; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(patch.replacement,encoding='utf-8')
        return changed
