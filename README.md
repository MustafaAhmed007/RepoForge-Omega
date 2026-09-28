# RepoForge-Omega

> **The repository engineer that turns an unknown codebase into an evidence-backed engineering report — and, when safely possible, a verified repair.**

RepoForge-Omega is a repository-agnostic engineering agent for discovering project structure, collecting evidence, diagnosing engineering risks, planning repairs, applying safe transactional patches, running deterministic verification, producing auditable reports, and assessing deployment readiness.

## What RepoForge actually does

Think of RepoForge as a **technical inspection + repair workshop for software repositories**.

You point it at a project. RepoForge first learns what the project is, then chooses checks appropriate to that project. It does not blindly run one fixed checklist against every codebase.

```text
                 YOUR REPOSITORY
                       │
                       ▼
              ┌─────────────────┐
              │ 1. DISCOVER     │
              │ files, stack,   │
              │ tools, entrypts │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ 2. DIAGNOSE     │
              │ tests, builds,  │
              │ secrets, risks  │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ 3. PLAN         │
              │ evidence-based  │
              │ repair strategy │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ 4. REPAIR       │
              │ gated patches + │
              │ transactional   │
              │ rollback        │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ 5. VERIFY       │
              │ tests + build + │
              │ safety checks   │
              └────────┬────────┘
                       ▼
                 PASS / FAIL
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        VERIFIED            NOT VERIFIED
             │                   │
             ▼                   ▼
        READY REPORT       EVIDENCE + NEXT ACTION
```

## Complete system workflow

RepoForge is designed as a closed engineering loop rather than a single AI coding command.

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         REPOSITORY INPUT                             │
│                 local repo / checked-out project                     │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 1. DISCOVERY                                                         │
│                                                                      │
│ Scan repository boundaries, files, Git state, configuration,         │
│ languages, frameworks, package managers, build systems, tests,      │
│ entry points, environment indicators and deployment signals.        │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 2. FINGERPRINTING                                                    │
│                                                                      │
│ Convert discovery results into a technology/project fingerprint.    │
│ This determines which diagnostics and verification checks make       │
│ sense for this particular repository.                                │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 3. DIAGNOSTICS                                                       │
│                                                                      │
│ Run relevant deterministic checks: linting, type checking, tests,   │
│ compilation, builds, repository diagnostics, secret checks and      │
│ other supported health checks.                                      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 4. EVIDENCE + MEMORY                                                 │
│                                                                      │
│ Store structured findings, command results, observations and run     │
│ events so reports and future decisions are traceable.                │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 5. ROOT-CAUSE / REPAIR PLANNING                                      │
│                                                                      │
│ Turn findings into bounded repair candidates. Each candidate should  │
│ identify its target, expected precondition, intended replacement,    │
│ rationale and verification requirement.                              │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ SAFE TO MODIFY?          │
                    └────────────┬─────────────┘
                                 │
                         YES     │     NO
                         ▼        │      ▼
              ┌────────────────┐  │  BLOCK / REPORT
              │ 6. TRANSACTION │  │
              │AL REPAIR       │  │
              └───────┬────────┘  │
                      │           │
                      ▼           │
              exact precondition │
              + repository bound │
              + controlled patch │
                      │           │
                      ▼           │
              ┌────────────────┐  │
              │ 7. REGRESSION  │  │
              │    VERIFY      │  │
              └───────┬────────┘  │
                      │           │
                 PASS │ FAIL      │
                      │   │       │
                      │   └───────┼──► ROLLBACK
                      ▼           │
              ┌────────────────┐  │
              │ 8. SECURITY    │  │
              │    GATE        │  │
              └───────┬────────┘  │
                      │           │
                      ▼           │
              ┌────────────────┐  │
              │ 9. READINESS   │  │
              │    ASSESSMENT  │  │
              └───────┬────────┘  │
                      │           │
                      ▼           │
              ┌────────────────┐  │
              │ 10. RELEASE    │  │
              │     GATE       │  │
              └───────┬────────┘  │
                      │           │
             ┌────────┼───────────┘
             ▼        ▼
         VERIFIED   NOT VERIFIED / BLOCKED
             │        │
             └────┬───┘
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 11. REPORT + NEXT ACTION                                             │
│                                                                      │
│ Produce human-readable and machine-readable results showing what     │
│ was inspected, what changed, what passed, what failed and what      │
│ remains uncertain.                                                   │
└──────────────────────────────────────────────────────────────────────┘
```

### The simple version

```text
UNDERSTAND → FIND → EXPLAIN → PLAN → FIX → TEST → PROVE → REPORT
```

And when a repair makes things worse:

```text
FIX → TEST FAILS → ROLLBACK → KEEP EVIDENCE → TRY A SAFER PATH
```

This is what makes RepoForge an **engineering loop**, not simply an AI code generator.

## Repository structure

The repository is intentionally modular. Each major responsibility has a focused module so that scanners, repair strategies, model providers, verification logic and reporting can evolve independently.

```text
RepoForge-Omega/
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # Continuous integration and release checks
│
├── examples/
│   └── sample_project/
│       ├── main.py                 # Small target repository for E2E testing
│       └── pyproject.toml          # Sample project metadata
│
├── repoforge/
│   ├── __init__.py                 # Package identity/version
│   ├── __main__.py                 # python -m repoforge entry point
│   ├── autopilot.py                # Autonomous inspection/repair orchestration
│   ├── bootstrap.py                # Target-repository bootstrap helpers
│   ├── cli.py                      # User-facing command-line interface
│   ├── config.py                   # Runtime/configuration handling
│   ├── deploy.py                   # Deployment-readiness planning
│   ├── diagnostics.py              # Evidence collection and diagnostics
│   ├── engine.py                   # Core repository engineering engine
│   ├── fingerprint.py              # Technology/project fingerprinting
│   ├── memory.py                   # Persistent evidence/event memory
│   ├── models.py                   # Shared domain models
│   ├── patching.py                 # Controlled patch application
│   ├── pipeline.py                 # End-to-end pipeline coordination
│   ├── policy.py                   # Safety and execution policies
│   ├── providers.py                # Optional model/provider adapters
│   ├── readiness.py                # Deployment/release readiness checks
│   ├── repair.py                   # Repair planning and repair logic
│   ├── report.py                   # Human/machine-readable reporting
│   ├── runner.py                   # Controlled subprocess execution
│   ├── secrets.py                  # Secret detection
│   ├── security.py                 # Command/security controls
│   ├── transaction.py              # Transaction + rollback mechanics
│   ├── agents.py                   # Specialized agent roles/runtime boundary
│   ├── tasks.py                    # Dependency-aware task graph
│   ├── goals.py                    # Bounded goal lifecycle + durable state snapshot
│   ├── hooks.py                    # Lifecycle event bus
│   ├── permissions.py              # Explicit capability/permission gates
│   ├── integrations.py             # Vendor-neutral integration registry
│   ├── protocols.py                # Protocol endpoint registry
│   ├── browser.py                  # Permission-gated browser adapter boundary
│   ├── router.py                   # Provider locality/preference routing
│   └── orchestrator.py             # Unified control-plane execution
│
├── tests/
│   ├── test_autopilot.py           # Autopilot regression coverage
│   ├── test_deploy.py              # Deployment-readiness tests
│   ├── test_diagnostics.py         # Diagnostic tests
│   ├── test_engine.py              # Core engine tests
│   ├── test_fingerprint.py         # Fingerprinting tests
│   ├── test_memory.py              # Evidence-memory tests
│   ├── test_patching.py            # Patch safety tests
│   ├── test_pipeline.py            # Pipeline integration tests
│   ├── test_readiness.py           # Readiness tests
│   ├── test_repair.py              # Repair tests
│   ├── test_report.py              # Reporting tests
│   ├── test_runner.py              # Execution tests
│   ├── test_secrets.py             # Secret scanner tests
│   ├── test_security.py            # Security policy tests
│   └── test_transaction.py         # Rollback/transaction tests
│
├── install.sh                      # Linux/macOS installer
├── install.ps1                     # Windows PowerShell installer
├── pyproject.toml                  # Python packaging and tool configuration
├── AGENTS.md                       # Repository engineering contract
├── LICENSE                          # Apache License 2.0
├── README.md                       # Project documentation
└── .gitignore                      # Repository hygiene rules
```

### Module responsibilities at a glance

| Module | Responsibility |
|---|---|
| `cli.py` | Human-facing commands and entry points |
| `engine.py` | Core repository engineering coordination |
| `pipeline.py` | Connects the major lifecycle stages |
| `fingerprint.py` | Learns what technology the repository uses |
| `diagnostics.py` | Finds evidence of problems and risks |
| `repair.py` | Creates and evaluates repair candidates |
| `patching.py` | Applies bounded, preconditioned changes |
| `transaction.py` | Makes repair operations reversible |
| `autopilot.py` | Coordinates autonomous execution |
| `providers.py` | Optional AI/model assistance |
| `runner.py` | Executes approved deterministic commands |
| `security.py` | Blocks unsafe command patterns |
| `secrets.py` | Detects likely secret material |
| `memory.py` | Preserves structured run evidence |
| `report.py` | Generates audit-friendly results |
| `readiness.py` | Assesses release/deployment readiness |
| `deploy.py` | Produces deployment plans |
| `policy.py` | Controls what RepoForge is allowed to do |
| `config.py` | Loads runtime configuration |
| `bootstrap.py` | Installs/initializes RepoForge in target repositories |\n| `adapters.py` | Discovers ecosystem-appropriate deterministic checks |\n| `evidence.py` | Builds auditable evidence bundles and digests |\n| `rca.py` | Maps deterministic failures to structured RCA hypotheses |\n| `repair_loop.py` | Runs bounded repair, verification, review, and rollback |\n| `sandbox.py` | Provides temporary-workspace and optional Docker isolation |\n| `dependencies.py` | Plans dependency installation without silent target mutation |\n| `dependency_graph.py` | Builds Python import dependency graphs |\n| `ci.py` | Discovers CI workflow checks |\n| `mcp_client.py` | Provides minimal JSON-RPC stdio integration |\n| `observability.py` | Records trace/span execution evidence |\n| `deployment.py` | Applies explicit deployment execution gates |

## Design contract

RepoForge never treats an AI answer as proof that software is correct. `VERIFIED` requires deterministic evidence. Unknown or unsupported conditions remain `BLOCKED` or `NOT VERIFIED`.

This is the core trust rule:

```text
AI suggestion ≠ proof

Evidence
   ↓
Controlled change
   ↓
Regression verification
   ↓
Release gate
```

## Universal engineering v1\n\nThe v1 engineering layer is adapter-driven: RepoForge fingerprints the target repository, selects applicable ecosystem adapters, discovers deterministic checks, and runs only checks supported by the detected project structure.\n\n```text\nTARGET REPOSITORY → DISCOVERY / FINGERPRINT → ADAPTER SELECTION\n                                      ↓\n                         DETERMINISTIC CHECKS\n                                      ↓\n                                   EVIDENCE\n```\n\nCurrent adapter coverage includes Python, Node/TypeScript, Go, Rust, Java, .NET, and Makefile-driven projects. This is implemented/initial coverage, not a claim of universal support for every language, framework, package manager, or build system.\n\n### Root-cause analysis\n\nWhen verification fails, RepoForge can convert deterministic failure output into structured RCA hypotheses instead of treating an AI explanation as fact.\n\n```text\nVERIFICATION FAILURE → PARSE → CLASSIFY → MAP TEST/SYMBOL\n                                      ↓\n                              MAP SOURCE CANDIDATES\n                                      ↓\n                              COLLECT EVIDENCE\n                                      ↓\n                                RCA HYPOTHESIS\n                                      ↓\n                              REPAIR CANDIDATE\n```\n\nRCA output is hypothesis-level evidence. A hypothesis becomes actionable only through controlled change and subsequent deterministic verification.\n\n### Evidence bundles\n\nRepair and review stages can consume structured evidence containing failure information, command results, relevant source evidence, changed-file information, and an evidence digest. This preserves an auditable chain between observation, proposed repair, and verification.\n\n### Bounded repair loop\n\n```text\nBASELINE VERIFY → RCA → PATCH CANDIDATE → TRANSACTION / DRY RUN\n                                      ↓\n                         POST-REPAIR VERIFY\n                                      ↓\n                         POST-REPAIR EVIDENCE\n                                      ↓\n                         INDEPENDENT REVIEW\n                                      ↓\n                              COMMIT / ROLLBACK\n```\n\nThe repair loop is bounded by maximum attempts, changed-file and patch-size limits, exact preconditions, repository-bound paths, protected runtime/generated areas, existing-test protection, dirty-file policy, and rollback on failed verification.\n\n### Independent review gate\n\nVerification and review are separate responsibilities. The deterministic reviewer checks conditions such as test mutation, diff hygiene, and verification evidence. An optional model reviewer can provide an additional evidence-based assessment.\n\nRepair and review providers can be configured by role. True model independence in production requires a genuinely separate provider/model/credential for the review role; two role names alone do not create independence.\n\n### Current capability boundary\n\n| Capability | Status |\n|---|---|\n| Runtime-aware deterministic verification | Implemented |\n| Python adapter | Implemented |\n| Node/TypeScript adapter | Implemented |\n| Go adapter | Implemented |\n| Rust adapter | Implemented |\n| Java adapter | Initial implementation |\n| .NET adapter | Initial implementation |\n| Makefile adapter | Implemented |\n| Deterministic RCA | Implemented |\n| Bounded transactional repair | Implemented |\n| Independent deterministic review | Implemented |\n| Optional model review | Implemented; production separation is configuration-dependent |\n| Docker execution sandbox | Implemented as an optional stronger boundary |\n| Full MCP protocol lifecycle | Not claimed; current implementation is a minimal JSON-RPC stdio client/boundary |\n| Universal language/build-system coverage | Not claimed |\n| Full CI/CD remediation across providers | Not claimed |\n| Production deployment automation | Limited and explicitly gated |\n\n## End-to-end pipeline

`DISCOVER -> FINGERPRINT -> ADAPT -> DIAGNOSE -> RCA -> PLAN -> REPAIR -> REGRESSION -> REVIEW -> VERIFY -> READINESS -> REPORT`

The implementation includes repository fingerprinting, diagnostics, secret scanning, safe command execution, deterministic verification, repair planning, transactional rollback, optional OpenAI-compatible model assistance, persistent event memory, deployment planning, reports, CI, package builds, and cross-platform bootstrap scripts.

## How a normal run works

### 1. Discover

RepoForge identifies:

- languages
- frameworks
- package managers
- build systems
- test systems
- entry points
- environment files
- deployment indicators
- Git state

### 2. Diagnose

It gathers evidence instead of guessing. Depending on the detected stack, it can discover relevant lint, type-check, test, compilation, and build commands and combine their results with repository-level diagnostics.

### 3. Plan

Findings become structured repair candidates. Each repair should have a reason, target, precondition, and verification requirement.

### 4. Repair

Repairs are deliberately constrained. Exact file preconditions and repository-bound paths reduce accidental modifications. Model assistance is optional rather than a hard dependency.

### 5. Verify

The repaired repository is tested again. If verification fails, the transactional repair path can roll back the change rather than leaving an unverified modification behind.

### 6. Report

RepoForge produces machine-readable and human-readable evidence so another engineer can understand **what was inspected, what changed, what passed, what failed, and what remains uncertain**.

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

## External-repository runtime isolation

When RepoForge verifies another Python repository, it first looks for that repository's own virtual environment:

```text
<target>/.venv/Scripts/python.exe
<target>/venv/Scripts/python.exe
<target>/.venv/bin/python
<target>/venv/bin/python
```

If one is found, deterministic Python checks run inside that target environment rather than inside RepoForge's environment. If none is found, RepoForge falls back to its own interpreter and records that limitation in the verification recommendations.

For Node projects, the verifier selects the package-manager runner from `pnpm-lock.yaml`, `yarn.lock`, or `package-lock.json`.

RepoForge also discovers project-declared deterministic checks such as:

- Python tests
- Python compilation
- Ruff when a Ruff configuration is present
- `benchmarks/run.py` benchmark suites
- Node lint/typecheck/test/build scripts
- Go test/build
- Rust check/test

Use verification-aware inspection when you want diagnostics to include actual failing-check evidence:

```bash
repoforge inspect . --verify
```

`VERIFIED` is never inferred from static inspection alone.

## Autonomous repair safety boundaries

Autonomous repair is bounded by default:

- maximum changed files: 5
- maximum patch payload: 100 KB
- exact precondition matching
- repository-bound paths only
- absolute Windows paths rejected
- generated/runtime directories protected
- existing test files protected from mutation
- pre-existing Git changes on a patch target are rejected unless explicitly allowed
- failed verification triggers transaction rollback

Use `--allow-dirty-files` only when you intentionally want RepoForge to modify files that already have local Git changes.

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

The provider layer is intentionally replaceable so future deployments can use compatible hosted APIs, local models, or organization-specific inference gateways without rewriting the core engineering pipeline.

## Sandbox and execution boundary\n\nRepoForge's workspace sandbox creates a temporary copy of the target repository for isolated operations while excluding Git metadata, virtual environments, dependency caches, and other runtime/generated material. This protects the original working tree from ordinary sandboxed operations, but it is not equivalent to OS-level isolation.\n\nAn optional Docker sandbox provides a stronger process/container boundary and can be configured with resource limits and restricted networking.\n\n```text\nWorkspace sandbox → protects the original working tree\nDocker sandbox    → stronger process/filesystem/network boundary\nHost execution    → controlled execution, not a security sandbox\n```\n\n## Safety model

- subprocess execution uses `shell=False`
- destructive commands are blocked by default
- network/package mutation is not silently performed by the verifier
- repository contents are treated as untrusted input
- patch paths cannot escape the target repository
- patches use exact preconditions
- failed repairs roll back when possible
- secrets are scanned separately
- deterministic verification is the release authority

## Verification and release states

RepoForge deliberately uses explicit states instead of pretending every repository is perfect.

| State | Meaning |
|---|---|
| `VERIFIED` | Required deterministic checks passed and sufficient evidence exists |
| `NOT VERIFIED` | One or more checks failed or evidence is insufficient |
| `BLOCKED` | The required verification could not safely be performed |

A green report therefore means **verified against the checks that actually ran**, not a universal mathematical guarantee of zero defects.

## Verification

GitHub Actions validates Python 3.10, 3.11, and 3.12 with linting, type checking, tests, compilation, and package building. The repository also contains a sample project and regression tests for discovery, diagnostics, repair, rollback, memory, readiness, secrets, and end-to-end execution.

## Architecture at a glance

```text
CLI
 │
 ▼
CONTROL PLANE
 ├── Goal + Task Graph
 ├── Agent Role Boundaries
 ├── Hooks + Permissions
 ├── Model Router
 └── Integrations / Protocol / Browser Adapters
 │
 ▼
ENGINEERING CORE
 ├── Discovery / Fingerprinting
 ├── Diagnostics / Repair Planning
 ├── Transactional Repair
 ├── Deterministic Verification
 ├── Security / Secret Scan
 ├── Deployment Readiness
 └── Evidence / Memory / Reports
 │
 ├── Deterministic tools
 └── Optional model assistance
```

The core is intentionally modular: detection, execution, repair, verification, provider integration, and reporting can evolve independently.

## Audit reality and verification boundary

A source inspection can identify configuration and code-structure signals, but it cannot substitute for executing the verification suite against the current commit. The repository's CI is the authoritative check for this project's own test/lint/type/build pipeline.

RepoForge itself also deliberately distinguishes `VERIFIED` from universal correctness: passing discovered checks is evidence about the checks that ran, not proof that arbitrary software has zero defects.

## Real-world validation\n\nRepoForge's own regression suite is necessary but not sufficient to establish repository-agnostic behavior. External-target validation should exercise the complete engineering loop against repositories that were not authored specifically for RepoForge.\n\n```text\nexternal repository → baseline verification → RCA → bounded repair\n                                      ↓\n                         deterministic re-verification\n                                      ↓\n                              independent review\n                                      ↓\n                       rollback or repair evidence\n```\n\nAdaptiveRag-X is being used as an external validation target. Its results should be reported separately from RepoForge's own test-suite results; a successful experiment does not establish universal correctness.\n\n## Limitations

No tool can truthfully guarantee that arbitrary software is permanently bug-free. RepoForge therefore reports evidence-backed states rather than inventing certainty. Browser-specific behavior, proprietary infrastructure, credentials, production deployment, and unsupported language ecosystems require an appropriate adapter and environment.

RepoForge is also not a sandbox by itself. For untrusted repositories, autonomous execution should be placed inside an isolated worker/container with least-privilege credentials and appropriate network restrictions.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy repoforge
pytest
python -m build
```

## Contributing philosophy

Good contributions make RepoForge **more observable, safer, more deterministic, or more broadly compatible**.

When adding a repair capability:

1. add the smallest useful implementation;
2. add a regression test;
3. define the evidence required to trust the result;
4. preserve fail-closed behavior;
5. run the full verification suite.

Do not weaken a gate merely to make CI green.

## Commercialization

The core can remain open source while paid layers provide managed repository scans, private runners, organization policies, deployment integrations, audit history, compliance evidence, and team-level governance.

## License

RepoForge-Omega is released under the **Apache License 2.0**. See [`LICENSE`](LICENSE).

Apache-2.0 was selected because it permits commercial and private use, modification, redistribution, and integration while providing an explicit patent license and preserving the project's attribution and license requirements.

---

**RepoForge-Omega principle:** inspect first, change carefully, verify with evidence, and never confuse AI confidence with software correctness.


## Autonomous engineering control plane

RepoForge now includes a unified control-plane layer around the existing deterministic engineering core. The objective is explicit:

> **make any given repository deployment-ready**

The control plane coordinates specialized roles, bounded task graphs, durable goal state, lifecycle hooks, permission policy, model routing, protocol endpoints, optional browser capabilities, and the existing repair/verification machinery.

```text
GOAL
  │
  ▼
REPOSITORY MAP
  │
  ▼
TASK GRAPH
  │
  ├── discovery
  ├── diagnosis
  ├── planning
  ├── repair
  ├── verification
  ├── review
  ├── security
  └── release readiness
          │
          ▼
   DETERMINISTIC GATES
          │
     ┌────┴────┐
     ▼         ▼
 VERIFIED   FAILED/BLOCKED
               │
               ▼
          evidence + rollback
               │
               └──► next bounded iteration
```

### Control-plane components

| Component | Responsibility |
|---|---|
| `agents.py` | Specialized engineering roles and execution boundaries |
| `tasks.py` | Dependency-aware task graph and task state |
| `goals.py` | Bounded autonomous goal lifecycle |
| `hooks.py` | Lifecycle events for observability and extensions |
| `permissions.py` | Explicit write, network, install and browser policy |
| `router.py` | Vendor-neutral model/provider selection |
| `integrations.py` | Extension registry for external capabilities |
| `protocols.py` | Protocol endpoint registry for future adapters |
| `browser.py` | Permission-gated browser automation interface |
| `orchestrator.py` | Unified control-plane coordination |

These are independently implemented RepoForge capabilities. The architecture is intentionally vendor-neutral and does not require any particular external agent, provider, editor, protocol server, or model runtime.

### Deployment-readiness goal

Run the autonomous goal in dry-run mode first:

```bash
repoforge goal /path/to/repository
```

When repository writes are explicitly authorized:

```bash
repoforge goal /path/to/repository --apply
```

The goal is bounded by `--max-iterations` and cannot promote a repository to `VERIFIED` from model confidence alone. The existing deterministic verification authority remains the final gate.

### Trust boundary

```text
AI / agents / models
        │
        │ propose, reason, coordinate
        ▼
RepoForge control plane
        │
        │ bounded changes
        ▼
Deterministic verification
        │
        ├── PASS ──► release evidence
        └── FAIL ──► rollback / blocked state
```

Autonomy expands what RepoForge can do; it does **not** weaken the evidence standard for `VERIFIED`.
