# RepoForge-Omega

RepoForge-Omega is a repository-agnostic engineering agent for discovering project structure, collecting evidence, diagnosing engineering risks, planning repairs, applying safe transactional patches, running deterministic verification, producing auditable reports, and assessing deployment readiness.

## Design contract

RepoForge never treats an AI answer as proof that software is correct. `VERIFIED` requires deterministic evidence. Unknown or unsupported conditions remain `BLOCKED` or `NOT VERIFIED`.

## Pipeline

`DISCOVER -> FINGERPRINT -> DIAGNOSE -> PLAN -> REPAIR -> REGRESSION -> VERIFY -> READINESS -> REPORT`

The implementation includes repository fingerprinting, diagnostics, secret scanning, safe command execution, deterministic verification, repair planning, transactional rollback, optional OpenAI-compatible model assistance, persistent event memory, deployment planning, reports, CI, package builds, and cross-platform bootstrap scripts.

## Install into a target repository

Clone RepoForge and run the installer against the target repository.

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

The installer creates an isolated `.repoforge-venv` and does not replace the target project's runtime.

## CLI

```bash
repoforge scan .
repoforge inspect .
repoforge verify .
repoforge doctor .
repoforge secrets .
repoforge autopilot .              # dry-run by default
repoforge autopilot . --apply     # apply gated deterministic/model patches
repoforge deploy-plan .
```

`inspect` writes `.repoforge/report.json`, `.repoforge/report.md`, and an append-only `.repoforge/events.jsonl` evidence trail.

## Optional model assistance

RepoForge remains fully usable without a model. To enable an OpenAI-compatible repair planner:

```text
REPOFORGE_PROVIDER=openai
REPOFORGE_API_KEY=<secret>
REPOFORGE_ENDPOINT=https://api.openai.com/v1
REPOFORGE_MODEL=<approved-model>
```

Model-generated patches are constrained to exact `expected -> replacement` file patches and must still pass deterministic verification. A failed verification causes transactional rollback.

## Safety model

- subprocess execution uses `shell=False`
- destructive commands are blocked by default
- network/package mutation is not silently performed by the verifier
- repository contents are treated as untrusted input
- patch paths cannot escape the target repository
- patches use exact preconditions
- failed repairs roll back when possible
- secrets are scanned separately
- deterministic verification is the release authority

## Verification

GitHub Actions validates Python 3.10, 3.11, and 3.12 with linting, type checking, tests, compilation, and package building. The repository also contains a sample project and regression tests for discovery, diagnostics, repair, rollback, memory, readiness, secrets, and end-to-end execution.

## Limitations

No tool can truthfully guarantee that arbitrary software is permanently bug-free. RepoForge therefore reports evidence-backed states rather than inventing certainty. Browser-specific, proprietary infrastructure, credentials, production deployment, and unsupported language ecosystems require an appropriate adapter and environment.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy repoforge
pytest
python -m build
```

## Commercialization

The core can remain open source while paid layers provide managed repository scans, private runners, organization policies, deployment integrations, audit history, compliance evidence, and team-level governance.
