from pydantic import BaseModel, Field
from typing import Literal

class K8sManifestRequest(BaseModel):
    manifest: str = Field(min_length=1)

class Finding(BaseModel):
    severity: Literal['high','medium','low']
    category: Literal['Security','Configuration','Missing Probes','Network and Routing','Observability','Best Practice', 'Others','Reliability']
    issue: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)

class K8sManifestAnalysis(BaseModel):
    summary: str
    score: int = Field(ge=0, le=100)
    findings: list[Finding] = Field(max_length=10)

class ValidationFindings(BaseModel):
    issues: list[str] 