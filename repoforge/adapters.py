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
    def matches(self, repo: Path) -> bool:return any((repo/x).exists() for x in ("pyproject.toml","requirements.txt","setup.py")) or (repo/"tests").is_dir() or any(repo.glob("*.py"))
    def checks(self, repo: Path) -> list[CheckSpec]:
        py,_=discover_python(repo); c: list[CheckSpec]=[]
        if (repo/"tests").is_dir() or (repo/"pytest.ini").exists():c.append(CheckSpec("python-tests",[ *py,"-m","pytest"]))
        if (repo/"pyproject.toml").exists() or any(repo.glob("*.py")) or (repo/"tests").is_dir():c.append(CheckSpec("python-compile",[ *py,"-m","compileall","-q","."]))
        if (repo/"pyproject.toml").exists():
            try: has="[tool.ruff" in (repo/"pyproject.toml").read_text(encoding="utf-8")
            except OSError: has=False
            if has:c.append(CheckSpec("python-ruff",[ *py,"-m","ruff","check","."]))
        if (repo/"benchmarks"/"run.py").exists():c.append(CheckSpec("python-benchmarks",[ *py,"-m","benchmarks.run"]))
        return c
    def dependency_install(self, repo: Path) -> list[str] | None:
        py,_=discover_python(repo)
        return [*py,"-m","pip","install","-e",".[dev]"] if (repo/"pyproject.toml").exists() else ([*py,"-m","pip","install","-r","requirements.txt"] if (repo/"requirements.txt").exists() else None)
class NodeAdapter:
    name="node"
    def matches(self, repo: Path) -> bool:return (repo/"package.json").exists()
    def checks(self, repo: Path) -> list[CheckSpec]:
        try:s=json.loads((repo/"package.json").read_text(encoding="utf-8")).get("scripts",{})
        except (OSError,json.JSONDecodeError):s={}
        runner,_=discover_node_runner(repo); out: list[CheckSpec]=[]
        for k,cmd in (("lint",[runner,"run","lint"]),("typecheck",[runner,"run","typecheck"]),("test",[runner,"test"]),("build",[runner,"run","build"])):
            if k in s:out.append(CheckSpec(f"{runner}-{k}",cmd))
        return out
    def dependency_install(self, repo: Path) -> list[str] | None:
        runner,_=discover_node_runner(repo)
        return [runner,"install","--frozen-lockfile"] if runner=="pnpm" else (["yarn","install","--immutable"] if runner=="yarn" else (["npm","ci"] if (repo/"package-lock.json").exists() else ["npm","install"]))
class GoAdapter:
    name="go"
    def matches(self, repo: Path) -> bool:return (repo/"go.mod").exists()
    def checks(self, repo: Path) -> list[CheckSpec]:return [CheckSpec("go-test",["go","test","./..."]),CheckSpec("go-build",["go","build","./..."])]
    def dependency_install(self, repo: Path) -> list[str] | None:return ["go","mod","download"]
class RustAdapter:
    name="rust"
    def matches(self, repo: Path) -> bool:return (repo/"Cargo.toml").exists()
    def checks(self, repo: Path) -> list[CheckSpec]:return [CheckSpec("cargo-check",["cargo","check"]),CheckSpec("cargo-test",["cargo","test"])]
    def dependency_install(self, repo: Path) -> list[str] | None:return ["cargo","fetch"]
class JavaAdapter:
    name="java"
    def matches(self, repo: Path) -> bool:return (repo/"pom.xml").exists() or (repo/"build.gradle").exists() or (repo/"build.gradle.kts").exists()
    def checks(self, repo: Path) -> list[CheckSpec]:return [CheckSpec("maven-test",["mvn","test"])] if (repo/"pom.xml").exists() else [CheckSpec("gradle-test",["gradle","test"])]
    def dependency_install(self, repo: Path) -> list[str] | None:return None
class DotNetAdapter:
    name="dotnet"
    def matches(self, repo: Path) -> bool:return any(repo.glob("*.sln")) or any(repo.glob("*.csproj"))
    def checks(self, repo: Path) -> list[CheckSpec]:return [CheckSpec("dotnet-test",["dotnet","test"]),CheckSpec("dotnet-build",["dotnet","build","--no-restore"])]
    def dependency_install(self, repo: Path) -> list[str] | None:return ["dotnet","restore"]
class MakeAdapter:
    name = "make"
    def matches(self, repo: Path) -> bool:
        return (repo / "Makefile").exists()
    def checks(self, repo: Path) -> list[CheckSpec]:
        text = (repo / "Makefile").read_text(encoding="utf-8", errors="replace")
        targets: list[CheckSpec] = []
        for target in ("test", "check", "lint", "build"):
            if f"{target}:" in text:
                targets.append(CheckSpec(f"make-{target}", ["make", target]))
        return targets
    def dependency_install(self, repo: Path) -> list[str] | None:
        return None

ADAPTERS: tuple[ProjectAdapter, ...]=(PythonAdapter(),NodeAdapter(),GoAdapter(),RustAdapter(),JavaAdapter(),DotNetAdapter(),MakeAdapter())
def adapters_for(repo: Path) -> list[ProjectAdapter]:return [a for a in ADAPTERS if a.matches(repo)]
def discover_checks(repo: Path) -> list[CheckSpec]:
    out: list[CheckSpec] = []
    seen: set[str] = set()
    for a in adapters_for(repo):
        for c in a.checks(repo):
            if c.name not in seen:out.append(c);seen.add(c.name)
    return out