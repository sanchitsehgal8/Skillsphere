from app.scoring.common import clamp01, log_norm, recency_score, to_100


def test_log_norm_bounds():
    assert log_norm(0, 100) == 0.0
    assert log_norm(-5, 100) == 0.0
    assert 0.0 < log_norm(50, 100) < 1.0
    assert log_norm(100, 100) == 1.0
    assert log_norm(100, 0) == 0.0  # zero ceiling is never a divide-by-zero


def test_log_norm_monotonic():
    assert log_norm(10, 1000) < log_norm(100, 1000) < log_norm(1000, 1000)


def test_recency_score_decays_with_age():
    assert recency_score(None) == 0.0
    assert recency_score(0) == 1.0
    fresh = recency_score(30)
    old = recency_score(720)
    assert fresh > old > 0.0


def test_clamp01_and_to_100():
    assert clamp01(-1) == 0.0
    assert clamp01(2) == 1.0
    assert clamp01(0.5) == 0.5
    assert to_100(0.5) == 50.0
    assert to_100(-1) == 0.0
    assert to_100(2) == 100.0
