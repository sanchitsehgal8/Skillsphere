import asyncio

from app.agents.recruiter_copilot import CandidateContext, answer_query
from app.models import DimensionScore, EngineeringScorecard, MatchResult


def _scorecard(candidate_id, overall, dims):
    return EngineeringScorecard(
        candidate_id=candidate_id,
        overall_score=overall,
        overall_confidence=0.6,
        dimensions=[DimensionScore(key=k, label=k.title(), score=v, confidence=0.7) for k, v in dims.items()],
        skills=[],
    )


def _context(candidate_id, name, overall, dims, fit_score=None):
    sc = _scorecard(candidate_id, overall, dims)
    match = None
    if fit_score is not None:
        match = MatchResult(job_id="job-1", candidate_id=candidate_id, fit_score=fit_score, confidence=0.6, scorecard=sc)
    return CandidateContext(candidate_id=candidate_id, name=name, scorecard=sc, match=match)


def test_answer_query_is_deterministic_without_llm():
    # conftest disables the LLM by default, so this must never call the network.
    contexts = [
        _context("alice", "Alice", 80, {"backend": 90}, fit_score=85),
        _context("bob", "Bob", 60, {"backend": 40}, fit_score=55),
    ]
    ans = asyncio.run(answer_query("Compare alice vs bob", contexts))
    assert ans.llm_assisted is False
    assert "Alice" in ans.answer
    assert "Bob" in ans.answer


def test_compare_attributes_dimension_lead_to_correct_candidate():
    contexts = [
        _context("alice", "Alice", 80, {"backend": 90}),
        _context("bob", "Bob", 60, {"backend": 20}),
    ]
    ans = asyncio.run(answer_query("Compare Alice vs Bob", contexts))
    # Alice has the higher backend score — the text must say Alice leads, not Bob.
    lines = [l for l in ans.answer.splitlines() if "Backend" in l]
    assert lines, "expected a Backend comparison line"
    assert "Alice" in lines[0] and "ahead" in lines[0]


def test_find_filters_by_threshold():
    contexts = [
        _context("alice", "Alice", 80, {"backend": 90}),
        _context("bob", "Bob", 60, {"backend": 20}),
    ]
    ans = asyncio.run(answer_query("Find strong backend engineers", contexts))
    assert "Alice" in ans.answer
    assert "Bob" not in ans.answer


def test_missing_skills_without_job_says_no_job_loaded():
    contexts = [_context("alice", "Alice", 80, {"backend": 90})]
    ans = asyncio.run(answer_query("What skills are missing for this JD?", contexts, job=None))
    assert "no job" in ans.answer.lower()


def test_shortlist_fallback_on_empty_pool():
    ans = asyncio.run(answer_query("Tell me about the pipeline", []))
    assert "no candidates" in ans.answer.lower()
