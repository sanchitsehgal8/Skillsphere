from app.scoring.ttp import MISSING_HOURS, estimate_ttp


def _cov(status, weight=0.9, skill_score=0.0, distance=None):
    return {"requirement": "python", "status": status, "weight": weight, "skill_score": skill_score, "distance": distance}


def test_no_requirements_returns_zeroed_result():
    result = estimate_ttp([], learning_velocity_score=50)
    assert result.hours_low == 0.0
    assert result.hours_high == 0.0
    assert result.method == "no-requirements"


def test_direct_strong_skill_is_faster_than_missing():
    strong = estimate_ttp([_cov("direct", skill_score=90)], learning_velocity_score=50)
    missing = estimate_ttp([_cov("missing")], learning_velocity_score=50)
    assert strong.hours_high < missing.hours_low


def test_higher_learning_velocity_never_increases_ramp_time():
    low_velocity = estimate_ttp([_cov("missing")], learning_velocity_score=0)
    high_velocity = estimate_ttp([_cov("missing")], learning_velocity_score=100)
    assert high_velocity.hours_high <= low_velocity.hours_high
    assert high_velocity.hours_low <= low_velocity.hours_low


def test_missing_requirement_never_exceeds_documented_ceiling():
    result = estimate_ttp([_cov("missing")], learning_velocity_score=0)
    assert result.hours_high <= MISSING_HOURS[1]


def test_sprints_and_days_are_consistent_with_hours():
    result = estimate_ttp([_cov("direct", skill_score=90)], learning_velocity_score=50)
    avg_hours = (result.hours_low + result.hours_high) / 2
    assert result.days_low == round(result.hours_low / 6.0, 1)
    assert abs(result.sprints - avg_hours / 60.0) < 0.01
