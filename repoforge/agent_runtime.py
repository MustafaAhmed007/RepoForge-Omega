from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
@dataclass(frozen=True,slots=True)
class AgentTask:role:str;instruction:str
@dataclass(frozen=True,slots=True)
class AgentResult:role:str;output:str;error:str|None=None
class IndependentAgentRuntime:
    def __init__(self,max_workers:int=4):self.max_workers=max(1,max_workers)
    def run(self,repo:Path,tasks:list[AgentTask],worker:Callable[[Path,AgentTask],str])->list[AgentResult]:
        def invoke(t: AgentTask) -> AgentResult:
            try:return AgentResult(t.role,worker(repo,t))
            except Exception as e:return AgentResult(t.role,"",str(e))
        with ThreadPoolExecutor(max_workers=min(self.max_workers,len(tasks) or 1)) as pool:return list(pool.map(invoke,tasks))