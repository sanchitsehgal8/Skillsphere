from typing import List, Tuple

import math

from app.models import JobDescription, SkillGraph, MatchScore, XAIComponent, XAIExplanation
from app.services.skill_adjacency import GLOBAL_SKILL_GRAPH


class MatchingAndRankingAgent:
    """Matches candidates to jobs via semantic-ish cosine similarity.

    For simplicity we use bag-of-words over skills and job requirements
    instead of a full embedding+FAISS pipeline. The interface is designed
    so you can later swap in a vector DB.
    """

    def _vectorize(self, job: JobDescription, graph: SkillGraph) -> Tuple[dict, dict]:
        job_vec = {}
        for req in job.requirements:
            job_vec[req.name.lower()] = req.weight

        cand_vec = {}
        for node in graph.skills:
            cand_vec[node.name.lower()] = node.score

        return job_vec, cand_vec

    def _cosine(self, a: dict, b: dict) -> float:
        keys = set(a.keys()) | set(b.keys())
        num = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
        den_a = math.sqrt(sum(v * v for v in a.values()))
        den_b = math.sqrt(sum(v * v for v in b.values()))
        if den_a == 0 or den_b == 0:
            return 0.0
        return num / (den_a * den_b)

    def rank_candidates(self, job: JobDescription, graphs: List[SkillGraph]) -> List[MatchScore]:
        scores: List[MatchScore] = []
        for graph in graphs:
            jv, cv = self._vectorize(job, graph)
            base_sim = self._cosine(jv, cv)
            # Evaluate direct and adjacency-based coverage per requirement.
            direct_matches: list[str] = []
            adjacent_support: list[str] = []
            ttp_numer = 0.0
            ttp_denom = 0.0

            for req in job.requirements:
                req_name = req.name.lower()
                weight = req.weight or 0.0

                # Find best direct skill and best adjacent skill.
                best_direct_score = 0.0
                best_direct_name: str | None = None
                best_adj_score = 0.0
                best_adj_desc: str | None = None
                best_adj_distance: int | None = None

                for node in graph.skills:
                    s_name = node.name.lower()
                    s_score = node.score
                    if s_name == req_name:
                        if s_score > best_direct_score:
                            best_direct_score = s_score
                            best_direct_name = node.name
                    else:
                        dist = GLOBAL_SKILL_GRAPH.shortest_distance(s_name, req_name, max_depth=3)
                        if dist is None:
                            continue
                        # Closer and stronger skills contribute more.
                        potential = s_score * (0.8 ** dist)
                        if potential > best_adj_score:
                            best_adj_score = potential
                            best_adj_distance = dist
                            best_adj_desc = f"{node.name} -> {req.name} (distance {dist})"

                # Time-to-productivity estimate (in pomodoros) for this requirement.
                # 1 pomodoro = 25 minutes of focused work.
                # Lower means the candidate can ship role-level output faster.
                lv = max(0.0, min(1.0, graph.learning_velocity))
                if best_direct_score >= 0.75:
                    pomodoros = 4.0
                    direct_matches.append(req.name)
                elif best_direct_score >= 0.4:
                    pomodoros = 10.0
                    direct_matches.append(req.name)
                elif best_adj_score > 0.0 and best_adj_distance is not None:
                    base_pomodoros = {1: 18.0, 2: 30.0, 3: 46.0}.get(best_adj_distance, 54.0)
                    pomodoros = base_pomodoros * (1.0 - 0.45 * lv)
                    if best_adj_desc:
                        adjacent_support.append(best_adj_desc)
                else:
                    # No direct or adjacent coverage; assume longer ramp-up.
                    pomodoros = 64.0 * (1.0 - 0.35 * lv)

                ttp_numer += pomodoros * max(weight, 0.1)
                ttp_denom += max(weight, 0.1)

            ttp_pomodoros = ttp_numer / ttp_denom if ttp_denom > 0 else None
            ttp_hours = (ttp_pomodoros * 25.0 / 60.0) if ttp_pomodoros is not None else None
            # 1 sprint = 2 weeks = ~80 focused work hours baseline.
            ttp_sprints = (ttp_hours / 80.0) if ttp_hours is not None else None

            # Incorporate present fit, learning velocity, and TTP into a single score.
            if ttp_pomodoros is not None:
                # Map effort to [0,1] where faster ramp-up => higher potential.
                ttp_clamped = max(0.0, min(80.0, ttp_pomodoros))
                ttp_score = 1.0 - (ttp_clamped / 80.0)
            else:
                ttp_score = 0.5

            score = max(
                0.0,
                min(
                    1.0,
                    0.4 * base_sim + 0.3 * graph.learning_velocity + 0.3 * ttp_score,
                ),
            )

            fit_component = 0.4 * base_sim
            velocity_component = 0.3 * graph.learning_velocity
            readiness_component = 0.3 * ttp_score

            components = [
                XAIComponent(
                    name="Present Skill Fit",
                    metric_value=base_sim,
                    weight=0.4,
                    contribution=fit_component,
                    reason="Cosine similarity between candidate skills and role requirements.",
                ),
                XAIComponent(
                    name="Learning Velocity",
                    metric_value=graph.learning_velocity,
                    weight=0.3,
                    contribution=velocity_component,
                    reason="Estimated ability to ramp quickly on unfamiliar tools.",
                ),
                XAIComponent(
                    name="Productivity Readiness",
                    metric_value=ttp_score,
                    weight=0.3,
                    contribution=readiness_component,
                    reason="Inverse of time-to-productivity estimate (lower TTP => higher readiness).",
                ),
            ]

            direct_set = sorted(set(direct_matches))
            missing_requirements = [
                req.name for req in job.requirements if req.name not in direct_set
            ]
            coverage_ratio = len(direct_set) / max(1, len(job.requirements))
            adjacency_evidence = min(0.25, 0.04 * len(adjacent_support))
            confidence = max(
                0.0,
                min(1.0, 0.45 + 0.35 * coverage_ratio + 0.2 * base_sim + adjacency_evidence),
            )

            if score >= 0.8:
                summary_label = "Strong match"
            elif score >= 0.65:
                summary_label = "Promising match"
            else:
                summary_label = "Developing match"

            strengths: list[str] = []
            if direct_set:
                strengths.append("Direct requirement matches: " + ", ".join(direct_set[:4]))
            if graph.learning_velocity >= 0.65:
                strengths.append("High learning velocity supports faster onboarding.")
            if ttp_pomodoros is not None:
                strengths.append(f"Estimated readiness in ~{ttp_pomodoros:.1f} pomodoros.")

            gaps: list[str] = []
            if missing_requirements:
                gaps.append("Missing direct coverage: " + ", ".join(missing_requirements[:4]))
            if not adjacent_support:
                gaps.append("No strong adjacent skill transfer paths were found.")

            recommendations: list[str] = []
            if missing_requirements:
                recommendations.append(
                    "Prioritize a targeted onboarding plan for: " + ", ".join(missing_requirements[:3]),
                )
            if adjacent_support:
                recommendations.append(
                    "Leverage adjacent strengths: " + "; ".join(adjacent_support[:2]),
                )
            if not recommendations:
                recommendations.append("Candidate can start with core role tasks immediately.")

            xai = XAIExplanation(
                summary=(
                    f"{summary_label}: score {score:.2f} from weighted metrics "
                    f"(fit {base_sim:.2f}, velocity {graph.learning_velocity:.2f}, readiness {ttp_score:.2f})."
                ),
                confidence=confidence,
                score_components=components,
                strengths=strengths,
                gaps=gaps,
                recommendations=recommendations,
            )

            explanation_parts = [
                f"Weighted score {score:.2f} = 0.4*fit({base_sim:.2f}) + "
                f"0.3*velocity({graph.learning_velocity:.2f}) + 0.3*readiness({ttp_score:.2f}).",
            ]
            if ttp_pomodoros is not None and ttp_hours is not None and ttp_sprints is not None:
                ttp_explanation = (
                    f"Estimated effort: {ttp_pomodoros:.1f} pomodoros (~{ttp_hours:.1f} hours, "
                    f"~{ttp_sprints:.2f} sprints)."
                )
                explanation_parts.append(
                    ttp_explanation,
                )
            else:
                ttp_explanation = None
            if direct_matches:
                explanation_parts.append(
                    "Directly satisfied requirements: " + ", ".join(sorted(set(direct_matches))) + ".",
                )
            if adjacent_support:
                explanation_parts.append(
                    "Adjacency-based potential (skills that transfer quickly): "
                    + "; ".join(adjacent_support)
                    + ".",
                )

            explanation = " ".join(explanation_parts)

            scores.append(
                MatchScore(
                    job_id=job.id,
                    candidate_id=graph.candidate_id,
                    score=score,
                    explanation=explanation,
                    time_to_productivity_pomodoros=ttp_pomodoros,
                    time_to_productivity_hours=ttp_hours,
                    time_to_productivity_sprints=ttp_sprints,
                    time_to_productivity_explanation=ttp_explanation,
                    direct_matches=direct_matches,
                    adjacent_support=adjacent_support,
                    xai=xai,
                )
            )

        scores.sort(key=lambda s: s.score, reverse=True)
        return scores
