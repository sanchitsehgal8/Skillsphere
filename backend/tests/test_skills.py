from app.models import CandidateEvidence, GithubEvidence, ResumeEvidence
from app.scoring.skills import verify_skills


def _github_with_languages(languages_bytes, frameworks=None, repos=None):
    return GithubEvidence(
        username="tester",
        profile_url="https://github.com/tester",
        public_repos=len(repos or []),
        account_age_years=2.0,
        languages_bytes=languages_bytes,
        languages_repo_count={k: 1 for k in languages_bytes},
        frameworks=frameworks or [],
        most_recent_push_days=10,
        repos=repos or [],
        fetched_ok=True,
    )


def test_verify_skills_requires_evidence():
    ev = CandidateEvidence(candidate_id="c1", name="Empty")
    assert verify_skills(ev) == []


def test_verify_skills_scores_language_from_bytes_and_recency():
    gh = _github_with_languages({"Python": 200_000})
    ev = CandidateEvidence(candidate_id="c1", name="Test", github=gh)
    skills = verify_skills(ev)
    python = next(s for s in skills if s.name == "python")
    assert 0 < python.score <= 100
    assert python.evidence  # every skill must carry evidence
    assert python.repo_count == 1


def test_ai_ml_framework_is_categorized_as_ai_ml_not_generic_framework():
    # Regression test: frameworks like PyTorch were previously miscategorized
    # as a catch-all "framework" bucket, so the AI/ML dimension read 0 despite
    # having real evidence.
    gh = _github_with_languages({"Python": 100_000}, frameworks=["PyTorch", "FastAPI"])
    ev = CandidateEvidence(candidate_id="c1", name="Test", github=gh)
    skills = verify_skills(ev)
    pytorch = next(s for s in skills if s.name == "PyTorch")
    fastapi = next(s for s in skills if s.name == "FastAPI")
    assert pytorch.category == "ai/ml"
    assert fastapi.category == "backend"


def test_resume_corroboration_boosts_existing_skill_and_adds_resume_only_skill():
    gh = _github_with_languages({"Python": 100_000})
    resume = ResumeEvidence(skills=["python", "leadership"], raw_text="")
    ev = CandidateEvidence(candidate_id="c1", name="Test", github=gh, resume=resume)
    skills = verify_skills(ev)

    python = next(s for s in skills if s.name == "python")
    assert any("resume" in e.detail.lower() or e.source == "resume" for e in python.evidence)

    leadership = next(s for s in skills if s.name == "leadership")
    assert leadership.confidence < 0.5  # resume-only claim, unverified by code
    assert leadership.suggestions  # should nudge toward corroboration
