from __future__ import annotations
from pathlib import Path
from .config import ForgeConfig
from .diagnostics import DiagnosticEngine
from .repair import RepairPlanner
from .report import write_json, write_markdown

class Pipeline:
    def __init__(self, config:ForgeConfig):
        self.config=config

    def inspect(self, output_dir:Path|None=None):
        fp, findings=DiagnosticEngine(self.config.repo).run()
        proposals=RepairPlanner(self.config.repo).propose(findings)
        if output_dir:
            output_dir.mkdir(parents=True,exist_ok=True)
            write_json(output_dir/'report.json',fp,findings,proposals)
            write_markdown(output_dir/'report.md',fp,findings,proposals)
        return fp, findings, proposals
