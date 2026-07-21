"""17 explainable engineering dimensions, each a pure function of evidence.

Every dimension returns a ``DimensionScore`` with score, confidence, the
evidence it was computed from, plain-language reasoning, and (when the score
is not already strong) concrete improvement suggestions. No dimension uses an
arbitrary weight against other dimensions here — cross-dimension weighting for
the single overall score happens in ``engine.py`` and is documented there.
"""

from __future__ import annotations

from typing import List

from app.models import CandidateEvidence, DimensionScore, Evidence, EvidenceSource, VerifiedSkill
from app.scoring.common import log_norm, recency_score, to_100

_CATEGORY_DIMENSION = {
    "backend": "backend",
    "frontend": "frontend",
    "ai/ml": "ai_ml",
    "cloud": "cloud",
    "devops": "devops",
}


def _skills_in(skills: List[VerifiedSkill], category: str) -> List[VerifiedSkill]:
    return [s for s in skills if s.category == category]


def _category_dimension(
    key: str, label: str, skills: List[VerifiedSkill], category: str
) -> DimensionScore:
    matched = _skills_in(skills, category)
    if not matched:
        return DimensionScore(
            key=key, label=label, score=0.0, confidence=0.15,
            reasoning=f"No {label.lower()} evidence found in public repositories or resume.",
            suggestions=[f"Add a public {label.lower()} project so this dimension can be evaluated."],
        )
    top = sorted(matched, key=lambda s: s.score, reverse=True)[:4]
    avg = sum(s.score for s in top) / len(top)
    breadth_bonus = min(10.0, 2.5 * (len(matched) - 1))
    score = min(100.0, avg + breadth_bonus)
    confidence = min(1.0, sum(s.confidence for s in top) / len(top) + 0.05 * (len(matched) - 1))
    evidence = [
        Evidence(source=EvidenceSource.derived, detail=f"{s.name}: {s.score:.0f}/100 ({s.repo_count} repo(s)).", metric=s.score)
        for s in top
    ]
    return DimensionScore(
        key=key, label=label, score=round(score, 1), confidence=round(confidence, 2),
        evidence=evidence,
        reasoning=f"Averaged top {len(top)} {label.lower()} skill(s) — {', '.join(s.name for s in top)} — with a breadth bonus for {len(matched)} distinct skill(s).",
        suggestions=[] if score >= 60 else [f"Deepen one {label.lower()} project with tests and documentation to raise this score."],
    )


def score_programming(skills: List[VerifiedSkill]) -> DimensionScore:
    langs = [s for s in skills if s.category == "language"]
    if not langs:
        return DimensionScore(
            key="programming", label="Programming", score=0.0, confidence=0.15,
            reasoning="No language-level evidence found (no GitHub languages, no resume skills).",
            suggestions=["Link a GitHub profile with public repositories."],
        )
    top = sorted(langs, key=lambda s: s.score, reverse=True)[:3]
    avg = sum(s.score for s in top) / len(top)
    breadth_bonus = min(12.0, 3.0 * (len(langs) - 1))
    score = min(100.0, avg + breadth_bonus)
    confidence = min(1.0, sum(s.confidence for s in top) / len(top))
    return DimensionScore(
        key="programming", label="Programming", score=round(score, 1), confidence=round(confidence, 2),
        evidence=[Evidence(source=EvidenceSource.derived, detail=f"{s.name}: {s.score:.0f}/100.", metric=s.score) for s in top],
        reasoning=f"Top languages by evidence: {', '.join(s.name for s in top)}. Breadth across {len(langs)} language(s) contributes a bonus.",
        suggestions=[] if score >= 60 else ["Grow depth in your primary language with a larger, actively-maintained project."],
    )


def score_problem_solving(ev: CandidateEvidence) -> DimensionScore:
    cf = ev.codeforces or {}
    stats = cf.get("stats_overview") if isinstance(cf, dict) else None
    if stats:
        rating = stats.get("current_rating") or 0
        solved = stats.get("total_problems_solved") or 0
        rating_component = min(1.0, rating / 2200) if rating else 0.0
        solved_component = log_norm(solved, 800)
        score01 = 0.6 * rating_component + 0.4 * solved_component
        return DimensionScore(
            key="problem_solving", label="Problem Solving", score=to_100(score01), confidence=0.8,
            evidence=[
                Evidence(source=EvidenceSource.codeforces, detail=f"Codeforces rating {rating}, {solved} problems solved.", metric=float(rating)),
            ],
            reasoning=f"Derived directly from Codeforces rating ({rating}) and {solved} solved problems.",
            suggestions=[] if score01 >= 0.5 else ["Practice more rated Codeforces contests to build a stronger algorithmic signal."],
        )
    resume = ev.resume
    text = (resume.raw_text if resume else "") or ""
    has_algo = any(k in text.lower() for k in ("algorithm", "leetcode", "competitive programming", "data structure"))
    if has_algo:
        return DimensionScore(
            key="problem_solving", label="Problem Solving", score=50.0, confidence=0.35,
            evidence=[Evidence(source=EvidenceSource.resume, detail="Resume references algorithms/competitive programming.")],
            reasoning="No Codeforces handle provided; resume mentions algorithmic work, giving a low-confidence baseline.",
            suggestions=["Provide a Codeforces or LeetCode handle for a verifiable problem-solving signal."],
        )
    return DimensionScore(
        key="problem_solving", label="Problem Solving", score=0.0, confidence=0.15,
        reasoning="No competitive-programming or algorithmic evidence found.",
        suggestions=["Add a Codeforces handle to measure algorithmic problem-solving with real data."],
    )


def score_system_design(ev: CandidateEvidence, skills: List[VerifiedSkill]) -> DimensionScore:
    gh = ev.github
    resume_text = (ev.resume.raw_text if ev.resume else "") or ""
    keyword_hit = any(k in resume_text.lower() for k in ("system design", "microservices", "distributed system", "architecture"))
    complexities = [r.complexity for r in (gh.repos if gh else []) if r.complexity]
    complexity_component = (sum(complexities) / len(complexities)) if complexities else 0.0
    multi_lang_repos = sum(1 for r in (gh.repos if gh else []) if len(r.languages_bytes) >= 3)
    breadth_component = log_norm(multi_lang_repos, 5)
    backend_cloud = [s for s in skills if s.category in ("backend", "cloud", "devops")]
    stack_component = min(1.0, len(backend_cloud) / 4.0)

    score01 = 0.4 * complexity_component + 0.25 * breadth_component + 0.2 * stack_component + 0.15 * (1.0 if keyword_hit else 0.0)
    evidence = []
    if complexities:
        evidence.append(Evidence(source=EvidenceSource.derived, detail=f"Average structural complexity across repos: {complexity_component:.2f} (0-1 scale).", metric=complexity_component))
    if multi_lang_repos:
        evidence.append(Evidence(source=EvidenceSource.github, detail=f"{multi_lang_repos} repo(s) combine 3+ languages, suggesting multi-service or full-stack design."))
    if keyword_hit:
        evidence.append(Evidence(source=EvidenceSource.resume, detail="Resume explicitly references system design / distributed systems / architecture."))
    return DimensionScore(
        key="system_design", label="System Design", score=to_100(score01), confidence=round(min(1.0, 0.3 + 0.5 * complexity_component + 0.2 * stack_component), 2),
        evidence=evidence,
        reasoning="Combines repository structural complexity, multi-language/service breadth, backend+cloud+devops stack coverage, and explicit resume evidence.",
        suggestions=[] if score01 >= 0.5 else ["Document architectural decisions (e.g. an ADR or design doc) in a repository README to evidence system design thinking."],
    )


def score_code_quality(ev: CandidateEvidence) -> DimensionScore:
    gh = ev.github
    if not gh or not gh.repos:
        return DimensionScore(key="code_quality", label="Code Quality", score=0.0, confidence=0.15, reasoning="No repositories available to assess.", suggestions=["Add public repositories to evidence code quality."])

    avg_complexity = sum(r.complexity for r in gh.repos) / len(gh.repos)

    if not gh.structural_analysis_available:
        # CI/test presence was never measured (requires GITHUB_TOKEN) — score
        # only from the complexity evidence we do have, at reduced confidence.
        # Critically: do NOT treat "unmeasured" as "measured zero" (that was a
        # real bug — it silently capped every unauthenticated candidate's score
        # near 25/100 regardless of actual code quality).
        score01 = avg_complexity
        return DimensionScore(
            key="code_quality", label="Code Quality", score=to_100(score01), confidence=0.35,
            evidence=[Evidence(source=EvidenceSource.derived, detail=f"Repository structural complexity: {avg_complexity:.2f} (0-1 scale). CI/test presence not measured.", metric=avg_complexity)],
            reasoning="CI and test-suite presence require GITHUB_TOKEN and were not measured for this candidate — score reflects only repository structural complexity, at reduced confidence.",
            suggestions=["Configure GITHUB_TOKEN on the backend to unlock full CI/test-based code-quality analysis."],
        )

    score01 = 0.4 * gh.ci_repo_ratio + 0.35 * gh.tested_repo_ratio + 0.25 * avg_complexity
    return DimensionScore(
        key="code_quality", label="Code Quality", score=to_100(score01), confidence=0.7,
        evidence=[
            Evidence(source=EvidenceSource.github, detail=f"{gh.ci_repo_ratio:.0%} of sampled repos have CI configured.", metric=gh.ci_repo_ratio),
            Evidence(source=EvidenceSource.github, detail=f"{gh.tested_repo_ratio:.0%} of sampled repos have a test suite.", metric=gh.tested_repo_ratio),
        ],
        reasoning="Weighted average of CI presence, test suite presence, and repository structural complexity across sampled repositories.",
        suggestions=[] if score01 >= 0.55 else ["Add automated tests and a CI workflow to your primary repository."],
    )


def score_documentation(ev: CandidateEvidence) -> DimensionScore:
    gh = ev.github
    if not gh or not gh.repos:
        return DimensionScore(key="documentation", label="Documentation", score=0.0, confidence=0.15, reasoning="No repositories available to assess.")
    if not gh.structural_analysis_available:
        return DimensionScore(
            key="documentation", label="Documentation", score=45.0, confidence=0.2,
            reasoning="README/docs presence requires GITHUB_TOKEN and was not measured for this candidate — neutral placeholder at low confidence.",
            suggestions=["Configure GITHUB_TOKEN to unlock documentation-ratio analysis."],
        )
    return DimensionScore(
        key="documentation", label="Documentation", score=to_100(gh.documented_repo_ratio), confidence=0.65,
        evidence=[Evidence(source=EvidenceSource.github, detail=f"{gh.documented_repo_ratio:.0%} of sampled repos include a README or docs folder.", metric=gh.documented_repo_ratio)],
        reasoning="Fraction of sampled repositories with a detected README or docs directory.",
        suggestions=[] if gh.documented_repo_ratio >= 0.5 else ["Add a README describing purpose, setup, and usage to your key repositories."],
    )


def score_testing(ev: CandidateEvidence) -> DimensionScore:
    gh = ev.github
    if not gh or not gh.repos:
        return DimensionScore(key="testing", label="Testing", score=0.0, confidence=0.15, reasoning="No repositories available to assess.")
    if not gh.structural_analysis_available:
        return DimensionScore(
            key="testing", label="Testing", score=45.0, confidence=0.2,
            reasoning="Test-suite presence requires GITHUB_TOKEN and was not measured for this candidate — neutral placeholder at low confidence.",
            suggestions=["Configure GITHUB_TOKEN to unlock test-suite detection."],
        )
    return DimensionScore(
        key="testing", label="Testing", score=to_100(gh.tested_repo_ratio), confidence=0.65,
        evidence=[Evidence(source=EvidenceSource.github, detail=f"{gh.tested_repo_ratio:.0%} of sampled repos contain a test directory or spec files.", metric=gh.tested_repo_ratio)],
        reasoning="Fraction of sampled repositories with detected test files or directories.",
        suggestions=[] if gh.tested_repo_ratio >= 0.4 else ["Add a test suite (pytest/jest/etc.) to your primary repository."],
    )


def score_open_source(ev: CandidateEvidence) -> DimensionScore:
    gh = ev.github
    if not gh:
        return DimensionScore(key="open_source", label="Open Source", score=0.0, confidence=0.15, reasoning="No GitHub evidence available.")
    score01 = gh.oss_signal
    # Stars/followers/forks are an asymmetric signal: accumulating them is a
    # meaningful, hard-to-fake indicator of impact, but *not* accumulating them
    # says little — most excellent engineers work on private repos and never
    # chase public visibility. So confidence scales with the score itself:
    # a high score is confidently real signal; a low score is only weak
    # evidence of low impact, and must not drag the overall average as if it
    # were a confidently-measured weakness.
    confidence = round(min(0.75, 0.2 + 0.55 * score01), 2)
    return DimensionScore(
        key="open_source", label="Open Source", score=to_100(score01), confidence=confidence,
        evidence=[
            Evidence(source=EvidenceSource.github, detail=f"{gh.total_stars} stars, {gh.total_forks} forks received across repositories.", metric=float(gh.total_stars)),
            Evidence(source=EvidenceSource.github, detail=f"{gh.followers} followers; member of {len(gh.contributed_orgs)} organization(s).", metric=float(gh.followers)),
        ],
        reasoning="Combines followers, stars, forks, and organization membership as external validation of open-source impact.",
        suggestions=[] if score01 >= 0.4 else ["Contribute to an existing open-source project to build external validation signal."],
    )


def score_collaboration(ev: CandidateEvidence, skills: List[VerifiedSkill]) -> DimensionScore:
    gh = ev.github
    resume_text = (ev.resume.raw_text if ev.resume else "") or ""
    keyword_hit = sum(1 for k in ("collaborat", "cross-functional", "stakeholder", "pair programming", "code review") if k in resume_text.lower())
    forks_component = log_norm(gh.total_forks, 100) if gh else 0.0
    orgs_component = min(1.0, len(gh.contributed_orgs) / 3.0) if gh else 0.0
    keyword_component = min(1.0, keyword_hit / 3.0)
    score01 = 0.4 * forks_component + 0.3 * orgs_component + 0.3 * keyword_component
    evidence = []
    if gh:
        evidence.append(Evidence(source=EvidenceSource.github, detail=f"{gh.total_forks} forks received; member of {len(gh.contributed_orgs)} org(s).", metric=float(gh.total_forks)))
    if keyword_hit:
        evidence.append(Evidence(source=EvidenceSource.resume, detail="Resume language emphasizes cross-functional collaboration."))
    # Low confidence floor when nothing was observed (no forks, no orgs, no
    # resume language) — absence of these specific signals is weak evidence of
    # poor collaboration, not confident proof of it. Confidence rises with
    # whichever signals actually fired.
    confidence = round(min(0.85, 0.15 + 0.25 * forks_component + 0.25 * orgs_component + 0.2 * keyword_component), 2)
    return DimensionScore(
        key="collaboration", label="Collaboration", score=to_100(score01), confidence=confidence,
        evidence=evidence,
        reasoning="Forks received (proxy for others building on your work), organization membership, and resume language about cross-functional work.",
        suggestions=[] if score01 >= 0.4 else ["Contribute to a team or org-owned repository to evidence collaboration beyond solo projects."],
    )


def score_ownership(ev: CandidateEvidence) -> DimensionScore:
    resume = ev.resume
    experience = (resume.experience if resume else []) or []
    long_tenure = sum(1 for e in experience if (e.duration_months or 0) >= 12)
    text = (resume.raw_text if resume else "") or ""
    keyword_hit = sum(1 for k in ("led ", "owned", "spearheaded", "drove", "initiated", "founded") if k in text.lower())
    gh = ev.github
    maintainer_signal = 1.0 if gh and gh.original_repo_count >= 5 and gh.followers >= 5 else (0.5 if gh and gh.original_repo_count >= 2 else 0.0)
    score01 = 0.35 * min(1.0, long_tenure / 2.0) + 0.35 * min(1.0, keyword_hit / 3.0) + 0.3 * maintainer_signal
    evidence = []
    if long_tenure:
        evidence.append(Evidence(source=EvidenceSource.resume, detail=f"{long_tenure} role(s) with 12+ months tenure."))
    if keyword_hit:
        evidence.append(Evidence(source=EvidenceSource.resume, detail="Resume uses ownership language (led/owned/spearheaded)."))
    if gh:
        evidence.append(Evidence(source=EvidenceSource.github, detail=f"Maintains {gh.original_repo_count} original repositor(y/ies)."))
    # Same asymmetric principle as Collaboration/Open Source: no resume text
    # and no maintainer signal means we simply haven't observed anything, not
    # that ownership is confidently low.
    confidence = round(
        min(0.85, 0.15 + 0.2 * min(long_tenure / 2.0, 1.0) + 0.15 * min(keyword_hit / 3.0, 1.0) + 0.35 * maintainer_signal),
        2,
    )
    return DimensionScore(
        key="ownership", label="Ownership", score=to_100(score01), confidence=confidence,
        evidence=evidence,
        reasoning="Combines tenure length, ownership language in resume descriptions, and maintainer behaviour on original repositories.",
        suggestions=[] if score01 >= 0.4 else ["Describe specific outcomes you drove end-to-end in your resume experience section."],
    )


def score_learning_velocity(ev: CandidateEvidence, skills: List[VerifiedSkill]) -> DimensionScore:
    gh = ev.github
    distinct_skills = len(skills)
    account_years = max(gh.account_age_years, 0.3) if gh else 1.0
    skills_per_year = distinct_skills / account_years
    breadth_component = min(1.0, skills_per_year / 4.0)
    rec_component = recency_score(gh.most_recent_push_days) if gh else 0.0
    resume_years = ev.resume.total_experience_years if ev.resume else None
    yoe_component = min(1.0, (resume_years or 2.0) / 8.0)
    score01 = 0.5 * breadth_component + 0.3 * rec_component + 0.2 * yoe_component
    return DimensionScore(
        key="learning_velocity", label="Learning Velocity", score=to_100(score01), confidence=round(min(1.0, 0.3 + 0.4 * breadth_component + 0.2 * rec_component), 2),
        evidence=[Evidence(source=EvidenceSource.derived, detail=f"{distinct_skills} distinct skill(s) evidenced across {account_years:.1f} year(s) of GitHub history.", metric=skills_per_year)],
        reasoning="Rate of distinct skills acquired per year of observable history, weighted by recent activity.",
        suggestions=[] if score01 >= 0.4 else ["Explore an adjacent technology in a new project to demonstrate continued learning."],
    )


def score_consistency(ev: CandidateEvidence) -> DimensionScore:
    gh = ev.github
    if not gh or gh.public_repos == 0:
        return DimensionScore(key="consistency", label="Consistency", score=0.0, confidence=0.15, reasoning="No repository activity available to assess.")
    active_ratio = min(1.0, gh.active_repos_last_year / max(1, gh.original_repo_count))
    rec = recency_score(gh.most_recent_push_days)
    score01 = 0.6 * active_ratio + 0.4 * rec
    return DimensionScore(
        key="consistency", label="Consistency", score=to_100(score01), confidence=0.6,
        evidence=[Evidence(source=EvidenceSource.github, detail=f"{gh.active_repos_last_year} of {gh.original_repo_count} original repos pushed to within the last year.", metric=active_ratio)],
        reasoning="Share of original repositories with activity in the last year, weighted by recency of the most recent push.",
        suggestions=[] if score01 >= 0.4 else ["Maintain a regular commit cadence on at least one active project."],
    )


def score_project_complexity(ev: CandidateEvidence) -> DimensionScore:
    gh = ev.github
    if not gh or not gh.repos:
        return DimensionScore(key="project_complexity", label="Project Complexity", score=0.0, confidence=0.15, reasoning="No repositories available to assess.")
    top = sorted(gh.repos, key=lambda r: r.complexity, reverse=True)[:5]
    avg = sum(r.complexity for r in top) / len(top)
    return DimensionScore(
        key="project_complexity", label="Project Complexity", score=to_100(avg), confidence=0.6,
        evidence=[Evidence(source=EvidenceSource.github, detail=f"{r.name}: complexity {r.complexity:.2f} ({len(r.languages_bytes)} language(s), {r.size_kb}KB).", metric=r.complexity) for r in top[:3]],
        reasoning="Average structural complexity (size, language diversity, CI/tests/docs rigor, external validation) across your most complex repositories.",
        suggestions=[] if avg >= 0.4 else ["Take on a project that spans multiple services or languages to demonstrate handling complexity."],
    )


def score_all_dimensions(ev: CandidateEvidence, skills: List[VerifiedSkill]) -> List[DimensionScore]:
    return [
        score_programming(skills),
        score_problem_solving(ev),
        _category_dimension("backend", "Backend", skills, "backend"),
        _category_dimension("frontend", "Frontend", skills, "frontend"),
        _category_dimension("ai_ml", "AI/ML", skills, "ai/ml"),
        _category_dimension("cloud", "Cloud", skills, "cloud"),
        _category_dimension("devops", "DevOps", skills, "devops"),
        score_system_design(ev, skills),
        score_code_quality(ev),
        score_documentation(ev),
        score_testing(ev),
        score_open_source(ev),
        score_collaboration(ev, skills),
        score_ownership(ev),
        score_learning_velocity(ev, skills),
        score_consistency(ev),
        score_project_complexity(ev),
    ]
