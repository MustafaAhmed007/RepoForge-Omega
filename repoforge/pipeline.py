from __future__ import annotations
from pathlib import Path
from .config import ForgeConfig
from .diagnostics import DiagnosticEngine,DiagnosticFinding
from .memory import MemoryStore
from .models import RepositoryFingerprint
from .repair import RepairPlanner,RepairProposal
from .report import write_json,write_markdown

class Pipeline:
    def __init__(self,config:ForgeConfig)->None: self.config=config
    def inspect(self,output_dir:Path|None=None)->tuple[RepositoryFingerprint,list[DiagnosticFinding],list[RepairProposal]]:
        fp,findings=DiagnosticEngine(self.config.repo).run(); proposals=RepairPlanner(self.config.repo).propose(findings)
        destination=output_dir or (self.config.repo/'.repoforge')
        destination.mkdir(parents=True,exist_ok=True)
        write_json(destination/'report.json',fp,findings,proposals); write_markdown(destination/'report.md',fp,findings,proposals)
        MemoryStore(destination/'events.jsonl').append('inspection','complete',f'{len(findings)} findings',f'{fp.file_count} files inspected')
        return fp,findings,proposals
