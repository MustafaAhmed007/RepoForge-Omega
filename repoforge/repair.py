from dataclasses import dataclass
from pathlib import Path
from .diagnostics import DiagnosticFinding

@dataclass(slots=True)
class RepairProposal:
    finding_code: str
    action: str
    rationale: str

class RepairPlanner:
    def __init__(self, repo: Path):
        self.repo = repo.resolve()

    def propose(self, findings: list[DiagnosticFinding]) -> list[RepairProposal]:
        proposals=[]
        for f in findings:
            if f.code == 'NO_TESTS':
                proposals.append(RepairProposal(f.code,'add_tests','Create deterministic regression tests.'))
            elif f.code == 'ENV_CONTRACT':
                proposals.append(RepairProposal(f.code,'create_env_template','Create a sanitized environment contract.'))
            elif f.code == 'UNLOCKED_NODE_DEPS':
                proposals.append(RepairProposal(f.code,'generate_lockfile','Generate a reproducible dependency lockfile after approval.'))
            elif f.code == 'NO_GITIGNORE':
                proposals.append(RepairProposal(f.code,'add_gitignore','Add ecosystem-specific ignore rules.'))
            else:
                proposals.append(RepairProposal(f.code,'manual_review','Collect more evidence before mutation.'))
        return proposals
