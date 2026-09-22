from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .autopilot import Autopilot
from .bootstrap import bootstrap
from .config import ForgeConfig
from .deploy import plan as deployment_plan
from .engine import RepoForge
from .pipeline import Pipeline
from .secrets import scan as scan_secrets


def main() -> None:
    p = argparse.ArgumentParser(prog="repoforge", description="Repository discovery, diagnostics, repair and verification")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("scan", "verify", "doctor"):
        c = sub.add_parser(name); c.add_argument("path", nargs="?", default="."); c.add_argument("--timeout", type=int, default=120)
    c = sub.add_parser("inspect"); c.add_argument("path", nargs="?", default="."); c.add_argument("--out", default=".repoforge")
    c = sub.add_parser("secrets"); c.add_argument("path", nargs="?", default=".")
    c = sub.add_parser("init"); c.add_argument("path", nargs="?", default=".")
    c = sub.add_parser("autopilot"); c.add_argument("path", nargs="?", default="."); c.add_argument("--timeout", type=int, default=120); c.add_argument("--apply", action="store_true")
    c = sub.add_parser("deploy-plan"); c.add_argument("path", nargs="?", default="."); c.add_argument("--timeout", type=int, default=120)
    a = p.parse_args(); repo = Path(a.path).resolve()
    if not repo.is_dir():
        print(f"Invalid repository path: {repo}", file=sys.stderr); raise SystemExit(2)
    if a.command == "init": print(bootstrap(repo)); return
    if a.command == "autopilot":
        result = Autopilot(ForgeConfig.for_repo(repo, timeout_seconds=a.timeout, dry_run=not a.apply)).run()
        print(json.dumps({"findings": result.findings, "proposals": result.proposals, "patched": result.patched, "verification_status": result.verification_status, "readiness": asdict(result.readiness), "rolled_back": result.rolled_back}, indent=2)); return
    if a.command == "inspect":
        fp, findings, proposals = Pipeline(ForgeConfig.for_repo(repo)).inspect(Path(a.out))
        print(json.dumps({"fingerprint": fp.to_dict(), "findings": [asdict(x) for x in findings], "proposals": [asdict(x) for x in proposals]}, indent=2)); return
    if a.command == "secrets":
        findings = scan_secrets(repo); print(json.dumps([asdict(f) for f in findings], indent=2)); raise SystemExit(1 if findings else 0)
    if a.command == "deploy-plan":
        verification = RepoForge(repo).verify(a.timeout)
        print(json.dumps(asdict(deployment_plan(repo, verification)), indent=2)); raise SystemExit(0 if verification.release_status.value == "VERIFIED" else 1)
    forge = RepoForge(repo)
    data = forge.fingerprint().to_dict() if a.command == "scan" else forge.verify(a.timeout).to_dict()
    print(json.dumps(data, indent=2))
    if a.command != "scan" and data["release_status"] != "VERIFIED": raise SystemExit(1)


if __name__ == "__main__":
    main()
