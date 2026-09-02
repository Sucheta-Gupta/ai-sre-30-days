from pydantic import BaseModel, Field
from typing import Literal

class DockerfileRequest(BaseModel):
    dockerfile: str = Field(min_length=1)

class Finding(BaseModel):
    severity: Literal["high", "medium", "low"]
    category: str
    issue: str
    recommendation: str

class DockerfileAnalysis(BaseModel):
    summary: str
    score: int = Field(ge=0, le=100)
    findings: list[Finding]
    optimized_dockerfile: str