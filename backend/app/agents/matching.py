from typing import List, Tuple

import math

from app.models import JobDescription, SkillGraph, MatchScore


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
            # incorporate learning velocity as a modest boost
            score = max(0.0, min(1.0, base_sim * 0.7 + graph.learning_velocity * 0.3))

            explanation = (
                f"Cosine alignment between role requirements and skills: {base_sim:.2f}. "
                f"Learning velocity: {graph.learning_velocity:.2f}. "
                "Composite score balances present fit and growth potential."
            )

            scores.append(
                MatchScore(
                    job_id=job.id,
                    candidate_id=graph.candidate_id,
                    score=score,
                    explanation=explanation,
                )
            )

        scores.sort(key=lambda s: s.score, reverse=True)
        return scores
