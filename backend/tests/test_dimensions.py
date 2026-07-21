from app.models import CandidateEvidence, GithubEvidence, RepoInsight
from app.scoring.dimensions import score_code_quality, score_open_source


def _repo(complexity, has_ci=False, has_tests=False):
    return RepoInsight(name="repo", url="https://github.com/x/repo", complexity=complexity, has_ci=has_ci, has_tests=has_tests)


def test_unmeasured_structural_data_does_not_fake_a_low_score():
    # Regression test: without GITHUB_TOKEN, has_ci/has_tests are never set,
    # so ci_repo_ratio/tested_repo_ratio are always 0.0. The old guard treated
    # that as "measured and legitimately bad," silently capping Code Quality
    # near 25/100 for every candidate with any repo complexity signal at all
    # (nearly everyone) regardless of actual code quality.
    gh = GithubEvidence(
        username="t", profile_url="https://github.com/t",
        repos=[_repo(0.9), _repo(0.85)],  # high complexity, but never measured for CI/tests
        structural_analysis_available=False,
    )
    ev = CandidateEvidence(candidate_id="c1", name="T", github=gh)
    dim = score_code_quality(ev)
    assert dim.score > 50.0  # must reflect the real complexity evidence, not a forced-zero CI/test term
    assert dim.confidence < 0.5  # appropriately less confident than a fully-measured result


def test_measured_structural_data_uses_full_formula_with_higher_confidence():
    gh = GithubEvidence(
        username="t", profile_url="https://github.com/t",
        repos=[_repo(0.9, has_ci=True, has_tests=True)],
        ci_repo_ratio=1.0, tested_repo_ratio=1.0,
        structural_analysis_available=True,
    )
    ev = CandidateEvidence(candidate_id="c1", name="T", github=gh)
    dim = score_code_quality(ev)
    assert dim.score > 80.0
    assert dim.confidence == 0.7


def test_low_open_source_signal_has_low_confidence_not_flat_confidence():
    # A candidate with zero stars/followers/forks must not be *confidently*
    # scored as having low open-source impact — absence of GitHub fame is
    # weak evidence, not proof, since most excellent engineers never
    # accumulate it regardless of skill.
    gh = GithubEvidence(username="t", profile_url="https://github.com/t", followers=0, total_stars=0, total_forks=0, oss_signal=0.0)
    ev = CandidateEvidence(candidate_id="c1", name="T", github=gh)
    dim = score_open_source(ev)
    assert dim.score == 0.0
    assert dim.confidence <= 0.25


def test_high_open_source_signal_has_higher_confidence():
    gh = GithubEvidence(username="t", profile_url="https://github.com/t", followers=500, total_stars=1000, total_forks=200, oss_signal=0.9)
    ev = CandidateEvidence(candidate_id="c1", name="T", github=gh)
    dim = score_open_source(ev)
    assert dim.confidence > 0.6
