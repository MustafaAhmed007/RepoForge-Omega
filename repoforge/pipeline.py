from __future__ import annotations
from pathlib import Path
from .config import ForgeConfig
from .diagnostics import DiagnosticEngine,DiagnosticFinding
from .models import RepositoryFingerprint
from .repair import RepairPlanner,RepairProposal
from .report import write_json,write_markdown

class Pipeline:
    def __init__(self,config:ForgeConfig)->None: self.config=config
    def inspect(self,output_dir:Path|None=None)->tuple[RepositoryFingerprint,list[DiagnosticFinding],list[RepairProposal]]:
        fp,findings=DiagnosticEngine(self.config.repo).run(); proposals=RepairPlanner(self.config.repo).propose(findings)
        if output_dir:
            output_dir.mkdir(parents=True,exist_ok=True); write_json(output_dir/'report.json',fp,findings,proposals); write_markdown(output_dir/'report.md',fp,findings,proposals)
        return fp,findings,proposals
