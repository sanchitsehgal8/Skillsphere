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
    time_to_productivity_days: float | None = None
    direct_matches: List[str] = []
    adjacent_support: List[str] = []


class RunMatchingResponse(BaseModel):
    job_id: str
    ranked: List[RankedCandidate]


class AuditEntryResponse(BaseModel):
    candidate_id: str
    bias_flags: List[str]


class AuditLogResponse(BaseModel):
    job_id: str
    entries: List[AuditEntryResponse]


class CodeforcesStatsOverview(BaseModel):
    current_rating: int
    max_rating: int
    rank_title: str
    total_problems_solved: int
    submission_count: int
    acceptance_rate: float
    contest_participation_count: int
    average_rank_percentile: float
    average_rank_percentile_note: str


class CodeforcesProblemSolvingProfile(BaseModel):
    difficulty_distribution: dict
    most_practiced_tags: List[str]
    comfort_zone: str
    struggle_zone: str
    tag_gaps: List[str]


class CodeforcesContestPerformance(BaseModel):
    rating_trajectory: str
    best_contest_delta: int
    worst_contest_delta: int
    consistency_score: float
    stability: str


class CodeforcesHonestSkillVerdict(BaseModel):
    genuinely_good_at: List[str]
    holding_back: List[str]
    rating_vs_habits: str
    improvement_signal: str
    mentor_summary: str


class CodeforcesAnalysisResponse(BaseModel):
    handle: str
    stats_overview: CodeforcesStatsOverview
    problem_solving_profile: CodeforcesProblemSolvingProfile
    contest_performance: CodeforcesContestPerformance
    honest_skill_verdict: CodeforcesHonestSkillVerdict
