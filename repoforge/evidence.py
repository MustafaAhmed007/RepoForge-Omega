from __future__ import annotations
import hashlib, re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
_SECRET=re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+")
@dataclass(frozen=True, slots=True)
class EvidenceItem:
    kind:str
    source:str
    content:str
    confidence:float=1.0
    metadata:dict[str,str]=field(default_factory=dict)
    def redacted(self)->"EvidenceItem":
        return EvidenceItem(self.kind,self.source,_SECRET.sub(r"\1=[REDACTED]",self.content),self.confidence,dict(self.metadata))
@dataclass(slots=True)
class EvidenceBundle:
    run_id:str
    items:list[EvidenceItem]=field(default_factory=list)
    created_at:str=field(default_factory=lambda:datetime.now(timezone.utc).isoformat())
    def add(self,item:EvidenceItem)->None:self.items.append(item.redacted())
    def digest(self)->str:
        payload="\n".join(f"{x.kind}|{x.source}|{x.content}|{x.confidence}" for x in self.items)
        return hashlib.sha256(payload.encode()).hexdigest()
    def for_reviewer(self)->dict[str,object]:
        return {"run_id":self.run_id,"digest":self.digest(),"items":[asdict(x.redacted()) for x in self.items]}
def file_evidence(repo:Path,relative:str,max_bytes:int=50000)->EvidenceItem|None:
    path=(repo/relative).resolve()
    if not path.is_file() or repo.resolve() not in path.parents:return None
    data=path.read_text(encoding="utf-8",errors="replace")
    return EvidenceItem("source",relative.replace("\\","/"),data[:max_bytes])