from __future__ import annotations
import argparse,json,sys
from dataclasses import asdict
from pathlib import Path
from .engine import RepoForge
from .config import ForgeConfig
from .pipeline import Pipeline
from .secrets import scan as scan_secrets
from .bootstrap import bootstrap

def main()->None:
    p=argparse.ArgumentParser(prog='repoforge',description='Repository discovery, diagnostics, verification and repair planning')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('scan','verify','doctor'):
        c=sub.add_parser(name); c.add_argument('path',nargs='?',default='.'); c.add_argument('--timeout',type=int,default=120); c.add_argument('--json',action='store_true')
    c=sub.add_parser('inspect'); c.add_argument('path',nargs='?',default='.'); c.add_argument('--out',default='.repoforge')
    c=sub.add_parser('secrets'); c.add_argument('path',nargs='?',default='.'); c.add_argument('--json',action='store_true')
    c=sub.add_parser('init'); c.add_argument('path',nargs='?',default='.')
    a=p.parse_args(); repo=Path(a.path).resolve()
    if not repo.is_dir(): print(f'Invalid repository path: {repo}',file=sys.stderr); raise SystemExit(2)
    if a.command=='init': print(bootstrap(repo)); return
    if a.command=='inspect':
        fp,findings,proposals=Pipeline(ForgeConfig.for_repo(repo)).inspect(Path(a.out))
        print(json.dumps({'languages':fp.languages,'frameworks':fp.frameworks,'findings':[x.code for x in findings],'proposals':[x.action for x in proposals]},indent=2)); return
    if a.command=='secrets':
        findings=scan_secrets(repo); print(json.dumps([asdict(f) for f in findings],indent=2)); raise SystemExit(1 if findings else 0)
    forge=RepoForge(repo); data=forge.fingerprint().to_dict() if a.command=='scan' else forge.verify(a.timeout).to_dict()
    print(json.dumps(data,indent=2))
    if a.command!='scan' and data['release_status']!='VERIFIED': raise SystemExit(1)

if __name__=='__main__': main()
