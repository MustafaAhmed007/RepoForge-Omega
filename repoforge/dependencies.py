from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .adapters import adapters_for
@dataclass(frozen=True,slots=True)
class DependencyPlan:
    manager:str
    command:list[str]|None
    reason:str
def plan_dependency_install(repo: Path) -> DependencyPlan:
    a=adapters_for(repo)
    if not a:return DependencyPlan("unknown",None,"No supported adapter matched.")
    return DependencyPlan(a[0].name,a[0].dependency_install(repo),"Derived from target dependency metadata.")
def can_install(repo: Path) -> bool:return plan_dependency_install(repo).command is not None