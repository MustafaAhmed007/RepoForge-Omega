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
from .orchestrator import Orchestrator
from .pipeline import Pipeline
from .secrets import scan as scan_secrets


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="repoforge",
        description="Autonomous repository engineering and deployment-readiness platform",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("scan", "verify", "doctor"):
        command = sub.add_parser(name)
        command.add_argument("path", nargs="?", default=".")
        command.add_argument("--timeout", type=int, default=120)

    command = sub.add_parser("inspect")
    command.add_argument("path", nargs="?", default=".")
    command.add_argument("--out", default=".repoforge")
    command.add_argument("--timeout", type=int, default=120)
    command.add_argument(
        "--verify",
        action="store_true",
        help="Run deterministic checks and include their failures in diagnostics.",
    )

    command = sub.add_parser("secrets")
    command.add_argument("path", nargs="?", default=".")

    command = sub.add_parser("init")
    command.add_argument("path", nargs="?", default=".")

    command = sub.add_parser("autopilot")
    command.add_argument("path", nargs="?", default=".")
    command.add_argument("--timeout", type=int, default=120)
    command.add_argument("--apply", action="store_true")
    command.add_argument("--allow-dirty-files", action="store_true")

    command = sub.add_parser("goal")
    command.add_argument("path", nargs="?", default=".")
    command.add_argument("--timeout", type=int, default=120)
    command.add_argument("--apply", action="store_true")
    command.add_argument("--max-iterations", type=int, default=3)
    command.add_argument("--allow-dirty-files", action="store_true")

    command = sub.add_parser("deploy-plan")
    command.add_argument("path", nargs="?", default=".")
    command.add_argument("--timeout", type=int, default=120)

    args = parser.parse_args()
    repo = Path(args.path).resolve()
    if not repo.is_dir():
        print(f"Invalid repository path: {repo}", file=sys.stderr)
        raise SystemExit(2)

    if args.command == "init":
        print(bootstrap(repo))
        return

    if args.command == "autopilot":
        result = Autopilot(
            ForgeConfig.for_repo(
                repo,
                timeout_seconds=args.timeout,
                dry_run=not args.apply,
                allow_dirty_files=args.allow_dirty_files,
            )
        ).run()
        print(
            json.dumps(
                {
                    "findings": result.findings,
                    "proposals": result.proposals,
                    "patched": result.patched,
                    "verification_status": result.verification_status,
                    "readiness": asdict(result.readiness),
                    "rolled_back": result.rolled_back,
                },
                indent=2,
            )
        )
        return

    if args.command == "goal":
        config = ForgeConfig.for_repo(
            repo,
            timeout_seconds=args.timeout,
            dry_run=not args.apply,
            max_goal_iterations=args.max_iterations,
            allow_dirty_files=args.allow_dirty_files,
        )
        result = Orchestrator(config).run()
        print(
            json.dumps(
                {
                    "goal": "make any given repository deployment-ready",
                    "goal_id": result.goal_id,
                    "goal_status": result.goal_status,
                    "verification_status": result.verification_status,
                    "readiness": asdict(result.readiness),
                    "iterations": result.iterations,
                    "patched": result.patched,
                    "blockers": result.blockers,
                    "goal_state": str(repo / ".repoforge" / "goal.json"),
                },
                indent=2,
            )
        )
        raise SystemExit(0 if result.goal_status == "VERIFIED" else 1)

    if args.command == "inspect":
        verification = RepoForge(repo).verify(args.timeout) if args.verify else None
        fp, findings, proposals = Pipeline(ForgeConfig.for_repo(repo)).inspect(
            Path(args.out),
            verification=verification,
        )
        print(
            json.dumps(
                {
                    "fingerprint": fp.to_dict(),
                    "findings": [asdict(item) for item in findings],
                    "proposals": [asdict(item) for item in proposals],
                },
                indent=2,
            )
        )
        if args.verify and verification and verification.release_status.value != "VERIFIED":
            raise SystemExit(1)
        return

    if args.command == "secrets":
        secret_findings = scan_secrets(repo)
        print(json.dumps([asdict(item) for item in secret_findings], indent=2))
        raise SystemExit(1 if secret_findings else 0)

    if args.command == "deploy-plan":
        verification = RepoForge(repo).verify(args.timeout)
        print(json.dumps(asdict(deployment_plan(repo, verification)), indent=2))
        raise SystemExit(0 if verification.release_status.value == "VERIFIED" else 1)

    forge = RepoForge(repo)
    data = forge.fingerprint().to_dict() if args.command == "scan" else forge.verify(args.timeout).to_dict()
    print(json.dumps(data, indent=2))
    if args.command != "scan" and data["release_status"] != "VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
