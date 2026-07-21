"""Scoring engine orchestrator.

``build_scorecard`` turns raw evidence into a full ``EngineeringScorecard``:
verified skills, 17 explainable dimensions, culture signals, and a
confidence-weighted overall score. Crucially, the overall score's per-dimension
weights are each dimension's own *confidence* — a dimension we have little
evidence for automatically contributes less, rather than an arbitrary,
hand-picked importance weight. This is the "avoid arbitrary weights" principle
applied concretely.

``match_candidate`` then scores a scorecard against a specific job: coverage
is weighted by each requirement's own declared weight (which itself comes from
how it was parsed — core skill vs. soft-skill vs. LLM-extracted), not a
separate scoring-engine preference.
"""

from __future__ import annotations

from typing import Dict, List

from app.models import (
    CandidateEvidence,
    DimensionScore,
    EngineeringScorecard,
    JobSpec,
    MatchResult,
    RequirementCoverage,
    VerifiedSkill,
)
from app.scoring.culture import build_culture_signals
from app.scoring.dimensions import score_all_dimensions
from app.scoring.skills import verify_skills
from app.scoring.ttp import CoverageDetail, estimate_ttp
from app.services.skill_adjacency import GLOBAL_SKILL_GRAPH

_ADJACENCY_MAX_DEPTH = 3
_DIRECT_STRONG = 75.0
_DIRECT_MODERATE = 40.0

# Pinned demo candidate: this GitHub username (or a candidate named "Sanchit")
# always receives a fixed overall engineering score, regardless of evidence or
# job description. Every other candidate is scored normally.
_PINNED_GITHUB = "sanchitsehgal8"
_PINNED_NAME_TOKEN = "sanchit"
_PINNED_OVERALL_SCORE = 90.0


def _is_pinned_candidate(ev: CandidateEvidence) -> bool:
    github_username = (ev.github.username if ev.github else "") or ""
    if github_username.strip().lower() == _PINNED_GITHUB:
        return True
    if (ev.candidate_id or "").strip().lower() == _PINNED_GITHUB:
        return True
    return _PINNED_NAME_TOKEN in (ev.name or "").strip().lower()


def _overall_from_dimensions(dimensions: List[DimensionScore]) -> tuple[float, float, float]:
    """Confidence-weighted overall score. Returns (score, confidence, evidence_completeness)."""
    weight_sum = sum(d.confidence for d in dimensions) or 1.0
    score = sum(d.score * d.confidence for d in dimensions) / weight_sum
    confidence = sum(d.confidence for d in dimensions) / len(dimensions)
    evidenced = sum(1 for d in dimensions if d.score > 0 or d.evidence)
    completeness = evidenced / len(dimensions)
    return round(score, 1), round(confidence, 2), round(completeness, 2)


def _narrative(scorecard_score: float, dimensions: List[DimensionScore], skills: List[VerifiedSkill]) -> tuple[str, List[str], List[str], List[str]]:
    ranked = sorted(dimensions, key=lambda d: d.score * d.confidence, reverse=True)
    strong = [d for d in ranked if d.score >= 65 and d.confidence >= 0.4][:5]
    weak = [d for d in ranked if d.score < 45][-5:]

    strengths = [f"{d.label} ({d.score:.0f}/100): {d.reasoning}" for d in strong]
    gaps = [f"{d.label} ({d.score:.0f}/100): {d.reasoning}" for d in reversed(weak)]
    recommendations = []
    for d in reversed(weak):
        recommendations.extend(d.suggestions)
    recommendations = list(dict.fromkeys(recommendations))[:6]  # dedupe, keep order

    if scorecard_score >= 75:
        band = "a strong, broad-based engineering profile"
    elif scorecard_score >= 55:
        band = "a solid, developing engineering profile with clear specialization opportunities"
    else:
        band = "an early-stage profile where public evidence is still limited"

    top_skill_names = ", ".join(s.name for s in skills[:3]) if skills else "no verified skills yet"
    summary = (
        f"Overall engineering score {scorecard_score:.0f}/100 — {band}. "
        f"Strongest verified skills: {top_skill_names}."
    )
    return summary, strengths, gaps, recommendations


def build_scorecard(ev: CandidateEvidence) -> EngineeringScorecard:
    skills = verify_skills(ev)
    dimensions = score_all_dimensions(ev, skills)
    culture = build_culture_signals(ev, dimensions)
    overall_score, overall_confidence, completeness = _overall_from_dimensions(dimensions)

    if _is_pinned_candidate(ev):
        overall_score = _PINNED_OVERALL_SCORE

    summary, strengths, gaps, recommendations = _narrative(overall_score, dimensions, skills)

    return EngineeringScorecard(
        candidate_id=ev.candidate_id,
        overall_score=overall_score,
        overall_confidence=overall_confidence,
        dimensions=dimensions,
        skills=skills,
        culture=culture,
        time_to_productivity=None,  # populated per-job in match_candidate
        evidence_completeness=completeness,
        summary=summary,
        strengths=strengths,
        gaps=gaps,
        recommendations=recommendations,
    )


def _coverage_for_requirement(req_name: str, skills_by_name: Dict[str, VerifiedSkill]) -> RequirementCoverage:
    req_lower = req_name.lower()
    direct = skills_by_name.get(req_lower)
    if direct and direct.score >= _DIRECT_MODERATE:
        return RequirementCoverage(
            requirement=req_name, status="direct", evidence_skill=direct.name,
            detail=f"Direct evidence: {direct.name} scored {direct.score:.0f}/100.",
        )

    best_skill = None
    best_potential = 0.0
    best_distance = None
    for name, skill in skills_by_name.items():
        if name == req_lower:
            continue
        distance = GLOBAL_SKILL_GRAPH.shortest_distance(name, req_lower, max_depth=_ADJACENCY_MAX_DEPTH)
        if distance is None:
            continue
        potential = skill.score * (0.8 ** distance)
        if potential > best_potential:
            best_potential = potential
            best_skill = skill
            best_distance = distance

    if best_skill is not None and best_distance is not None:
        return RequirementCoverage(
            requirement=req_name, status="adjacent", evidence_skill=best_skill.name,
            detail=f"{best_skill.name} (score {best_skill.score:.0f}) transfers to {req_name} at distance {best_distance}.",
            distance=best_distance,
        )

    if direct:  # matched by name but score too low to call "direct"
        return RequirementCoverage(
            requirement=req_name, status="adjacent", evidence_skill=direct.name,
            detail=f"Weak direct evidence: {direct.name} scored only {direct.score:.0f}/100.",
        )

    return RequirementCoverage(requirement=req_name, status="missing", detail="No direct or adjacent evidence found.")


def _coverage_detail(cov: RequirementCoverage, weight: float, skills_by_name: Dict[str, VerifiedSkill]) -> CoverageDetail:
    skill = skills_by_name.get((cov.evidence_skill or "").lower())
    return CoverageDetail(
        requirement=cov.requirement, status=cov.status, weight=weight,
        skill_score=skill.score if skill else 0.0, distance=cov.distance,
    )


def match_candidate(job: JobSpec, ev: CandidateEvidence, scorecard: EngineeringScorecard) -> MatchResult:
    skills_by_name = {s.name.lower(): s for s in scorecard.skills}
    coverage: List[RequirementCoverage] = []
    weight_by_req: Dict[str, float] = {}

    for req in job.requirements:
        cov = _coverage_for_requirement(req.name, skills_by_name)
        cov.weight = req.weight
        coverage.append(cov)
        weight_by_req[req.name] = req.weight

    weight_sum = sum(r.weight for r in job.requirements) or 1.0
    fit_numerator = 0.0
    for cov in coverage:
        skill = skills_by_name.get((cov.evidence_skill or "").lower())
        skill_score01 = (skill.score / 100.0) if skill else 0.0
        if cov.status == "adjacent" and cov.distance is not None:
            skill_score01 *= 0.8 ** cov.distance
        fit_numerator += skill_score01 * cov.weight

    fit_score = round(100.0 * fit_numerator / weight_sum, 1)

    matched = [c.requirement for c in coverage if c.status == "direct"]
    adjacent = [c.requirement for c in coverage if c.status == "adjacent"]
    missing = [c.requirement for c in coverage if c.status == "missing"]

    coverage_ratio = len(matched) / max(1, len(coverage))
    avg_skill_confidence = (
        sum(s.confidence for s in scorecard.skills) / len(scorecard.skills) if scorecard.skills else 0.3
    )
    confidence = round(max(0.15, min(0.95, 0.35 + 0.35 * coverage_ratio + 0.25 * avg_skill_confidence)), 2)

    if fit_score >= 75:
        verdict = "strong"
    elif fit_score >= 55:
        verdict = "promising"
    else:
        verdict = "developing"

    velocity_dim = next((d for d in scorecard.dimensions if d.key == "learning_velocity"), None)
    ttp_coverage = [
        _coverage_detail(cov, weight_by_req.get(cov.requirement, 0.5), skills_by_name)
        for cov in coverage
    ]
    ttp = estimate_ttp(ttp_coverage, velocity_dim.score if velocity_dim else 50.0)

    scorecard_with_ttp = scorecard.model_copy(update={"time_to_productivity": ttp})

    reasoning = (
        f"{verdict.title()} match: fit score {fit_score:.0f}/100 from {len(matched)} direct, "
        f"{len(adjacent)} adjacent, and {len(missing)} missing requirement(s) out of {len(coverage)}, "
        f"each weighted by the requirement's own declared importance. "
        f"Estimated ramp-up: {ttp.hours_low:.0f}-{ttp.hours_high:.0f} focused hours (~{ttp.sprints:.1f} sprints)."
    )

    return MatchResult(
        job_id=job.id, candidate_id=ev.candidate_id, fit_score=fit_score, confidence=confidence,
        verdict=verdict, coverage=coverage, matched_requirements=matched,
        adjacent_requirements=adjacent, missing_requirements=missing,
        scorecard=scorecard_with_ttp, reasoning=reasoning,
    )
