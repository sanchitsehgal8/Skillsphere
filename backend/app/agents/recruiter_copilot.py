"""AI Recruiter Copilot — grounded natural-language Q&A over candidate evidence.

Architecture (deliberately "boring" to satisfy "never hallucinate"):

1. **Intent routing is deterministic** (keyword/entity matching), not LLM-based —
   so which candidates and which facts get pulled is 100% reproducible.
2. **The factual answer is always built deterministically** from the caller's
   scorecards/match results — every sentence cites a concrete number that
   exists in those objects. This deterministic answer is complete and correct
   on its own, with or without the LLM.
3. **The LLM (Qwen) only rephrases** those already-computed facts into a
   fluent executive summary, under a strict "do not add facts" system prompt.
   If the LLM is unavailable, times out, or is unreachable, the deterministic
   answer is returned unchanged — the copilot never degrades to "I don't know"
   nor invents an answer.

This means every claim in the final answer traces back to an ``Evidence``-typed
object the caller already computed via the scoring engine.
"""

from __future__ import annotations

import math
import re
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.models import EngineeringScorecard, JobSpec, MatchResult
from app.services.llm import llm


class CandidateContext(BaseModel):
    candidate_id: str
    name: str
    scorecard: EngineeringScorecard
    match: Optional[MatchResult] = None

    model_config = {"arbitrary_types_allowed": True}


class CopilotAnswer(BaseModel):
    answer: str
    grounded_facts: str
    llm_assisted: bool
    candidates_referenced: List[str] = []


_DIMENSION_KEYWORDS = {
    "backend": ["backend", "back-end", "server-side"],
    "frontend": ["frontend", "front-end", "ui engineer", "client-side"],
    "ai_ml": ["ai", "ml", "machine learning", "ai/ml"],
    "cloud": ["cloud"],
    "devops": ["devops", "sre", "infrastructure"],
    "system_design": ["system design", "architecture", "distributed"],
    "testing": ["testing", "qa", "quality"],
    "documentation": ["documentation", "docs", "technical writing"],
    "open_source": ["open source", "oss"],
    "programming": ["programmer", "engineer", "developer", "coding"],
    "problem_solving": ["problem solving", "algorithm", "competitive"],
    "ownership": ["ownership", "self-directed"],
    "collaboration": ["collaboration", "teamwork"],
    "learning_velocity": ["learning", "fast learner", "adaptable"],
}
_STRONG_TERMS = ["strong", "senior", "excellent", "top", "best"]
_WEAK_TERMS = ["junior", "entry", "weak"]


def _find_mentioned_candidates(query: str, contexts: List[CandidateContext]) -> List[CandidateContext]:
    q = query.lower()
    found = []
    for c in contexts:
        if c.candidate_id.lower() in q or (c.name and c.name.lower() in q):
            found.append(c)
    return found


def _best_by_overall(contexts: List[CandidateContext]) -> Optional[CandidateContext]:
    return max(contexts, key=lambda c: c.scorecard.overall_score, default=None)


def _best_by_fit(contexts: List[CandidateContext]) -> Optional[CandidateContext]:
    with_match = [c for c in contexts if c.match]
    if not with_match:
        return None
    return max(with_match, key=lambda c: c.match.fit_score)


def _skill_vector(sc: EngineeringScorecard) -> Dict[str, float]:
    return {s.name.lower(): s.score for s in sc.skills}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = set(a) | set(b)
    num = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    return num / (da * db) if da and db else 0.0


def _dim_score(ctx: CandidateContext, key: str) -> Optional[float]:
    return next((d.score for d in ctx.scorecard.dimensions if d.key == key), None)


# --------------------------------------------------------------------------- #
# Intent handlers — each returns (deterministic_answer, facts_for_llm, referenced_ids)
# --------------------------------------------------------------------------- #
def _handle_find(query: str, contexts: List[CandidateContext]) -> tuple[str, dict, List[str]]:
    q = query.lower()
    matched_dims = [key for key, kws in _DIMENSION_KEYWORDS.items() if any(k in q for k in kws)]
    dim_key = matched_dims[0] if matched_dims else "programming"
    threshold = 65.0 if any(t in q for t in _STRONG_TERMS) else (30.0 if any(t in q for t in _WEAK_TERMS) else 45.0)

    scored = []
    for c in contexts:
        val = _dim_score(c, dim_key)
        if val is not None:
            scored.append((c, val))
    scored.sort(key=lambda t: t[1], reverse=True)
    qualifying = [(c, v) for c, v in scored if v >= threshold][:8]

    label = next((d.label for c in contexts for d in c.scorecard.dimensions if d.key == dim_key), dim_key)
    if not qualifying:
        text = f"No candidates in this pool meet a {label} score of {threshold:.0f}+. Highest available: " + (
            f"{scored[0][0].name} at {scored[0][1]:.0f}/100." if scored else "none evaluated yet."
        )
        return text, {"dimension": label, "threshold": threshold, "results": []}, []

    lines = [f"{len(qualifying)} candidate(s) meet {label} ≥ {threshold:.0f}:"]
    for c, v in qualifying:
        top_skill = c.scorecard.skills[0] if c.scorecard.skills else None
        evidence_bit = f" — top skill {top_skill.name} ({top_skill.score:.0f}/100, {top_skill.repo_count} repo(s))" if top_skill else ""
        lines.append(f"• {c.name}: {label} {v:.0f}/100{evidence_bit}")
    facts = {"dimension": label, "threshold": threshold, "results": [{"id": c.candidate_id, "name": c.name, "score": v} for c, v in qualifying]}
    return "\n".join(lines), facts, [c.candidate_id for c, _ in qualifying]


def _handle_similar(query: str, contexts: List[CandidateContext]) -> tuple[str, dict, List[str]]:
    mentioned = _find_mentioned_candidates(query, contexts)
    reference = mentioned[0] if mentioned else _best_by_overall(contexts)
    if not reference:
        return "No candidates are available to compare against.", {}, []

    others = [c for c in contexts if c.candidate_id != reference.candidate_id]
    ref_vec = _skill_vector(reference.scorecard)
    ranked = sorted(others, key=lambda c: _cosine(ref_vec, _skill_vector(c.scorecard)), reverse=True)[:5]
    if not ranked:
        return f"{reference.name} is the only candidate in this pool — nothing to compare against.", {}, [reference.candidate_id]

    lines = [f"Candidates most similar to {reference.name} (by verified skill overlap):"]
    for c in ranked:
        sim = _cosine(ref_vec, _skill_vector(c.scorecard))
        shared = sorted(set(ref_vec) & set(_skill_vector(c.scorecard)))[:5]
        lines.append(f"• {c.name}: {sim:.0%} skill-vector similarity, shared skills: {', '.join(shared) or 'none'}")
    facts = {
        "reference": reference.name,
        "results": [{"name": c.name, "similarity": round(_cosine(ref_vec, _skill_vector(c.scorecard)), 3)} for c in ranked],
    }
    return "\n".join(lines), facts, [reference.candidate_id] + [c.candidate_id for c in ranked]


def _handle_compare(query: str, contexts: List[CandidateContext], job: Optional[JobSpec]) -> tuple[str, dict, List[str]]:
    mentioned = _find_mentioned_candidates(query, contexts)
    if len(mentioned) >= 2:
        a, b = mentioned[0], mentioned[1]
    elif len(mentioned) == 1:
        a = mentioned[0]
        b = _best_by_overall([c for c in contexts if c.candidate_id != a.candidate_id])
    else:
        ranked = sorted(contexts, key=lambda c: c.scorecard.overall_score, reverse=True)
        a, b = (ranked[0], ranked[1]) if len(ranked) >= 2 else (ranked[0] if ranked else None, None)

    if not a or not b:
        return "Need at least two candidates in this pool to compare.", {}, []

    lines = [f"{a.name} vs {b.name}:"]
    lines.append(f"• Overall score: {a.name} {a.scorecard.overall_score:.0f} vs {b.name} {b.scorecard.overall_score:.0f}/100.")
    a_dims = {d.key: d for d in a.scorecard.dimensions}
    b_dims = {d.key: d for d in b.scorecard.dimensions}
    diffs = []
    for key, da in a_dims.items():
        db = b_dims.get(key)
        if db is None or (da.score == 0 and db.score == 0):
            continue
        diffs.append((abs(da.score - db.score), da.label, da.score, db.score))
    diffs.sort(reverse=True)
    for _, label, sa, sb in diffs[:5]:
        leader = a.name if sa > sb else (b.name if sb > sa else "tied")
        lines.append(f"• {label}: {a.name} {sa:.0f} vs {b.name} {sb:.0f} — {leader} ahead." if leader != "tied" else f"• {label}: tied at {sa:.0f}.")
    if a.match and b.match and job:
        lines.append(f"• Fit for {job.title}: {a.name} {a.match.fit_score:.0f} vs {b.name} {b.match.fit_score:.0f}/100.")
    facts = {
        "a": {"name": a.name, "overall": a.scorecard.overall_score},
        "b": {"name": b.name, "overall": b.scorecard.overall_score},
        "top_dimension_diffs": [{"label": l, "a": sa, "b": sb} for _, l, sa, sb in diffs[:5]],
    }
    return "\n".join(lines), facts, [a.candidate_id, b.candidate_id]


def _handle_why_rank(query: str, contexts: List[CandidateContext], job: Optional[JobSpec]) -> tuple[str, dict, List[str]]:
    mentioned = _find_mentioned_candidates(query, contexts)
    if len(mentioned) >= 2:
        higher, lower = sorted(mentioned[:2], key=lambda c: (c.match.fit_score if c.match else c.scorecard.overall_score), reverse=True)
    elif len(mentioned) == 1:
        c = mentioned[0]
        best = _best_by_fit(contexts) if job else _best_by_overall(contexts)
        if not best or best.candidate_id == c.candidate_id:
            return f"{c.name} is already the top-ranked candidate in this pool.", {}, [c.candidate_id]
        higher, lower = best, c
    else:
        ranked = sorted(contexts, key=lambda c: (c.match.fit_score if c.match else c.scorecard.overall_score), reverse=True)
        if len(ranked) < 2:
            return "Need at least two candidates to explain a ranking difference.", {}, []
        higher, lower = ranked[0], ranked[1]

    lines = [f"{higher.name} ranks above {lower.name}:"]
    if higher.match and lower.match:
        lines.append(f"• Fit score: {higher.match.fit_score:.0f} vs {lower.match.fit_score:.0f}/100.")
        only_higher = set(higher.match.matched_requirements) - set(lower.match.matched_requirements)
        only_lower = set(lower.match.matched_requirements) - set(higher.match.matched_requirements)
        if only_higher:
            lines.append(f"• {higher.name} directly covers: {', '.join(sorted(only_higher))} (not matched for {lower.name}).")
        if only_lower:
            lines.append(f"• {lower.name} directly covers: {', '.join(sorted(only_lower))} (not matched for {higher.name}).")
    a_dims = {d.key: d for d in higher.scorecard.dimensions}
    b_dims = {d.key: d for d in lower.scorecard.dimensions}
    diffs = sorted(
        ((a_dims[k].score - b_dims[k].score, a_dims[k].label) for k in a_dims if k in b_dims),
        reverse=True,
    )[:3]
    for delta, label in diffs:
        if delta > 3:
            lines.append(f"• {label}: {higher.name} leads by {delta:.0f} points.")
    facts = {"higher": higher.name, "lower": lower.name, "dimension_leads": [{"label": l, "delta": d} for d, l in diffs]}
    return "\n".join(lines), facts, [higher.candidate_id, lower.candidate_id]


def _handle_missing_skills(query: str, contexts: List[CandidateContext], job: Optional[JobSpec]) -> tuple[str, dict, List[str]]:
    if not job:
        return "No job description is loaded — provide a job to check skill gaps against.", {}, []
    mentioned = _find_mentioned_candidates(query, contexts)
    targets = mentioned if mentioned else contexts

    lines = [f"Skill gaps against \"{job.title}\":"]
    facts_results = []
    for c in targets:
        if not c.match:
            continue
        if not c.match.missing_requirements and not c.match.adjacent_requirements:
            lines.append(f"• {c.name}: full direct coverage of all requirements.")
        else:
            parts = []
            if c.match.missing_requirements:
                parts.append(f"missing {', '.join(c.match.missing_requirements)}")
            if c.match.adjacent_requirements:
                parts.append(f"adjacent-only on {', '.join(c.match.adjacent_requirements)}")
            lines.append(f"• {c.name}: {'; '.join(parts)}.")
        facts_results.append({"name": c.name, "missing": c.match.missing_requirements, "adjacent": c.match.adjacent_requirements})
    if not facts_results:
        return "No match results are available yet for these candidates against this job.", {}, []
    return "\n".join(lines), {"job": job.title, "results": facts_results}, [c.candidate_id for c in targets if c.match]


def _handle_shortlist(contexts: List[CandidateContext], job: Optional[JobSpec]) -> tuple[str, dict, List[str]]:
    if not contexts:
        return "No candidates have been analyzed yet.", {}, []
    ranked = sorted(
        contexts, key=lambda c: (c.match.fit_score if c.match else c.scorecard.overall_score), reverse=True
    )
    header = f"Shortlist for {job.title}:" if job else "Candidate shortlist (no job selected):"
    lines = [header]
    for rank, c in enumerate(ranked, start=1):
        score = c.match.fit_score if c.match else c.scorecard.overall_score
        verdict = c.match.verdict if c.match else "unscored"
        lines.append(f"{rank}. {c.name} — {score:.0f}/100 ({verdict}); overall engineering score {c.scorecard.overall_score:.0f}/100.")
    facts = {"job": job.title if job else None, "ranked": [{"name": c.name, "score": (c.match.fit_score if c.match else c.scorecard.overall_score)} for c in ranked]}
    return "\n".join(lines), facts, [c.candidate_id for c in ranked]


_GLOSS_SYSTEM = (
    "You are a recruiter's AI copilot. You will be given (1) a recruiter question and "
    "(2) a JSON object of facts already computed by a deterministic scoring engine. "
    "Write a concise (max 70 words) executive answer using ONLY numbers and names that "
    "appear in the JSON. Never introduce a candidate, score, or skill not present in the "
    "JSON. If the JSON is empty or does not answer the question, say the data is not "
    "available. Do not repeat the JSON verbatim — synthesize it into prose."
)


async def _llm_gloss(query: str, facts: dict) -> Optional[str]:
    if not llm.is_ready or not facts:
        return None
    import json

    text = await llm.achat(
        [
            {"role": "system", "content": _GLOSS_SYSTEM},
            {"role": "user", "content": f"Question: {query}\n\nFacts JSON:\n{json.dumps(facts, default=str)[:3000]}"},
        ],
        max_tokens=180,
        temperature=0.2,
    )
    if text and not _gloss_is_grounded(text, facts):
        return None  # small models occasionally swap A/B attribution — never surface an ungrounded claim
    return text


def _two_names(facts: dict) -> Optional[tuple[str, str]]:
    if isinstance(facts.get("a"), dict) and isinstance(facts.get("b"), dict):
        return facts["a"].get("name"), facts["b"].get("name")
    if facts.get("higher") and facts.get("lower"):
        return facts["higher"], facts["lower"]
    return None


def _leader_entries(facts: dict) -> List[tuple[str, str, str]]:
    """(dimension_label, correct_leader_name, correct_trailer_name) for every dimension the facts compare."""
    names = _two_names(facts)
    if not names:
        return []
    name_a, name_b = names
    entries: List[tuple[str, str, str]] = []
    for e in facts.get("top_dimension_diffs", []):
        if e.get("a") == e.get("b"):
            continue
        leader = name_a if e["a"] > e["b"] else name_b
        trailer = name_b if leader == name_a else name_a
        entries.append((e["label"], leader, trailer))
    for e in facts.get("dimension_leads", []):
        # `higher` (name_a) always leads in this facts shape by construction.
        entries.append((e["label"], name_a, name_b))
    return entries


def _gloss_is_grounded(gloss: str, facts: dict) -> bool:
    """Reject a gloss that names the wrong candidate as leading on a dimension.

    Heuristic: for each dimension label the gloss mentions, look at the text
    immediately around it — if the *trailing* candidate's name appears there
    without the true leader's name also appearing, the model likely swapped
    attribution (observed in practice with the 7B model on compound sentences).
    """
    entries = _leader_entries(facts)
    if not entries:
        return True
    low = gloss.lower()
    for label, leader, trailer in entries:
        idx = low.find(label.lower())
        if idx == -1:
            continue
        window = low[max(0, idx - 60): idx + 60]
        if trailer.lower() in window and leader.lower() not in window:
            return False
    return True


async def answer_query(
    query: str, contexts: List[CandidateContext], job: Optional[JobSpec] = None
) -> CopilotAnswer:
    q = query.lower().strip()

    if re.search(r"\b(vs|versus|compare)\b", q):
        det_text, facts, refs = _handle_compare(query, contexts, job)
    elif re.search(r"\bwhy\b.*\b(rank|higher|above|better)\b", q):
        det_text, facts, refs = _handle_why_rank(query, contexts, job)
    elif re.search(r"\bsimilar to\b|\blike\b.*\bengineer\b", q):
        det_text, facts, refs = _handle_similar(query, contexts)
    elif re.search(r"\bmissing\b|\bgap\b|\blacks?\b", q) and re.search(r"\bskill|\brequirement|\bjd\b|\bjob\b", q):
        det_text, facts, refs = _handle_missing_skills(query, contexts, job)
    elif re.search(r"\bfind\b|\bshow\b|\bwho (has|is|are)\b|\bcandidates? with\b", q):
        det_text, facts, refs = _handle_find(query, contexts)
    else:
        det_text, facts, refs = _handle_shortlist(contexts, job)

    gloss = await _llm_gloss(query, facts) if facts else None
    if gloss:
        combined = f"{gloss}\n\n— Evidence —\n{det_text}"
        return CopilotAnswer(answer=combined, grounded_facts=det_text, llm_assisted=True, candidates_referenced=refs)
    return CopilotAnswer(answer=det_text, grounded_facts=det_text, llm_assisted=False, candidates_referenced=refs)


def summarize_candidate(ctx: CandidateContext) -> str:
    sc = ctx.scorecard
    lines = [f"{ctx.name}: overall {sc.overall_score:.0f}/100 (confidence {sc.overall_confidence:.0%})."]
    if sc.skills:
        top = ", ".join(f"{s.name} ({s.score:.0f})" for s in sc.skills[:5])
        lines.append(f"Top verified skills: {top}.")
    if ctx.match:
        lines.append(
            f"Fit for {ctx.match.job_id}: {ctx.match.fit_score:.0f}/100 ({ctx.match.verdict}). "
            f"Ramp-up: {ctx.match.scorecard.time_to_productivity.hours_low:.0f}-{ctx.match.scorecard.time_to_productivity.hours_high:.0f}h."
            if ctx.match.scorecard.time_to_productivity else ""
        )
    return "\n".join(l for l in lines if l)
