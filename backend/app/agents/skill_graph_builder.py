from typing import List

from app.models import SkillGraph, SkillNode
from app.agents.talent_scout import TalentSignals


class SkillGraphBuilderAgent:
    """Builds a candidate's Skill DNA and computes learning velocity.

    This is a deterministic heuristic model that infers skills from the
    talent signals. In a production setup, you would plug in a GNN/LLM.
    """

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
            skills.append(SkillNode(name=name, score=max(0.0, min(1.0, score)), evidence=[evidence]))

        # Very rough inference based on keywords
        if "github" in text or "repo" in text:
            add_skill("software engineering", 0.8, "Active repositories and code contributions.")
        if "kaggle" in text:
            add_skill("machine learning", 0.75, "Kaggle projects indicate ML familiarity.")
        if "competitive" in text or "rating" in text:
            add_skill("algorithmic thinking", 0.8, "Competitive programming history.")
        if "portfolio" in text:
            add_skill("system design", 0.7, "Portfolio projects spread across domains.")

        if not skills:
            add_skill("general problem solving", 0.6, "Limited public signal; inferred from profile.")

        # Learning velocity heuristic: more diverse signals => higher velocity
        diversity = len({s.name for s in skills})
        base_velocity = 0.4 + 0.1 * min(diversity, 4)

        # If candidate has competitive programming signals, boost learning velocity
        if any("algorithmic" in s.name for s in skills):
            base_velocity += 0.1

        learning_velocity = max(0.0, min(1.0, base_velocity))

        return SkillGraph(candidate_id=signals.candidate.id, skills=skills, learning_velocity=learning_velocity)
