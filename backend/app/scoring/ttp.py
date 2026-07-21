"""Evidence-based, reproducible time-to-productivity (TTP) estimation.

TTP answers: "how many focused hours before this candidate can independently
ship role-level work?" Every requirement contributes a bounded hour range
based on its coverage status (direct / adjacent / missing), scaled by the
candidate's own evidenced skill strength and learning-velocity dimension —
never a flat per-status constant applied blindly. Assumptions (sprint length,
adjacency decay) are explicit constants documented here, not hidden magic
numbers scattered through the code.

Given identical inputs this always returns identical output (deterministic —
no randomness, no model calls), so results are reproducible run-to-run.
"""

from __future__ import annotations

from typing import List, TypedDict

from app.models import Evidence, EvidenceSource, TimeToProductivity

# Explicit assumptions (documented, not buried):
SPRINT_HOURS = 60.0  # 2-week sprint at ~6 focused hours/day, 5 days/week
DIRECT_STRONG_HOURS = (2.0, 6.0)      # skill score >= 75
DIRECT_MODERATE_HOURS = (8.0, 18.0)   # skill score 40-75
ADJACENT_BASE_HOURS = {1: (14.0, 24.0), 2: (24.0, 40.0), 3: (36.0, 56.0)}
MISSING_HOURS = (40.0, 72.0)


class CoverageDetail(TypedDict):
    requirement: str
    status: str  # direct | adjacent | missing
    weight: float
    skill_score: float
    distance: int | None


def _range_for_requirement(cov: CoverageDetail, velocity01: float) -> tuple[float, float]:
    if cov["status"] == "direct":
        lo, hi = DIRECT_STRONG_HOURS if cov["skill_score"] >= 75 else DIRECT_MODERATE_HOURS
    elif cov["status"] == "adjacent":
        distance = cov.get("distance") or 3
        lo, hi = ADJACENT_BASE_HOURS.get(distance, ADJACENT_BASE_HOURS[3])
        # Stronger adjacent skill and higher learning velocity shrink the range.
        strength01 = max(0.0, min(1.0, cov["skill_score"] / 100.0))
        shrink = 1.0 - 0.25 * strength01 - 0.25 * velocity01
        lo, hi = lo * shrink, hi * shrink
    else:
        lo, hi = MISSING_HOURS
        shrink = 1.0 - 0.35 * velocity01
        lo, hi = lo * shrink, hi * shrink
    return lo, hi


def estimate_ttp(
    coverage: List[CoverageDetail],
    learning_velocity_score: float,
) -> TimeToProductivity:
    velocity01 = max(0.0, min(1.0, learning_velocity_score / 100.0))

    if not coverage:
        return TimeToProductivity(
            hours_low=0.0, hours_high=0.0, days_low=0.0, days_high=0.0, sprints=0.0,
            confidence=0.2, method="no-requirements",
            reasoning="The job has no parsed requirements, so no ramp-up estimate can be computed.",
        )

    weighted_lo = weighted_hi = weight_sum = 0.0
    evidence: List[Evidence] = []

    for cov in coverage:
        lo, hi = _range_for_requirement(cov, velocity01)
        w = max(cov["weight"], 0.1)
        weighted_lo += lo * w
        weighted_hi += hi * w
        weight_sum += w
        evidence.append(
            Evidence(
                source=EvidenceSource.derived,
                detail=f"{cov['requirement']}: {cov['status']} coverage → {lo:.0f}-{hi:.0f}h ramp.",
                metric=(lo + hi) / 2,
                unit="hours",
            )
        )

    hours_low = round(weighted_lo / weight_sum, 1) if weight_sum else 0.0
    hours_high = round(weighted_hi / weight_sum, 1) if weight_sum else 0.0
    days_low = round(hours_low / 6.0, 1)   # 6 focused hours/day assumption
    days_high = round(hours_high / 6.0, 1)
    sprints = round(((hours_low + hours_high) / 2.0) / SPRINT_HOURS, 2)

    direct_n = sum(1 for c in coverage if c["status"] == "direct")
    coverage_ratio = direct_n / len(coverage)
    confidence = round(max(0.2, min(0.95, 0.4 + 0.4 * coverage_ratio + 0.15 * velocity01)), 2)

    return TimeToProductivity(
        hours_low=hours_low, hours_high=hours_high,
        days_low=days_low, days_high=days_high, sprints=sprints,
        confidence=confidence, method="requirement-coverage-weighted",
        reasoning=(
            f"Weighted across {len(coverage)} requirement(s) by their declared importance: "
            f"{direct_n} direct match(es), scaled by evidenced skill strength and a "
            f"learning-velocity score of {learning_velocity_score:.0f}/100. "
            f"Assumes {SPRINT_HOURS:.0f} focused hours per sprint and 6 focused hours/day."
        ),
        evidence=evidence,
    )
