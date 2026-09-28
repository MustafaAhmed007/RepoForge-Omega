from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
@dataclass(frozen=True,slots=True)
class CIWorkflow:
    path:str;provider:str;language:str;commands:list[str]
def discover_ci(repo:Path):
    out=[]
    d=repo/".github"/"workflows"
    if not d.is_dir():return out
    tokens=("pytest","npm ","pnpm ","yarn ","ruff","go test","cargo test","dotnet test","mvn ")
    for p in sorted(d.glob("*.y*ml")):
        text=p.read_text(encoding="utf-8",errors="replace")
        commands=[line.strip()[2:].strip() for line in text.splitlines() if line.strip().startswith("- ") and any(t in line for t in tokens)]
        out.append(CIWorkflow(str(p.relative_to(repo)).replace("\\","/"),"github-actions","multi",commands))
    return out
def workflow_commands(repo:Path):
    return sorted({c for w in discover_ci(repo) for c in w.commands})
