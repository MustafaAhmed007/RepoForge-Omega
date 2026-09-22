from __future__ import annotations
import json
from dataclasses import asdict,dataclass
from datetime import datetime,timezone
from pathlib import Path

@dataclass(slots=True)
class LearningEvent:
    category: str
    outcome: str
    signal: str
    evidence: str
    timestamp: str

class MemoryStore:
    def __init__(self,path:Path): self.path=path
    def append(self,category:str,outcome:str,signal:str,evidence:str)->None:
        event=LearningEvent(category,outcome,signal,evidence,datetime.now(timezone.utc).isoformat())
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('a',encoding='utf-8') as handle: handle.write(json.dumps(asdict(event))+'\n')
    def recent(self,limit:int=50)->list[LearningEvent]:
        if not self.path.exists(): return []
        lines=self.path.read_text(encoding='utf-8').splitlines()[-limit:]
        return [LearningEvent(**json.loads(line)) for line in lines]
