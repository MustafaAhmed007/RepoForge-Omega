from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from .runtime import discover_node_runner, discover_python
@dataclass(frozen=True,slots=True)
class CheckSpec:
    name:str
    command:list[str]
    required:bool=True
class ProjectAdapter(Protocol):
    name:str
    def matches(self,repo:Path)->bool:...
    def checks(self,repo:Path)->list[CheckSpec]:...
    def dependency_install(self,repo:Path)->list[str]|None:...
class PythonAdapter:
    name="python"
    def matches(self,r):return any((r/x).exists() for x in ("pyproject.toml","requirements.txt","setup.py"))
    def checks(self,r):
        py,_=discover_python(r); c=[]
        if (r/"tests").is_dir() or (r/"pytest.ini").exists():c.append(CheckSpec("python-tests",[ *py,"-m","pytest"]))
        if (r/"pyproject.toml").exists():c.append(CheckSpec("python-compile",[ *py,"-m","compileall","-q","."]))
        if (r/"pyproject.toml").exists():
            try: has="[tool.ruff" in (r/"pyproject.toml").read_text(encoding="utf-8")
            except OSError: has=False
            if has:c.append(CheckSpec("python-ruff",[ *py,"-m","ruff","check","."]))
        if (r/"benchmarks"/"run.py").exists():c.append(CheckSpec("python-benchmarks",[ *py,"-m","benchmarks.run"]))
        return c
    def dependency_install(self,r):
        py,_=discover_python(r)
        return [*py,"-m","pip","install","-e",".[dev]"] if (r/"pyproject.toml").exists() else ([*py,"-m","pip","install","-r","requirements.txt"] if (r/"requirements.txt").exists() else None)
class NodeAdapter:
    name="node"
    def matches(self,r):return (r/"package.json").exists()
    def checks(self,r):
        try:s=json.loads((r/"package.json").read_text(encoding="utf-8")).get("scripts",{})
        except (OSError,json.JSONDecodeError):s={}
        runner,_=discover_node_runner(r); out=[]
        for k,cmd in (("lint",[runner,"run","lint"]),("typecheck",[runner,"run","typecheck"]),("test",[runner,"test"]),("build",[runner,"run","build"])):
            if k in s:out.append(CheckSpec(f"{runner}-{k}",cmd))
        return out
    def dependency_install(self,r):
        runner,_=discover_node_runner(r)
        return [runner,"install","--frozen-lockfile"] if runner=="pnpm" else (["yarn","install","--immutable"] if runner=="yarn" else (["npm","ci"] if (r/"package-lock.json").exists() else ["npm","install"]))
class GoAdapter:
    name="go"
    def matches(self,r):return (r/"go.mod").exists()
    def checks(self,r):return [CheckSpec("go-test",["go","test","./..."]),CheckSpec("go-build",["go","build","./..."])]
    def dependency_install(self,r):return ["go","mod","download"]
class RustAdapter:
    name="rust"
    def matches(self,r):return (r/"Cargo.toml").exists()
    def checks(self,r):return [CheckSpec("cargo-check",["cargo","check"]),CheckSpec("cargo-test",["cargo","test"])]
    def dependency_install(self,r):return ["cargo","fetch"]
class JavaAdapter:
    name="java"
    def matches(self,r):return (r/"pom.xml").exists() or (r/"build.gradle").exists() or (r/"build.gradle.kts").exists()
    def checks(self,r):return [CheckSpec("maven-test",["mvn","test"])] if (r/"pom.xml").exists() else [CheckSpec("gradle-test",["gradle","test"])]
    def dependency_install(self,r):return None
class DotNetAdapter:
    name="dotnet"
    def matches(self,r):return any(r.glob("*.sln")) or any(r.glob("*.csproj"))
    def checks(self,r):return [CheckSpec("dotnet-test",["dotnet","test"]),CheckSpec("dotnet-build",["dotnet","build","--no-restore"])]
    def dependency_install(self,r):return ["dotnet","restore"]
ADAPTERS=(PythonAdapter(),NodeAdapter(),GoAdapter(),RustAdapter(),JavaAdapter(),DotNetAdapter())
def adapters_for(repo):return [a for a in ADAPTERS if a.matches(repo)]
def discover_checks(repo):
    out=[];seen=set()
    for a in adapters_for(repo):
        for c in a.checks(repo):
            if c.name not in seen:out.append(c);seen.add(c.name)
    return out