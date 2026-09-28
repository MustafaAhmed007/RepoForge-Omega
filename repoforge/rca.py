from __future__ import annotations
import ast,re
from dataclasses import dataclass,field
from pathlib import Path
from .evidence import EvidenceBundle,EvidenceItem
from .models import VerificationReport
@dataclass(frozen=True,slots=True)
class Hypothesis:
    statement:str
    evidence:list[str]
    confidence:float
    category:str
@dataclass(slots=True)
class RootCauseAnalysis:
    run_id:str
    failure:str
    hypotheses:list[Hypothesis]=field(default_factory=list)
    affected_files:list[str]=field(default_factory=list)
    reproduction:list[str]=field(default_factory=list)
    missing_evidence:list[str]=field(default_factory=list)
    confidence:float=0.0
    def primary(self):return max(self.hypotheses,key=lambda h:h.confidence,default=None)
class RootCauseAnalysisEngine:
    def __init__(self,repo:Path):self.repo=repo.resolve()
    def analyze(self, verification: VerificationReport, evidence: EvidenceBundle) -> RootCauseAnalysis:
        failures=[c for c in verification.checks if c.status.value in {"FAIL","BLOCKED"}]
        if not failures:return RootCauseAnalysis(evidence.run_id,"No failing deterministic checks.")
        check=failures[0]; output=(check.stdout+"\n"+check.stderr).strip()
        affected=re.findall(r"(?m)([A-Za-z0-9_./\\-]+\.py):\d+",output); hs=[]
        if "ModuleNotFoundError" in output or "ImportError" in output:hs.append(Hypothesis("The target runtime is missing a dependency.",["import/module error"],.95,"environment"))
        if re.search(r"AssertionError|assert .*? == .*",output,re.I):hs.append(Hypothesis("Implementation behavior differs from an explicit test contract.",["assertion failure"],.8,"behavior"))
        node=re.search(r"([A-Za-z0-9_./\\-]+\.py::[A-Za-z0-9_]+)",output)
        if node:
            test=node.group(1); affected.append(test.split("::")[0]); symbol=test.split("::")[-1]
            for p in self._find_symbol(symbol):
                affected.append(p);hs.append(Hypothesis(f"Implementation associated with '{symbol}' is a candidate root-cause location.",[test,p],.7,"localization"))
        evidence.add(EvidenceItem("failure",check.name,output[-12000:]))
        for p in sorted(set(affected))[:20]:
            f=(self.repo/p).resolve()
            if f.is_file() and self.repo in f.parents:evidence.add(EvidenceItem("source",p,f.read_text(encoding="utf-8",errors="replace")[:50000],.8))
        return RootCauseAnalysis(evidence.run_id,f"{check.name} failed",hs,sorted(set(affected)),[check.name],max((h.confidence for h in hs), default=0.0))
    def _find_symbol(self, symbol: str) -> list[str]:
        out=[]
        for p in self.repo.rglob("*.py"):
            if any(x in {".git",".venv","venv",".repoforge","__pycache__"} for x in p.parts):continue
            try:t=ast.parse(p.read_text(encoding="utf-8",errors="replace"))
            except (OSError,SyntaxError):continue
            if any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name==symbol for n in ast.walk(t)):out.append(str(p.relative_to(self.repo)).replace("\\","/"))
        return out[:10]