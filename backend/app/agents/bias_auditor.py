from typing import Any, Dict, List, Optional

from app.models import BiasFlag, AuditLogEntry, CandidateProfile, MatchScore


class TransformerBiasDetector:
    """Transformer-backed bias detector using zero-shot classification.

    - Primary model: facebook/bart-large-mnli
    - If transformers/runtime is unavailable, detector degrades gracefully.
    """

    def __init__(self, model_name: str = "facebook/bart-large-mnli") -> None:
        self.model_name = model_name
        self._classifier = None
        self._is_ready = False
        self._init_error: Optional[str] = None
        self._init_pipeline()

    def _init_pipeline(self) -> None:
        try:
            from transformers import pipeline  # type: ignore

            self._classifier = pipeline("zero-shot-classification", model=self.model_name)
            self._is_ready = True
        except Exception as exc:  # noqa: BLE001
            self._is_ready = False
            self._init_error = str(exc)

    @property
    def is_ready(self) -> bool:
        return self._is_ready and self._classifier is not None

    def analyze(self, text: str) -> Dict[str, Any]:
        """Return transformer-based risk scores for bias in a rationale text."""
        if not self.is_ready:
            return {
                "available": False,
                "bias_probability": None,
                "neutral_probability": None,
                "init_error": self._init_error,
            }

        labels = [
            "demographic-biased hiring rationale",
            "stereotyping or discriminatory hiring language",
            "neutral skill-based hiring rationale",
        ]

        try:
            result = self._classifier(text, candidate_labels=labels, multi_label=True)
            label_to_score = dict(zip(result["labels"], result["scores"]))
            demographic_bias = float(label_to_score.get(labels[0], 0.0))
            stereotyping = float(label_to_score.get(labels[1], 0.0))
            neutral = float(label_to_score.get(labels[2], 0.0))
            bias_prob = max(demographic_bias, stereotyping)
            return {
                "available": True,
                "bias_probability": bias_prob,
                "neutral_probability": neutral,
                "demographic_bias_probability": demographic_bias,
                "stereotyping_probability": stereotyping,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "available": False,
                "bias_probability": None,
                "neutral_probability": None,
                "init_error": str(exc),
            }


_GLOBAL_TRANSFORMER_BIAS_DETECTOR = TransformerBiasDetector()


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

        # Group-level disparity check (score gap between protected/non-protected groups)
        protected_scores = [s.score for s in ranked_scores if s.candidate_id in protected_ids]
        non_protected_scores = [s.score for s in ranked_scores if s.candidate_id not in protected_ids]

        protected_mean = sum(protected_scores) / len(protected_scores) if protected_scores else None
        non_protected_mean = (
            sum(non_protected_scores) / len(non_protected_scores) if non_protected_scores else None
        )
        disparity_gap = None
        if protected_mean is not None and non_protected_mean is not None:
            disparity_gap = non_protected_mean - protected_mean

        for rank, score in enumerate(ranked_scores, start=1):
            flags: List[BiasFlag] = []

            # Transformer-based candidate-level rationale analysis
            rationale_text = (
                f"Candidate {score.candidate_id}. "
                f"Ranking explanation: {score.explanation}. "
            )
            ai_result = _GLOBAL_TRANSFORMER_BIAS_DETECTOR.analyze(rationale_text)
            ai_bias_probability = ai_result.get("bias_probability")

            if ai_result.get("available") and isinstance(ai_bias_probability, float):
                if ai_bias_probability >= 0.65:
                    flags.append(
                        BiasFlag(
                            candidate_id=score.candidate_id,
                            reason=(
                                "Transformer audit detected potentially demographic or stereotyping bias "
                                f"in rationale text (risk={ai_bias_probability:.2f})."
                            ),
                            severity="high",
                        )
                    )
                elif ai_bias_probability >= 0.45:
                    flags.append(
                        BiasFlag(
                            candidate_id=score.candidate_id,
                            reason=(
                                "Transformer audit detected moderate bias risk in rationale text "
                                f"(risk={ai_bias_probability:.2f})."
                            ),
                            severity="medium",
                        )
                    )

            if score.candidate_id in protected_ids and rank > len(ranked_scores) // 2:
                flags.append(
                    BiasFlag(
                        candidate_id=score.candidate_id,
                        reason="Protected demographic appears in lower half of ranking.",
                        severity="medium",
                    )
                )

            if (
                disparity_gap is not None
                and disparity_gap > 0.10
                and score.candidate_id in protected_ids
            ):
                flags.append(
                    BiasFlag(
                        candidate_id=score.candidate_id,
                        reason=(
                            "Group-level disparity detected: protected group average score is "
                            f"{disparity_gap:.2f} lower than non-protected group."
                        ),
                        severity="high" if disparity_gap > 0.18 else "medium",
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
