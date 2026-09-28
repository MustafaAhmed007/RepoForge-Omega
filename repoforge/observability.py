from __future__ import annotations
import json,time,uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
@dataclass(slots=True)
class Trace:
    trace_id:str
    operation:str
    started:float
    ended:float=0.0
    attributes:dict[str,str]|None=None
    def finish(self):self.ended=time.perf_counter()
class TraceStore:
    def __init__(self,path:Path):self.path=path
    @contextmanager
    def span(self,operation:str,**attributes:str)->Iterator[Trace]:
        t=Trace(uuid.uuid4().hex,operation,time.perf_counter(),attributes=dict(attributes))
        try:yield t
        finally:
            t.finish();self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.path.open("a",encoding="utf-8") as f:f.write(json.dumps({"trace_id":t.trace_id,"operation":t.operation,"duration_ms":int((t.ended-t.started)*1000),"attributes":t.attributes or {}})+"\n")
