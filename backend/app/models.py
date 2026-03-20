from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class ExperienceLevel(str, Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"


class JobRequirement(BaseModel):
    name: str
    weight: float = Field(ge=0, le=1)
    category: str = "skill"  # e.g. skill, domain, soft-skill


class JobDescription(BaseModel):
    id: str
    title: str
    description: str
    requirements: List[JobRequirement] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlatformSignal(BaseModel):
    platform: str  # e.g. github, leetcode, linkedin, kaggle, portfolio
    url: Optional[str] = None
    metadata: Dict[str, str] = {}


class CandidateProfile(BaseModel):
    id: str
    name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    platforms: List[PlatformSignal] = []
    demographics: Dict[str, str] = {}  # e.g. {"gender": "female", "ethnicity": "..."}


class SkillNode(BaseModel):
    name: str
    score: float  # 0-1 inferred proficiency
    evidence: List[str] = []


class SkillGraph(BaseModel):
    candidate_id: str
    skills: List[SkillNode]
    learning_velocity: float  # 0-1, how fast the person seems to grow


class MatchScore(BaseModel):
    job_id: str
    candidate_id: str
    score: float
    explanation: str
    time_to_productivity_days: float | None = None
    direct_matches: List[str] = []
    adjacent_support: List[str] = []


class BiasFlag(BaseModel):
    candidate_id: str
    reason: str
    severity: str  # e.g. low, medium, high


class AuditLogEntry(BaseModel):
    job_id: str
    candidate_id: str
    original_rank: int
    adjusted_rank: int
    bias_flags: List[BiasFlag] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
