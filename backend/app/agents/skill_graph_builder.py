from typing import List

from app.models import SkillGraph, SkillNode
from app.agents.talent_scout import TalentSignals


class SkillGraphBuilderAgent:

    def build_skill_graph(self, signals: TalentSignals) -> SkillGraph:
        text = (
            (signals.activity_summary or "")
            + " "
            + " ".join(signals.repositories)
            + " "
            + (signals.problem_solving_summary or "")
        ).lower()

        skills: List[SkillNode] = []

        def add_skill(name: str, score: float, evidence: str) -> None:
            skills.append(
                SkillNode(name=name, score=max(0.0, min(1.0, score)), evidence=[evidence])
            )

        # Very rough inference based on keywords
        if "github" in text or "repo" in text:
            add_skill("software engineering", 0.8, "Active repositories and code contributions.")
        if "kaggle" in text:
            add_skill("machine learning", 0.75, "Kaggle projects indicate ML familiarity.")
        if "competitive" in text or "rating" in text:
            add_skill("algorithmic thinking", 0.8, "Competitive programming history.")
        if "portfolio" in text:
            add_skill("system design", 0.7, "Portfolio projects spread across domains.")

        # Add language-specific skills based on the structured language profile.
        # This is what makes different GitHub stacks produce different vectors.
        if signals.language_profile:
            max_count = max(signals.language_profile.values()) or 1

            # Normalise overall activity so very active profiles stand out.
            total_repos = max(signals.total_repos, 0)
            total_stars = max(signals.total_stars, 0)

            # Lightly saturate with log to avoid huge extremes.
            import math

            repo_factor = math.log1p(total_repos) / 5.0  # ~0-1 for 0-150+ repos
            star_factor = math.log1p(total_stars) / 8.0  # ~0-1 for 0-3k+ stars

            for lang, count in signals.language_profile.items():
                usage_ratio = count / max_count
                base = 0.45 + 0.35 * usage_ratio
                activity_boost = 0.1 * repo_factor + 0.1 * star_factor
                score = base + activity_boost
                add_skill(
                    lang.lower(),
                    score,
                    f"Language {lang} appears in {count} GitHub repositories ("
                    f"{total_repos} total repos, {total_stars} total stars).",
                )

        # Resume adds structured signals beyond public repositories.
        resume_skill_set = {s.lower() for s in (signals.resume_skills or [])}
        for resume_skill in sorted(resume_skill_set):
            # Resume-only skill claims start with moderate confidence.
            # If the same skill appears in GitHub signals, confidence is higher.
            existing = next((s for s in skills if s.name.lower() == resume_skill), None)
            if existing:
                existing.score = max(existing.score, min(1.0, existing.score + 0.1))
                existing.evidence.append("Also validated by resume evidence.")
                continue

            base_resume_score = 0.62
            if resume_skill in {"python", "fastapi", "react", "typescript", "javascript"}:
                base_resume_score = 0.68

            add_skill(
                resume_skill,
                base_resume_score,
                "Inferred from uploaded resume.",
            )

        if not skills:
            add_skill(
                "general problem solving",
                0.6,
                "Limited public signal; inferred from profile.",
            )

        # Learning velocity calibration:
        # - deterministic for the same inputs
        # - avoids extreme jumps when optional resume data is missing
        # - remains bounded to realistic range for UI and ranking stability
        diversity = len({s.name for s in skills})

        import math

        diversity_norm = min(diversity, 8) / 8.0
        repo_norm = min(1.0, math.log1p(max(signals.total_repos, 0)) / math.log1p(120))
        star_norm = min(1.0, math.log1p(max(signals.total_stars, 0)) / math.log1p(2000))

        if signals.years_experience is None:
            # Missing resume should not be treated as zero experience.
            # Use neutral prior to prevent instability between runs with/without resume.
            yoe_norm = 0.55
        else:
            yoe_norm = min(max(signals.years_experience, 0.0), 12.0) / 12.0

        if signals.resume_text or (signals.resume_skills and len(signals.resume_skills) > 0):
            resume_norm = min(len(signals.resume_skills or []), 12) / 12.0
        else:
            # Neutral prior when resume is absent (unknown != weak).
            resume_norm = 0.55

        # Portfolio signal combines breadth of work and quality signal.
        portfolio_norm = 0.6 * repo_norm + 0.4 * star_norm
        cp_signal = 1.0 if any("algorithmic" in s.name for s in skills) else 0.5

        learning_velocity = (
            0.18
            + 0.26 * diversity_norm
            + 0.24 * portfolio_norm
            + 0.18 * yoe_norm
            + 0.12 * resume_norm
            + 0.08 * cp_signal
        )

        # Keep a realistic bounded range and avoid hard 100% saturation.
        learning_velocity = max(0.35, min(0.95, learning_velocity))

        return SkillGraph(candidate_id=signals.candidate.id, skills=skills, learning_velocity=learning_velocity)
