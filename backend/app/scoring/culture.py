"""Explainable engineering culture-fit signals from observable behaviour only.

We never infer personality traits. Every signal here is a re-framing of an
already-observed, explainable behaviour (documentation habits, maintainer
behaviour, initiative language in a resume) with an explicit reasoning string.
If the evidence is missing, the signal is low-confidence, not guessed.
"""

from __future__ import annotations

from typing import List

from app.models import CandidateEvidence, CultureSignal, DimensionScore, Evidence, EvidenceSource


def _from_dimension(dim: DimensionScore, key: str, label: str) -> CultureSignal:
    return CultureSignal(
        key=key, label=label, score=dim.score, confidence=dim.confidence,
        evidence=dim.evidence, reasoning=dim.reasoning,
    )


def _initiative(ev: CandidateEvidence) -> CultureSignal:
    resume = ev.resume
    text = (resume.raw_text if resume else "") or ""
    hackathons = len(resume.hackathons) if resume else 0
    side_projects = len(resume.projects) if resume else 0
    keyword_hit = sum(1 for k in ("initiated", "founded", "launched", "built from scratch", "side project") if k in text.lower())
    score01 = min(1.0, 0.15 * hackathons + 0.1 * side_projects + 0.15 * keyword_hit)
    evidence: List[Evidence] = []
    if hackathons:
        evidence.append(Evidence(source=EvidenceSource.resume, detail=f"{hackathons} hackathon(s) listed."))
    if side_projects:
        evidence.append(Evidence(source=EvidenceSource.resume, detail=f"{side_projects} personal project(s) listed."))
    return CultureSignal(
        key="initiative", label="Initiative", score=round(100 * score01, 1),
        confidence=round(min(1.0, 0.3 + 0.15 * hackathons + 0.1 * side_projects), 2),
        evidence=evidence,
        reasoning="Counts self-directed work (hackathons, personal projects) and initiative language in the resume — not a personality guess.",
    )


def _technical_breadth_depth(dimensions: List[DimensionScore]) -> tuple[CultureSignal, CultureSignal]:
    category_scores = [d.score for d in dimensions if d.key in {"backend", "frontend", "ai_ml", "cloud", "devops"}]
    active = [s for s in category_scores if s > 0]
    breadth_score = min(100.0, 20.0 * len(active))
    depth_score = max(active, default=0.0)
    breadth = CultureSignal(
        key="technical_breadth", label="Technical Breadth", score=round(breadth_score, 1),
        confidence=0.6 if active else 0.2,
        reasoning=f"{len(active)} distinct technical category/categories evidenced ({', '.join(d.label for d in dimensions if d.key in {'backend','frontend','ai_ml','cloud','devops'} and d.score > 0) or 'none'}).",
    )
    depth = CultureSignal(
        key="technical_depth", label="Technical Depth", score=round(depth_score, 1),
        confidence=0.6 if active else 0.2,
        reasoning="Highest single-category score across backend/frontend/AI-ML/cloud/devops, reflecting depth in a primary specialization.",
    )
    return breadth, depth


def build_culture_signals(ev: CandidateEvidence, dimensions: List[DimensionScore]) -> List[CultureSignal]:
    by_key = {d.key: d for d in dimensions}
    signals = [
        _from_dimension(by_key["collaboration"], "collaboration", "Collaboration"),
        _from_dimension(by_key["documentation"], "documentation", "Documentation"),
        _from_dimension(by_key["ownership"], "ownership", "Ownership"),
        _from_dimension(by_key["consistency"], "consistency", "Consistency"),
        _initiative(ev),
    ]
    gh = ev.github
    maintainer = CultureSignal(
        key="maintainer_behaviour", label="Maintainer Behaviour",
        score=round(min(100.0, 100 * (gh.oss_signal if gh else 0.0)), 1),
        confidence=0.55 if gh and gh.public_repos else 0.2,
        evidence=[Evidence(source=EvidenceSource.github, detail=f"{gh.original_repo_count} original repos maintained, {gh.followers} followers.")] if gh else [],
        reasoning="Followers, forks, and org membership as external validation of maintaining code others rely on.",
    )
    signals.append(maintainer)
    communication = CultureSignal(
        key="communication", label="Communication", score=by_key["documentation"].score,
        confidence=by_key["documentation"].confidence,
        reasoning="Proxied by documentation quality (READMEs, docs) as the primary observable written-communication signal available.",
    )
    signals.append(communication)
    breadth, depth = _technical_breadth_depth(dimensions)
    signals.extend([breadth, depth])
    return signals
