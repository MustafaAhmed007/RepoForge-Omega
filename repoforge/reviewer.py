from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from .evidence import EvidenceBundle
from .providers import ModelRequest,provider_from_environment
@dataclass(frozen=True,slots=True)
class ReviewFinding:
    severity:str
    category:str
    statement:str
    evidence:str
@dataclass(slots=True)
class IndependentReview:
    approved:bool
    findings:list[ReviewFinding]
    reviewer:str
    evidence_digest:str
class IndependentReviewer:
    def __init__(self,repo:Path):self.repo=repo.resolve()
    def review(self,evidence:EvidenceBundle,changed_files:list[str]):
        provider=provider_from_environment()
        if getattr(provider,"name","disabled")=="disabled":
            return IndependentReview(False,[ReviewFinding("high","review-unavailable","Independent reviewer is not configured.","No reviewer provider.")],"disabled",evidence.digest())
        response=provider.complete(ModelRequest("You are an independent software reviewer. Do not trust the repair agent.","Return JSON: {approved:boolean, findings:[{severity,category,statement,evidence}]}",
            json.dumps({"evidence":evidence.for_reviewer(),"changed_files":changed_files,"rules":["judge only evidence","reject unsupported root cause","reject weakened tests","reject insufficient evidence"]})))
        try:data=json.loads(response.text)
        except json.JSONDecodeError:return IndependentReview(False,[ReviewFinding("high","invalid-review","Reviewer returned invalid JSON.",response.text[:1000])],provider.name,evidence.digest())
        fs=[ReviewFinding(str(x.get("severity","high")),str(x.get("category","unknown")),str(x.get("statement","")),str(x.get("evidence",""))) for x in data.get("findings",[]) if isinstance(x,dict)]
        return IndependentReview(bool(data.get("approved",False)) and not any(x.severity=="high" for x in fs),fs,provider.name,evidence.digest())