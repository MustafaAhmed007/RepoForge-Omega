from __future__ import annotations
import json,uuid
from pathlib import Path
from .fingerprint import detect
from .models import CheckResult,GateStatus,ReleaseStatus,VerificationReport
from .runner import run_check

class RepoForge:
    def __init__(self,repo:Path): self.repo=repo.resolve()
    def fingerprint(self): return detect(self.repo)
    def discover_checks(self):
        fp=self.fingerprint(); checks=[]
        if "Python" in fp.languages:
            if (self.repo/"tests").is_dir() or (self.repo/"pytest.ini").exists(): checks.append(("python-tests",["python","-m","pytest"]))
            if (self.repo/"pyproject.toml").exists(): checks.append(("python-compile",["python","-m","compileall","-q","."]))
        if "JavaScript" in fp.languages or "TypeScript" in fp.languages:
            pkg=self.repo/"package.json"
            if pkg.exists():
                try:scripts=json.loads(pkg.read_text(encoding="utf-8")).get("scripts",{})
                except (OSError,json.JSONDecodeError): scripts={}
                for key,cmd in (("lint",["npm","run","lint"]),("typecheck",["npm","run","typecheck"]),("test",["npm","test"]),("build",["npm","run","build"])):
                    if key in scripts: checks.append((f"npm-{key}",cmd))
        if "Go" in fp.languages and (self.repo/"go.mod").exists(): checks += [("go-test",["go","test","./..."]),("go-build",["go","build","./..."])]
        if "Rust" in fp.languages and (self.repo/"Cargo.toml").exists(): checks += [("cargo-check",["cargo","check"]),("cargo-test",["cargo","test"])]
        return checks
    def verify(self,timeout_s=120):
        fp=self.fingerprint(); checks=[run_check(n,c,self.repo,timeout_s) for n,c in self.discover_checks()]
        if not checks: checks=[CheckResult("verification",GateStatus.BLOCKED,None,0,reason="no deterministic verification commands discovered")]
        blockers=[c.name for c in checks if c.status in {GateStatus.FAIL,GateStatus.BLOCKED}]
        status=ReleaseStatus.BLOCKED if any(c.status==GateStatus.BLOCKED for c in checks) else ReleaseStatus.NOT_VERIFIED if blockers else ReleaseStatus.VERIFIED
        rec=[]
        if not fp.test_systems: rec.append("Add deterministic tests appropriate to the detected application.")
        return VerificationReport(fp,checks,status,blockers,rec,uuid.uuid4().hex)
