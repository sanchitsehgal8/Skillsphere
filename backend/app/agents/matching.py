from typing import List, Tuple

import math

from app.models import JobDescription, SkillGraph, MatchScore
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

                # Time-to-productivity estimate for this requirement
                # Shorter if direct skill is strong, longer if only adjacent
                # skills exist; scaled by learning velocity.
                lv = max(0.0, min(1.0, graph.learning_velocity))
                if best_direct_score >= 0.75:
                    days = 7.0
                    direct_matches.append(req.name)
                elif best_direct_score >= 0.4:
                    days = 21.0
                    direct_matches.append(req.name)
                elif best_adj_score > 0.0 and best_adj_distance is not None:
                    base_days = {1: 45.0, 2: 75.0, 3: 110.0}.get(best_adj_distance, 120.0)
                    days = base_days * (1.0 - 0.4 * lv)
                    if best_adj_desc:
                        adjacent_support.append(best_adj_desc)
                else:
                    # No direct or adjacent coverage; assume long ramp-up.
                    days = 150.0 * (1.0 - 0.3 * lv)

                ttp_numer += days * max(weight, 0.1)
                ttp_denom += max(weight, 0.1)

            time_to_productivity = ttp_numer / ttp_denom if ttp_denom > 0 else None

            # Incorporate present fit, learning velocity, and TTP into a single score.
            if time_to_productivity is not None:
                # Map days to [0,1] where faster ramp-up => higher potential.
                ttp_clamped = max(0.0, min(180.0, time_to_productivity))
                ttp_score = 1.0 - (ttp_clamped / 180.0)
            else:
                ttp_score = 0.5

            score = max(
                0.0,
                min(
                    1.0,
                    0.4 * base_sim + 0.3 * graph.learning_velocity + 0.3 * ttp_score,
                ),
            )

            explanation_parts = [
                f"Cosine alignment (current skills vs requirements): {base_sim:.2f}.",
                f"Learning velocity: {graph.learning_velocity:.2f}.",
            ]
            if time_to_productivity is not None:
                explanation_parts.append(
                    f"Estimated time-to-productivity: {time_to_productivity:.1f} days "
                    "across core requirements (lower is better).",
                )
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
                    time_to_productivity_days=time_to_productivity,
                    direct_matches=direct_matches,
                    adjacent_support=adjacent_support,
                )
            )

        scores.sort(key=lambda s: s.score, reverse=True)
        return scores
