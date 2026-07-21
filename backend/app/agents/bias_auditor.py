"""Fairness audit over ranked candidates.

The previous implementation ran a ~1.6GB zero-shot NLI model
(``facebook/bart-large-mnli``) against the ranking rationale text to detect
"bias probability." Removed: the rationale text is entirely generated from
numeric evidence (skill scores, requirement coverage) and structurally cannot
contain demographic language, so the classifier was analyzing text that had no
signal to find — a large, slow, failure-prone dependency for no measurable
benefit (its cold start alone risked never loading in production, silently
disabling the check either way).

What is actually evidence-based and worth computing:
- **Group-level disparity**: do candidates in an observed protected group score
  systematically lower than the rest of the pool?
- **Rank concentration**: are protected-group candidates disproportionately
  clustered in the bottom half of the ranking?

Both are deterministic, reproducible, and directly inspectable — the numbers
that trigger a flag are the numbers shown in the flag.
"""

from __future__ import annotations

from typing import Dict, List

from app.models import BiasFlag, CandidateEvidence, FairnessReport, MatchResult

_PROTECTED_GENDERS = {"female", "non-binary", "nonbinary"}
_DISPARITY_FLAG_THRESHOLD = 10.0   # points on a 0-100 fit_score scale
_DISPARITY_HIGH_THRESHOLD = 18.0


def _is_protected(ev: CandidateEvidence) -> bool:
    gender = (ev.demographics.get("gender") or "").strip().lower()
    return gender in _PROTECTED_GENDERS


def audit(
    job_id: str,
    ranked_results: List[MatchResult],
    candidates_by_id: Dict[str, CandidateEvidence],
) -> FairnessReport:
    ranked = sorted(ranked_results, key=lambda r: r.fit_score, reverse=True)
    protected_ids = {
        cid for cid, ev in candidates_by_id.items() if isinstance(ev, CandidateEvidence) and _is_protected(ev)
    }

    protected_scores = [r.fit_score for r in ranked if r.candidate_id in protected_ids]
    other_scores = [r.fit_score for r in ranked if r.candidate_id not in protected_ids]
    protected_mean = sum(protected_scores) / len(protected_scores) if protected_scores else None
    other_mean = sum(other_scores) / len(other_scores) if other_scores else None
    disparity = (other_mean - protected_mean) if (protected_mean is not None and other_mean is not None) else None

    flags: List[BiasFlag] = []
    n = len(ranked)
    for rank, r in enumerate(ranked, start=1):
        if r.candidate_id not in protected_ids:
            continue
        if rank > n // 2 and n >= 4:
            flags.append(
                BiasFlag(
                    candidate_id=r.candidate_id,
                    reason=f"Ranked {rank} of {n} — in the bottom half despite belonging to an observed protected group.",
                    severity="low",
                )
            )
        if disparity is not None and disparity > _DISPARITY_FLAG_THRESHOLD:
            flags.append(
                BiasFlag(
                    candidate_id=r.candidate_id,
                    reason=(
                        f"Group-level disparity: protected-group average fit score "
                        f"({protected_mean:.1f}) is {disparity:.1f} points below the rest of the pool "
                        f"({other_mean:.1f})."
                    ),
                    severity="high" if disparity > _DISPARITY_HIGH_THRESHOLD else "medium",
                )
            )

    note = (
        f"{len(protected_ids)} of {n} candidate(s) in an observed protected group."
        if protected_ids else
        "No demographic data was provided for this candidate pool — fairness audit has no group to compare."
    )
    return FairnessReport(job_id=job_id, flags=flags, group_disparity=disparity, note=note)
