from app.agents.bias_auditor import audit
from app.models import CandidateEvidence, EngineeringScorecard, MatchResult


def _scorecard(candidate_id, score=50.0):
    return EngineeringScorecard(candidate_id=candidate_id, overall_score=score, overall_confidence=0.5)


def _result(candidate_id, fit_score):
    return MatchResult(
        job_id="job-1", candidate_id=candidate_id, fit_score=fit_score, confidence=0.5,
        scorecard=_scorecard(candidate_id, fit_score),
    )


def test_no_demographics_produces_no_disparity():
    candidates = {
        "a": CandidateEvidence(candidate_id="a", name="A"),
        "b": CandidateEvidence(candidate_id="b", name="B"),
    }
    results = [_result("a", 80.0), _result("b", 70.0)]
    report = audit("job-1", results, candidates)
    assert report.group_disparity is None
    assert report.flags == []


def test_group_disparity_flags_when_gap_exceeds_threshold():
    candidates = {
        "a": CandidateEvidence(candidate_id="a", name="A", demographics={"gender": "male"}),
        "b": CandidateEvidence(candidate_id="b", name="B", demographics={"gender": "female"}),
    }
    # Non-protected (a) scores far above protected (b) -> disparity should trip the flag.
    results = [_result("a", 90.0), _result("b", 50.0)]
    report = audit("job-1", results, candidates)
    assert report.group_disparity == 40.0
    assert any(f.candidate_id == "b" for f in report.flags)
    assert any(f.severity == "high" for f in report.flags)


def test_small_disparity_does_not_flag():
    candidates = {
        "a": CandidateEvidence(candidate_id="a", name="A", demographics={"gender": "male"}),
        "b": CandidateEvidence(candidate_id="b", name="B", demographics={"gender": "female"}),
    }
    results = [_result("a", 71.0), _result("b", 70.0)]
    report = audit("job-1", results, candidates)
    assert report.group_disparity == 1.0
    assert report.flags == []
