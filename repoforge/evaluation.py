from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .engine import RepoForge
@dataclass(frozen=True,slots=True)
class EvaluationResult:
    checks:int;passed:int;failed:int;blocked:int;release_status:str
class EvaluationEngine:
    def evaluate(self,repo:Path,timeout_s:int=120)->EvaluationResult:
        r=RepoForge(repo).verify(timeout_s)
        return EvaluationResult(len(r.checks),sum(c.status.value=="PASS" for c in r.checks),sum(c.status.value=="FAIL" for c in r.checks),sum(c.status.value=="BLOCKED" for c in r.checks),r.release_status.value)
