from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .config import ForgeConfig
from .engine import RepoForge
from .memory import MemoryStore
from .patching import FilePatch,SafePatcher
from .pipeline import Pipeline
from .readiness import Readiness,assess

@dataclass(slots=True)
class AutopilotResult:
    findings: int
    proposals: int
    patched: list[str]
    verification_status: str
    readiness: Readiness

class Autopilot:
    def __init__(self,config:ForgeConfig): self.config=config
    def run(self,patches:list[FilePatch]|None=None)->AutopilotResult:
        _,findings,proposals=Pipeline(self.config).inspect()
        patched=SafePatcher(self.config.repo).apply(patches or [],dry_run=self.config.dry_run)
        verification=RepoForge(self.config.repo).verify(self.config.timeout_seconds)
        readiness=assess(self.config.repo)
        MemoryStore(self.config.repo/'.repoforge'/'events.jsonl').append('autopilot',verification.release_status.value,f'{len(findings)} findings',f'{len(patched)} patches applied or validated')
        return AutopilotResult(len(findings),len(proposals),patched,verification.release_status.value,readiness)
