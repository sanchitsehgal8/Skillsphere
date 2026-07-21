"""Thin request/response wrappers for endpoints that don't map 1:1 onto a
domain object already defined in ``app.models``. Where a domain object *is*
the correct wire format (JobSpec, CandidateEvidence, EngineeringScorecard,
MatchResult, FairnessReport, ResumeEvidence), endpoints use it directly instead
of duplicating an equivalent schema here.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel

from app.models import CandidateEvidence, EngineeringScorecard


class CreateJobRequest(BaseModel):
    job_id: str
    title: str
    description: str


class ExtractJobDescriptionResponse(BaseModel):
    extracted_text: str
    suggested_title: Optional[str] = None


class CreateCandidateRequest(BaseModel):
    candidate_id: str
    name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    github_username: Optional[str] = None
    codeforces_handle: Optional[str] = None
    resume_text: Optional[str] = None
    demographics: Dict[str, str] = {}


class CandidateWithScorecard(BaseModel):
    evidence: CandidateEvidence
    scorecard: EngineeringScorecard


class RunMatchingRequest(BaseModel):
    job_id: str
    candidate_ids: List[str]


class CopilotQueryRequest(BaseModel):
    query: str
    job_id: Optional[str] = None
    candidate_ids: Optional[List[str]] = None


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
