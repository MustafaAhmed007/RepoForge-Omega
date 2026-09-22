from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from .diagnostics import DiagnosticFinding
from .repair import RepairProposal
from .models import RepositoryFingerprint

def write_json(path:Path, fingerprint:RepositoryFingerprint, findings:list[DiagnosticFinding], proposals:list[RepairProposal])->None:
    payload={
        'fingerprint':asdict(fingerprint),
        'findings':[asdict(x) for x in findings],
        'repair_proposals':[asdict(x) for x in proposals],
    }
    path.write_text(json.dumps(payload,indent=2),encoding='utf-8')

def write_markdown(path:Path, fingerprint:RepositoryFingerprint, findings:list[DiagnosticFinding], proposals:list[RepairProposal])->None:
    lines=['# RepoForge Report','',f"Path: `{fingerprint.path}`",f"Languages: {', '.join(fingerprint.languages) or 'unknown'}",f"Frameworks: {', '.join(fingerprint.frameworks) or 'unknown'}",'', '## Findings','']
    if not findings: lines.append('No diagnostic findings detected.')
    for f in findings: lines.extend([f"### [{f.severity.upper()}] {f.code}",f.message,'',f"Evidence: {f.evidence}",'',f"Remediation: {f.remediation}",''])
    lines += ['## Repair proposals','']
    for p in proposals: lines.extend([f'- **{p.action}** — {p.rationale}'])
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
