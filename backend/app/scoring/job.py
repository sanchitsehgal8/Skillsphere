"""Job description → structured requirements.

Upgrades the previous 9-keyword list to the full skill taxonomy (40+ terms,
word-boundary matched so "go" doesn't match "going"), plus optional LLM
extraction for requirements outside the taxonomy — grounded strictly to the JD
text, never invented. Rules always run and always produce a usable result;
the LLM only adds extra, textually-grounded requirements on top.
"""

from __future__ import annotations

import re
from typing import List, Optional

from app.models import JobRequirement, JobSpec
from app.scoring.common import SKILL_CATEGORY, category_of
from app.services.llm import llm

_SOFT_SKILLS = ["communication", "ownership", "leadership", "mentorship", "collaboration"]

_SENIORITY_PATTERNS = [
    (re.compile(r"\b(staff|principal)\b", re.I), "staff/principal"),
    (re.compile(r"\bsenior\b", re.I), "senior"),
    (re.compile(r"\b(mid[- ]?level|intermediate)\b", re.I), "mid"),
    (re.compile(r"\b(junior|entry[- ]?level|new grad|graduate)\b", re.I), "junior"),
]


def _word_boundary(term: str) -> re.Pattern:
    escaped = re.escape(term)
    return re.compile(rf"(?<![\w+#.]){escaped}(?![\w+#])", re.I)


def _rules_requirements(text: str) -> List[JobRequirement]:
    reqs: List[JobRequirement] = []
    for skill in SKILL_CATEGORY:
        if _word_boundary(skill).search(text):
            category = category_of(skill)
            weight = 0.9 if category != "soft-skill" else 0.6
            reqs.append(JobRequirement(name=skill, category=category, weight=weight, source="rules"))
    for skill in _SOFT_SKILLS:
        if _word_boundary(skill).search(text) and not any(r.name == skill for r in reqs):
            reqs.append(JobRequirement(name=skill, category="soft-skill", weight=0.55, source="rules"))
    return reqs


def _detect_seniority(text: str) -> Optional[str]:
    for pattern, label in _SENIORITY_PATTERNS:
        if pattern.search(text):
            return label
    return None


_LLM_SYSTEM = (
    "You extract job requirements. Only list skills/technologies/domains that are "
    "EXPLICITLY mentioned in the job text. Do not infer or add anything not written. "
    "Return strict JSON only: {\"requirements\": [{\"name\": str, \"category\": "
    "\"skill\"|\"domain\"|\"tool\"|\"soft-skill\", \"required\": bool}]}"
)


async def _llm_extra_requirements(text: str, existing: List[JobRequirement]) -> List[JobRequirement]:
    if not llm.is_ready:
        return []
    known = {r.name.lower() for r in existing}
    data = await llm.achat_json(
        [
            {"role": "system", "content": _LLM_SYSTEM},
            {"role": "user", "content": text[:4000]},
        ],
        max_tokens=500,
    )
    if not isinstance(data, dict):
        return []
    extra: List[JobRequirement] = []
    for raw in data.get("requirements", []) or []:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "").strip().lower()
        if not name or name in known or len(name) > 40:
            continue
        # Grounding check: the extracted term (or a close variant) must appear in the text.
        if not _word_boundary(name).search(text) and name not in text.lower():
            continue
        category = raw.get("category") if raw.get("category") in {"skill", "domain", "tool", "soft-skill"} else "skill"
        extra.append(
            JobRequirement(
                name=name, category=category,
                weight=0.5 if category == "soft-skill" else 0.75,
                required=bool(raw.get("required", True)), source="llm",
            )
        )
        known.add(name)
    return extra


async def parse_job(job_id: str, title: str, description: str) -> JobSpec:
    text = f"{title}\n{description}"
    reqs = _rules_requirements(text)
    if not reqs:
        reqs.append(JobRequirement(name="problem solving", category="soft-skill", weight=0.7, source="fallback"))

    try:
        reqs.extend(await _llm_extra_requirements(text, reqs))
    except Exception:  # noqa: BLE001 - JD parsing must never fail because the LLM is down
        pass

    return JobSpec(
        id=job_id, title=title, description=description,
        requirements=reqs, seniority=_detect_seniority(text),
        domains=sorted({r.name for r in reqs if r.category == "domain"}),
    )
