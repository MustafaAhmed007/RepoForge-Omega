from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .models import VerificationReport
from .security import assess_command
@dataclass(frozen=True,slots=True)
class DeploymentAction:
    command:list[str];allowed:bool;reason:str|None=None
class DeploymentExecutor:
    def plan(self,repo:Path,verification:VerificationReport):
        if verification.release_status.value!="VERIFIED":return [DeploymentAction([],False,"Deployment requires VERIFIED deterministic checks.")]
        if (repo/"docker-compose.yml").exists() or (repo/"compose.yml").exists():cmd=["docker","compose","up","-d","--build"]
        elif (repo/"vercel.json").exists():cmd=["vercel","--prod"]
        else:return [DeploymentAction([],False,"No supported deployment target detected.")]
        ok,reason=assess_command(cmd);return [DeploymentAction(cmd,ok,reason)]
    def execute(self,action:DeploymentAction,approved=False):
        if not approved:raise PermissionError("Deployment execution requires explicit approval.")
        if not action.allowed:raise PermissionError(action.reason or "Deployment action is blocked.")
        import subprocess
        return subprocess.run(action.command,check=False).returncode
