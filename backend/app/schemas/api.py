from typing import List, Optional

from pydantic import BaseModel

from app.models import PlatformSignal, ExperienceLevel


class CreateJobRequest(BaseModel):
    job_id: str
    title: str
    description: str


class CreateCandidateRequest(BaseModel):
    candidate_id: str
    name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    platforms: List[PlatformSignal] = []
    demographics: dict = {}


class RunMatchingRequest(BaseModel):
    job_id: str
    candidate_ids: List[str]


class CopilotQueryRequest(BaseModel):
    job_id: str
    candidate_id: Optional[str] = None


class CopilotResponse(BaseModel):
    answer: str


class RankedCandidate(BaseModel):
    candidate_id: str
    score: float
    explanation: str


class RunMatchingResponse(BaseModel):
    job_id: str
    ranked: List[RankedCandidate]


class AuditEntryResponse(BaseModel):
    candidate_id: str
    bias_flags: List[str]


class AuditLogResponse(BaseModel):
    job_id: str
    entries: List[AuditEntryResponse]
