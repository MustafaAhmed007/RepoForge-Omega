from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .fingerprint import detect
from .models import RepositoryFingerprint

@dataclass(slots=True)
class DiagnosticFinding:
    code: str
    severity: str
    message: str
    evidence: str
    remediation: str

class DiagnosticEngine:
    def __init__(self, repo: Path):
        self.repo = repo.resolve()

    def run(self) -> tuple[RepositoryFingerprint, list[DiagnosticFinding]]:
        fp = detect(self.repo)
        findings: list[DiagnosticFinding] = []
        if not fp.languages:
            findings.append(DiagnosticFinding('NO_LANGUAGE','high','No recognized source language detected','fingerprint.languages=[]','Add or configure a supported project language.'))
        if not fp.test_systems:
            findings.append(DiagnosticFinding('NO_TESTS','medium','No test system was detected','fingerprint.test_systems=[]','Add deterministic tests.'))
        if fp.environment_files and '.env.example' not in fp.environment_files and '.env.template' not in fp.environment_files:
            findings.append(DiagnosticFinding('ENV_CONTRACT','medium','Environment files exist without a template contract',','.join(fp.environment_files),'Provide a sanitized environment template.'))
        if (self.repo / 'package.json').exists() and not any((self.repo / x).exists() for x in ('package-lock.json','pnpm-lock.yaml','yarn.lock')):
            findings.append(DiagnosticFinding('UNLOCKED_NODE_DEPS','medium','Node dependency manifest has no lockfile','package.json exists','Commit a package-manager lockfile.'))
        if not (self.repo / '.gitignore').exists():
            findings.append(DiagnosticFinding('NO_GITIGNORE','low','No .gitignore was detected','.gitignore missing','Add an appropriate ignore policy.'))
        return fp, findings
