# RepoForge-Omega

RepoForge-Omega is a repository-agnostic engineering agent foundation for discovering project structure, collecting evidence, diagnosing common engineering risks, planning repairs, running deterministic verification, and producing auditable reports.

## Design contract

RepoForge does not claim that an AI answer makes software correct. A release becomes `VERIFIED` only when configured deterministic checks pass. Unknown or unsupported conditions remain `BLOCKED` or `NOT VERIFIED`.

### Pipeline

`DISCOVER -> FINGERPRINT -> DIAGNOSE -> PLAN -> REPAIR -> REGRESSION -> VERIFY -> REPORT`

The current release implements discovery, fingerprinting, deterministic verification, command safety, diagnostics, repair planning, reporting, and cross-platform bootstrap scripts. Mutation-capable repair adapters are intentionally isolated behind explicit approval boundaries.

## Install

From a clone of this repository:

### Linux/macOS

```bash
bash install.sh /path/to/target-repository
/path/to/target-repository/.repoforge-venv/bin/repoforge inspect /path/to/target-repository
```

### Windows PowerShell

```powershell
.\install.ps1 C:\path\to\target-repository
C:\path\to\target-repository\.repoforge-venv\Scripts\repoforge.exe inspect C:\path\to\target-repository
```

## CLI

```bash
repoforge scan .
repoforge verify .
repoforge doctor .
repoforge inspect . --out .repoforge
```

`inspect` writes `.repoforge/report.json` and `.repoforge/report.md`.

## Safety model

- subprocess execution uses `shell=False`
- destructive commands are blocked by default
- network/package mutation is approval-gated
- repository contents are treated as untrusted input
- diagnostics are evidence-producing, not proof of correctness
- repair planning is separate from repair execution

## Roadmap

1. Universal discovery and fingerprinting
2. Diagnostic and verification adapters
3. Sandboxed repair execution with rollback
4. Model/provider adapters
5. Security and dependency intelligence
6. E2E/browser verification adapters
7. Deployment-readiness gates
8. Persistent learning and regression corpus
9. Cross-platform installer and CI bootstrap
10. Adversarial end-to-end verification

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy repoforge
pytest
```

## Commercialization

The core can remain open source while paid layers provide managed repository scans, private runners, team policies, deployment integrations, audit history, and organization-level governance.
