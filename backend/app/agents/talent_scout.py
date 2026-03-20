from typing import List
from datetime import datetime, timedelta

from pydantic import BaseModel

from app.models import CandidateProfile, PlatformSignal


class TalentSignals(BaseModel):
    candidate: CandidateProfile
    activity_summary: str
    repositories: List[str]
    problem_solving_summary: str


class TalentScoutAgent:
    """Agent that gathers signals from 6+ platforms.

    For this demo we don't call real APIs; instead we simulate
    based on platform metadata so the system is fully runnable.
    """

    def gather_signals(self, candidate: CandidateProfile) -> TalentSignals:
        repos: List[str] = []
        problem_solving_bits: List[str] = []
        activity_descriptions: List[str] = []

        for p in candidate.platforms:
            if p.platform.lower() == "github":
                repos.append(p.metadata.get("top_repo", "demo-project"))
                activity_descriptions.append("Active on GitHub with consistent commits.")
            if p.platform.lower() in {"leetcode", "codeforces"}:
                rating = p.metadata.get("rating", "intermediate")
                problem_solving_bits.append(f"Competitive programming level: {rating}.")
            if p.platform.lower() == "linkedin":
                activity_descriptions.append("Professional profile with endorsements.")
            if p.platform.lower() in {"kaggle", "portfolio"}:
                activity_descriptions.append("Has public projects showcasing practical skills.")

        if not activity_descriptions:
            activity_descriptions.append("Limited public signal; relying on resume summary.")

        # Very rough heuristic for recency
        days_active = len(activity_descriptions) * 30
        recent_window = datetime.utcnow() - timedelta(days=days_active)

        activity_summary = (
            f"Public activity observed over ~{days_active} days since {recent_window.date()}. "
            + " ".join(activity_descriptions)
        )

        problem_summary = " ".join(problem_solving_bits) or "No competitive programming data available."

        return TalentSignals(
            candidate=candidate,
            activity_summary=activity_summary,
            repositories=repos,
            problem_solving_summary=problem_summary,
        )
