from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

@dataclass(slots=True)
class SecretFinding:
    path: str
    line: int
    kind: str

PATTERNS=(
    ('PRIVATE_KEY',re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
    ('AWS_ACCESS_KEY',re.compile(r'AKIA[0-9A-Z]{16}')),
    ('GENERIC_TOKEN',re.compile(r'(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*["\'][^"\']{12,}["\']')),
)
SKIP={'.git','.venv','venv','node_modules','dist','build','__pycache__'}

def scan(repo:Path)->list[SecretFinding]:
    findings=[]
    for p in repo.rglob('*'):
        if not p.is_file() or any(x in SKIP for x in p.parts) or p.name.startswith('.env'):
            continue
        try:text=p.read_text(encoding='utf-8')
        except (OSError,UnicodeDecodeError):
            continue
        for number,line in enumerate(text.splitlines(),1):
            for kind,pattern in PATTERNS:
                if pattern.search(line): findings.append(SecretFinding(str(p.relative_to(repo)),number,kind))
    return findings
