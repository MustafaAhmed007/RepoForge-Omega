from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
from .config import ForgeConfig
from .engine import RepoForge
from .evidence import EvidenceBundle
from .rca import RootCauseAnalysis,RootCauseAnalysisEngine
from .reviewer import IndependentReviewer
from .transaction import RepairTransaction
@dataclass(slots=True)
class RepairAttempt:
    number:int;patches:list[str];status:str;rca_confidence:float;review_approved:bool;reason:str=""
@dataclass(slots=True)
class RepairLoopResult:
    verified:bool;attempts:list[RepairAttempt]=field(default_factory=list);rca:RootCauseAnalysis|None=None
class RepairLoop:
    def __init__(self,config:ForgeConfig):self.config=config
    def run(self,patch_provider):
        attempts=[];forge=RepoForge(self.config.repo)
        for number in range(1,self.config.max_repair_attempts+1):
            v=forge.verify(self.config.timeout_seconds)
            if v.release_status.value=="VERIFIED":return RepairLoopResult(True,attempts)
            evidence=EvidenceBundle(v.execution_id);rca=RootCauseAnalysisEngine(self.config.repo).analyze(v,evidence);patches=patch_provider(rca,v,evidence)
            if not patches:return RepairLoopResult(False,attempts+[RepairAttempt(number,[],"NO_PATCH",rca.confidence,False,"No bounded patch candidate.")],rca)
            if self.config.dry_run:return RepairLoopResult(False,attempts+[RepairAttempt(number,[p.path for p in patches],"DRY_RUN",rca.confidence,False)],rca)
            tx=RepairTransaction(self.config.repo,max_files=self.config.max_files_changed,max_patch_bytes=self.config.max_patch_bytes,allow_dirty_files=self.config.allow_dirty_files)
            try:
                changed=tx.apply(patches);after=forge.verify(self.config.timeout_seconds);review=IndependentReviewer(self.config.repo).review(evidence,changed)
                if after.release_status.value=="VERIFIED" and review.approved:tx.commit();attempts.append(RepairAttempt(number,changed,"VERIFIED",rca.confidence,True));return RepairLoopResult(True,attempts,rca)
                tx.rollback();attempts.append(RepairAttempt(number,changed,"ROLLED_BACK",rca.confidence,review.approved,"Verification or independent review failed."))
            except Exception as e:tx.rollback();attempts.append(RepairAttempt(number,[],"ERROR",rca.confidence,False,str(e)))
        return RepairLoopResult(False,attempts,rca if 'rca' in locals() else None)