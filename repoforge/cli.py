from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from .engine import RepoForge

def main()->None:
    p=argparse.ArgumentParser(prog="repoforge",description="Universal repository engineering system")
    sub=p.add_subparsers(dest="command",required=True)
    for name in ("scan","verify","doctor"):
        c=sub.add_parser(name); c.add_argument("path",nargs="?",default="."); c.add_argument("--timeout",type=int,default=120); c.add_argument("--json",action="store_true")
    a=p.parse_args(); forge=RepoForge(Path(a.path))
    if not forge.repo.is_dir(): print(f"Invalid repository path: {forge.repo}",file=sys.stderr); raise SystemExit(2)
    data=forge.fingerprint().to_dict() if a.command=="scan" else forge.verify(a.timeout).to_dict()
    print(json.dumps(data,indent=2) if a.json else json.dumps(data,indent=2))
    if a.command!="scan" and data["release_status"]!="VERIFIED": raise SystemExit(1)

if __name__=="__main__": main()
