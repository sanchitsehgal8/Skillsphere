"""SkillSphere domain model — evidence-first.

Everything the platform asserts about a candidate is traceable to an
``Evidence`` object: a typed, sourced, optionally-quantified observation. Scores,
skills, culture signals and time-to-productivity all carry the evidence that
produced them, so every number is explainable and nothing is asserted without
support.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Evidence primitives
# --------------------------------------------------------------------------- #
class EvidenceSource(str, Enum):
    github = "github"
    resume = "resume"
    codeforces = "codeforces"
    derived = "derived"


class Evidence(BaseModel):
    source: EvidenceSource
    detail: str
    metric: Optional[float] = None
    unit: Optional[str] = None
    url: Optional[str] = None


# --------------------------------------------------------------------------- #
# GitHub evidence
# --------------------------------------------------------------------------- #
class RepoInsight(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    primary_language: Optional[str] = None
    languages_bytes: Dict[str, int] = {}
    stars: int = 0
    forks: int = 0
    is_fork: bool = False
    topics: List[str] = []
    size_kb: int = 0
    pushed_at: Optional[str] = None
    created_at: Optional[str] = None
    open_issues: int = 0
    has_ci: bool = False
    has_tests: bool = False
    has_docs: bool = False
    complexity: float = 0.0  # 0..1 relative structural complexity


class GithubEvidence(BaseModel):
    username: str
    profile_url: str
    name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    hireable: Optional[bool] = None

    public_repos: int = 0
    followers: int = 0
    following: int = 0
    account_created_at: Optional[str] = None
    account_age_years: float = 0.0

    total_stars: int = 0
    total_forks: int = 0
    original_repo_count: int = 0
    forked_repo_count: int = 0

    languages_bytes: Dict[str, int] = {}
    languages_repo_count: Dict[str, int] = {}
    frameworks: List[str] = []
    topics: List[str] = []

    most_recent_push_days: Optional[int] = None
    active_repos_last_year: int = 0
    documented_repo_ratio: float = 0.0
    tested_repo_ratio: float = 0.0
    ci_repo_ratio: float = 0.0
    structural_analysis_available: bool = False  # True only if CI/test/docs were actually inspected (requires GITHUB_TOKEN)

    contributed_orgs: List[str] = []
    oss_signal: float = 0.0  # 0..1

    repos: List[RepoInsight] = []
    fetched_ok: bool = False
    note: str = ""


# --------------------------------------------------------------------------- #
# Resume evidence
# --------------------------------------------------------------------------- #
class ResumeContact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    other_links: List[str] = []


class EducationItem(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[str] = None


class ExperienceItem(BaseModel):
    company: str
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    is_current: bool = False
    duration_months: Optional[int] = None
    description: Optional[str] = None


class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    tech: List[str] = []
    url: Optional[str] = None


class ResumeEvidence(BaseModel):
    contact: ResumeContact = ResumeContact()
    summary: Optional[str] = None
    education: List[EducationItem] = []
    experience: List[ExperienceItem] = []
    skills: List[str] = []
    projects: List[ProjectItem] = []
    certifications: List[str] = []
    achievements: List[str] = []
    hackathons: List[str] = []
    internships: List[ExperienceItem] = []
    total_experience_years: Optional[float] = None
    parsed_by: str = "rules"  # rules | llm | hybrid
    raw_text: str = ""


# --------------------------------------------------------------------------- #
# Candidate + Job
# --------------------------------------------------------------------------- #
class CandidateEvidence(BaseModel):
    candidate_id: str
    name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    github: Optional[GithubEvidence] = None
    resume: Optional[ResumeEvidence] = None
    codeforces: Optional[Dict] = None
    demographics: Dict[str, str] = {}
    fetched_at: datetime = Field(default_factory=_utcnow)


class JobRequirement(BaseModel):
    name: str
    category: str = "skill"  # skill | domain | soft-skill | tool
    weight: float = Field(default=0.7, ge=0, le=1)
    required: bool = True
    source: str = "parsed"


class JobSpec(BaseModel):
    id: str
    title: str
    description: str
    requirements: List[JobRequirement] = []
    seniority: Optional[str] = None
    domains: List[str] = []
    created_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Skill verification
# --------------------------------------------------------------------------- #
class VerifiedSkill(BaseModel):
    name: str
    category: str = "language"
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    repo_count: int = 0
    loc_bytes: int = 0
    commit_recency_days: Optional[int] = None
    frameworks: List[str] = []
    years_used: Optional[float] = None
    projects: List[str] = []
    oss_contributions: int = 0
    complexity: float = 0.0
    evidence: List[Evidence] = []
    reasoning: str = ""
    suggestions: List[str] = []


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
class DimensionScore(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: List[Evidence] = []
    reasoning: str = ""
    suggestions: List[str] = []


class CultureSignal(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: List[Evidence] = []
    reasoning: str = ""


class TimeToProductivity(BaseModel):
    hours_low: float
    hours_high: float
    days_low: float
    days_high: float
    sprints: float
    confidence: float = Field(ge=0, le=1)
    method: str = ""
    reasoning: str = ""
    evidence: List[Evidence] = []


class EngineeringScorecard(BaseModel):
    candidate_id: str
    overall_score: float = Field(ge=0, le=100)
    overall_confidence: float = Field(ge=0, le=1)
    dimensions: List[DimensionScore] = []
    skills: List[VerifiedSkill] = []
    culture: List[CultureSignal] = []
    time_to_productivity: Optional[TimeToProductivity] = None
    evidence_completeness: float = Field(default=0.0, ge=0, le=1)
    summary: str = ""
    strengths: List[str] = []
    gaps: List[str] = []
    recommendations: List[str] = []


# --------------------------------------------------------------------------- #
# Job ↔ candidate match
# --------------------------------------------------------------------------- #
class RequirementCoverage(BaseModel):
    requirement: str
    status: str  # direct | adjacent | missing
    evidence_skill: Optional[str] = None
    detail: str = ""
    weight: float = 0.0
    distance: Optional[int] = None


class MatchResult(BaseModel):
    job_id: str
    candidate_id: str
    fit_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    verdict: str = "developing"  # strong | promising | developing
    coverage: List[RequirementCoverage] = []
    matched_requirements: List[str] = []
    adjacent_requirements: List[str] = []
    missing_requirements: List[str] = []
    scorecard: EngineeringScorecard
    reasoning: str = ""
    created_at: datetime = Field(default_factory=_utcnow)


class BiasFlag(BaseModel):
    candidate_id: str
    reason: str
    severity: str = "medium"  # low | medium | high


class FairnessReport(BaseModel):
    job_id: str
    flags: List[BiasFlag] = []
    group_disparity: Optional[float] = None
    note: str = ""
