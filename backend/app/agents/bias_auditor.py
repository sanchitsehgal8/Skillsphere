from typing import List

from app.models import BiasFlag, AuditLogEntry, CandidateProfile, MatchScore


class BiasAuditorAgent:
    """Performs a lightweight fairness pass over ranked candidates.

    We simulate a bias audit by checking for underrepresented demographics
    and ensuring they are not systematically pushed to the bottom.
    """

    def audit(
        self,
        job_id: str,
        ranked_scores: List[MatchScore],
        candidates_by_id: dict,
    ) -> List[AuditLogEntry]:
        logs: List[AuditLogEntry] = []

        # Identify protected candidates (very naive heuristic for demo only)
        protected_ids = set()
        for c_id, cand in candidates_by_id.items():  # type: ignore[arg-type]
            if not isinstance(cand, CandidateProfile):
                continue
            gender = (cand.demographics.get("gender") or "").lower()
            if gender in {"female", "non-binary"}:
                protected_ids.add(c_id)

        for rank, score in enumerate(ranked_scores, start=1):
            flags: List[BiasFlag] = []
            if score.candidate_id in protected_ids and rank > len(ranked_scores) // 2:
                flags.append(
                    BiasFlag(
                        candidate_id=score.candidate_id,
                        reason="Protected demographic appears in lower half of ranking.",
                        severity="medium",
                    )
                )

            logs.append(
                AuditLogEntry(
                    job_id=job_id,
                    candidate_id=score.candidate_id,
                    original_rank=rank,
                    adjusted_rank=rank,  # no automatic re-ranking yet
                    bias_flags=flags,
                )
            )

        return logs
