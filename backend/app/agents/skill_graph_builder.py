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

        if not skills:
            add_skill(
                "general problem solving",
                0.6,
                "Limited public signal; inferred from profile.",
            )

        # Learning velocity heuristic: more diverse signals => higher velocity
        diversity = len({s.name for s in skills})
        base_velocity = 0.4 + 0.1 * min(diversity, 4)

        # Increase learning velocity for higher GitHub activity levels.
        import math

        base_velocity += 0.08 * (math.log1p(max(signals.total_repos, 0)) / 5.0)
        base_velocity += 0.07 * (math.log1p(max(signals.total_stars, 0)) / 8.0)

        # If candidate has competitive programming signals, boost learning velocity
        if any("algorithmic" in s.name for s in skills):
            base_velocity += 0.1

        learning_velocity = max(0.0, min(1.0, base_velocity))

        return SkillGraph(candidate_id=signals.candidate.id, skills=skills, learning_velocity=learning_velocity)
