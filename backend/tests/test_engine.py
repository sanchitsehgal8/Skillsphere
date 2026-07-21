import asyncio

from app.models import CandidateEvidence, GithubEvidence
from app.scoring.engine import build_scorecard, match_candidate
from app.scoring.job import parse_job


def _candidate(languages_bytes, most_recent_push_days=5):
    gh = GithubEvidence(
        username="tester",
        profile_url="https://github.com/tester",
        public_repos=len(languages_bytes),
        original_repo_count=len(languages_bytes),
        account_age_years=2.0,
        languages_bytes=languages_bytes,
        languages_repo_count={k: 1 for k in languages_bytes},
        most_recent_push_days=most_recent_push_days,
        active_repos_last_year=len(languages_bytes),
        fetched_ok=True,
    )
    return CandidateEvidence(candidate_id="cand-1", name="Test Candidate", github=gh)


def test_build_scorecard_is_deterministic():
    ev = _candidate({"Python": 150_000, "TypeScript": 40_000})
    a = build_scorecard(ev)
    b = build_scorecard(ev)
    assert a.overall_score == b.overall_score
    assert [d.score for d in a.dimensions] == [d.score for d in b.dimensions]


def test_scorecard_every_skill_has_evidence():
    ev = _candidate({"Python": 150_000})
    sc = build_scorecard(ev)
    for skill in sc.skills:
        assert skill.evidence, f"skill {skill.name} has no evidence"


def test_overall_score_is_confidence_weighted_not_flat_average():
    ev = _candidate({"Python": 150_000})
    sc = build_scorecard(ev)
    flat_average = sum(d.score for d in sc.dimensions) / len(sc.dimensions)
    weighted = sum(d.score * d.confidence for d in sc.dimensions) / sum(d.confidence for d in sc.dimensions)
    assert abs(sc.overall_score - weighted) < 0.15
    # With many zero-evidence low-confidence dimensions, confidence weighting
    # should pull the score away from a naive flat average toward the
    # evidenced dimensions.
    assert sc.overall_score != flat_average


def test_match_candidate_direct_and_missing_requirements():
    ev = _candidate({"Python": 150_000})
    sc = build_scorecard(ev)
    job = asyncio.run(parse_job("job-1", "Backend Engineer", "We need Python and AWS experience."))
    result = match_candidate(job, ev, sc)

    assert result.job_id == "job-1"
    assert result.candidate_id == "cand-1"
    assert "python" in result.matched_requirements
    assert 0 <= result.fit_score <= 100
    assert result.scorecard.time_to_productivity is not None
    assert result.verdict in {"strong", "promising", "developing"}


def test_match_candidate_is_deterministic():
    ev = _candidate({"Python": 150_000, "JavaScript": 60_000})
    sc = build_scorecard(ev)
    job = asyncio.run(parse_job("job-2", "Full Stack Engineer", "Python and JavaScript required."))
    a = match_candidate(job, ev, sc)
    b = match_candidate(job, ev, sc)
    assert a.fit_score == b.fit_score
    assert a.scorecard.time_to_productivity.hours_low == b.scorecard.time_to_productivity.hours_low
