from __future__ import annotations
import ast
from dataclasses import dataclass,field
from pathlib import Path
@dataclass(slots=True)
class DependencyGraph:
    edges:dict[str,set[str]]=field(default_factory=dict)
    def add(self,source,target):self.edges.setdefault(source,set()).add(target)
    def dependencies_of(self,source):return sorted(self.edges.get(source,set()))
def build_python_graph(repo:Path):
    g=DependencyGraph()
    for p in repo.rglob("*.py"):
        if any(x in {".git",".venv","venv",".repoforge","__pycache__"} for x in p.parts):continue
        rel=str(p.relative_to(repo)).replace("\\","/")
        try:t=ast.parse(p.read_text(encoding="utf-8",errors="replace"))
        except (OSError,SyntaxError):continue
        for n in ast.walk(t):
            if isinstance(n,ast.Import):
                for x in n.names:g.add(rel,x.name)
            elif isinstance(n,ast.ImportFrom) and n.module:g.add(rel,n.module)
    return g
