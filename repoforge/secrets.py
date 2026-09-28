from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SecretFinding:
    path: str
    line: int
    kind: str


PATTERNS = (
    ("PRIVATE_KEY", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS_ACCESS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    (
        "GENERIC_TOKEN",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*["'][^"']{12,}["']"
        ),
    ),
)
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}


def scan(repo: Path) -> list[SecretFinding]:
    repo = repo.resolve()
    findings: list[SecretFinding] = []
    for path in repo.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for number, line in enumerate(text.splitlines(), 1):
            for kind, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(SecretFinding(str(path.relative_to(repo)), number, kind))
    return findings
