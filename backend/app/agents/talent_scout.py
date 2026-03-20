from typing import List, Dict
from datetime import datetime, timedelta

from pydantic import BaseModel

from app.models import CandidateProfile, PlatformSignal


class TalentSignals(BaseModel):
    candidate: CandidateProfile
    activity_summary: str
    repositories: List[str]
    problem_solving_summary: str
    language_profile: Dict[str, int] = {}
    total_repos: int = 0
    total_stars: int = 0


class TalentScoutAgent:

    def gather_signals(self, candidate: CandidateProfile) -> TalentSignals:
        repos: List[str] = []
        problem_solving_bits: List[str] = []
        activity_descriptions: List[str] = []
        language_profile: Dict[str, int] = {}

        total_repos = 0
        total_stars = 0

        for p in candidate.platforms:
            if p.platform.lower() == "github":
                repos.append(p.metadata.get("top_repo", "demo-project"))

                # If GitHub metadata includes languages and repo counts (as the Streamlit
                # app sends), incorporate them so downstream scoring can differ by stack.
                # Prefer a JSON mapping of languages -> repo counts if available.
                languages_csv = p.metadata.get("languages") or ""
                languages_json = p.metadata.get("languages_json") or ""

                if languages_json:
                    try:
                        import json

                        data = json.loads(languages_json)
                        if isinstance(data, dict):
                            for lang, count in data.items():
                                try:
                                    c = int(count)
                                except (TypeError, ValueError):
                                    c = 1
                                language_profile[lang] = language_profile.get(lang, 0) + max(c, 1)
                    except Exception:  # noqa: BLE001
                        # Fall back to CSV parsing below
                        pass

                if not language_profile and languages_csv:
                    for raw in languages_csv.split(","):
                        lang = raw.strip()
                        if not lang:
                            continue
                        language_profile[lang] = language_profile.get(lang, 0) + 1

                repo_count_raw = p.metadata.get("repo_count") or "0"
                stars_raw = p.metadata.get("total_stars") or "0"
                try:
                    rc = int(repo_count_raw)
                except (TypeError, ValueError):
                    rc = 0
                try:
                    ts = int(stars_raw)
                except (TypeError, ValueError):
                    ts = 0

                total_repos += max(rc, 0)
                total_stars += max(ts, 0)
                activity_descriptions.append(
                    "GitHub activity with "
                    f"{repo_count_raw} public repos, {stars_raw} total stars, "
                    f"languages: {languages_csv or 'unknown'}."
                )
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
            language_profile=language_profile,
            total_repos=total_repos,
            total_stars=total_stars,
        )
