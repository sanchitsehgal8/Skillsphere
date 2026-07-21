"""Evidence-based skill verification.

Replaces static "skill percentages" with a per-skill score that is a direct
function of observable evidence: repos, bytes of code (LOC proxy), frameworks,
recency, resume corroboration, and OSS signal (stars/forks as external
validation). No skill is emitted without at least one evidence item.
"""

from __future__ import annotations

from typing import Dict, List

from app.models import CandidateEvidence, Evidence, EvidenceSource, VerifiedSkill
from app.scoring.common import (
    FRAMEWORK_LANGUAGE,
    canon_lang,
    category_of,
    log_norm,
    recency_score,
    to_100,
)


def _language_skills(ev: CandidateEvidence) -> Dict[str, VerifiedSkill]:
    gh = ev.github
    out: Dict[str, VerifiedSkill] = {}
    if not gh or not gh.languages_bytes:
        return out

    max_bytes = max(gh.languages_bytes.values()) if gh.languages_bytes else 1
    account_years = gh.account_age_years or 0.1

    for lang, bytes_count in gh.languages_bytes.items():
        canon = canon_lang(lang)
        if canon in {"html", "css"}:
            continue  # markup, not a programming-skill signal on its own
        repo_count = gh.languages_repo_count.get(lang, 0)
        share = bytes_count / max_bytes if max_bytes else 0.0
        rec = recency_score(gh.most_recent_push_days)

        loc_component = log_norm(bytes_count, 400_000)  # ~400KB ceiling per lang
        breadth_component = log_norm(repo_count, 10)
        oss_component = gh.oss_signal

        score01 = (
            0.40 * loc_component
            + 0.20 * breadth_component
            + 0.15 * share
            + 0.15 * rec
            + 0.10 * oss_component
        )
        frameworks = sorted(
            f for f in gh.frameworks if FRAMEWORK_LANGUAGE.get(f, "").lower() == canon
        )
        evidence = [
            Evidence(
                source=EvidenceSource.github,
                detail=f"{bytes_count:,} bytes of {lang} across {repo_count} repositor{'y' if repo_count == 1 else 'ies'}.",
                metric=float(bytes_count),
                unit="bytes",
            ),
        ]
        if gh.most_recent_push_days is not None:
            evidence.append(
                Evidence(
                    source=EvidenceSource.github,
                    detail=f"Most recent push {gh.most_recent_push_days} days ago.",
                    metric=float(gh.most_recent_push_days),
                    unit="days",
                )
            )
        if frameworks:
            evidence.append(
                Evidence(
                    source=EvidenceSource.github,
                    detail=f"Used with framework(s): {', '.join(frameworks)}.",
                )
            )

        confidence = min(1.0, 0.35 + 0.35 * breadth_component + 0.2 * rec + 0.1 * min(account_years / 3, 1.0))

        out[canon] = VerifiedSkill(
            name=canon,
            category=category_of(canon),
            score=to_100(score01),
            confidence=round(confidence, 2),
            repo_count=repo_count,
            loc_bytes=bytes_count,
            commit_recency_days=gh.most_recent_push_days,
            frameworks=frameworks,
            projects=[r.name for r in gh.repos if canon_lang(r.primary_language or "") == canon][:5],
            oss_contributions=len(gh.contributed_orgs),
            complexity=max((r.complexity for r in gh.repos if canon_lang(r.primary_language or "") == canon), default=0.0),
            evidence=evidence,
            reasoning=(
                f"Derived from {bytes_count:,} bytes of {lang} across {repo_count} repos "
                f"({share:.0%} of your largest language by volume), weighted by recency and OSS validation."
            ),
            suggestions=(
                [] if score01 >= 0.6 else [f"Ship a larger or more recent {lang} project to strengthen this signal."]
            ),
        )
    return out


def _framework_skills(ev: CandidateEvidence, langs: Dict[str, VerifiedSkill]) -> Dict[str, VerifiedSkill]:
    gh = ev.github
    out: Dict[str, VerifiedSkill] = {}
    if not gh:
        return out
    for fw in gh.frameworks:
        owner_lang = canon_lang(FRAMEWORK_LANGUAGE.get(fw, ""))
        owner = langs.get(owner_lang)
        base_score = owner.score if owner else 55.0
        confidence = 0.55 if owner else 0.4
        matching_repos = [r.name for r in gh.repos if fw.lower() in (r.description or "").lower() or fw.lower() in " ".join(r.topics).lower()]
        resolved_category = category_of(fw.lower())
        out[fw.lower()] = VerifiedSkill(
            name=fw,
            category=resolved_category if resolved_category != "skill" else "framework",
            score=round(base_score, 1),
            confidence=confidence,
            repo_count=len(matching_repos) or 1,
            projects=matching_repos[:5],
            evidence=[
                Evidence(
                    source=EvidenceSource.github,
                    detail=f"Detected via repository topics/descriptions ({fw}).",
                )
            ],
            reasoning=f"Inferred from GitHub repository metadata mentioning {fw}; scored relative to underlying {owner_lang or 'language'} evidence.",
        )
    return out


def _resume_corroboration(ev: CandidateEvidence, skills: Dict[str, VerifiedSkill]) -> None:
    resume = ev.resume
    if not resume or not resume.skills:
        return
    for raw in resume.skills:
        key = raw.lower()
        if key in skills:
            s = skills[key]
            s.score = min(100.0, s.score + 8.0)
            s.confidence = min(1.0, s.confidence + 0.1)
            s.evidence.append(
                Evidence(source=EvidenceSource.resume, detail="Also listed on resume — corroborates GitHub evidence.")
            )
            s.reasoning += " Corroborated by resume."
        else:
            skills[key] = VerifiedSkill(
                name=raw,
                category=category_of(key),
                score=45.0,
                confidence=0.35,
                evidence=[Evidence(source=EvidenceSource.resume, detail="Claimed on resume; no public code evidence found yet.")],
                reasoning="Resume-only claim without corroborating GitHub activity — lower confidence until verified by code.",
                suggestions=["Link a public repository that demonstrates this skill to raise confidence."],
            )


def verify_skills(ev: CandidateEvidence) -> List[VerifiedSkill]:
    langs = _language_skills(ev)
    frameworks = _framework_skills(ev, langs)
    skills: Dict[str, VerifiedSkill] = {**langs, **frameworks}
    _resume_corroboration(ev, skills)
    return sorted(skills.values(), key=lambda s: s.score, reverse=True)
