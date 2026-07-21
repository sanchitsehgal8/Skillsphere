"""Modular, explainable, evidence-based scoring engine."""

from app.scoring.engine import build_scorecard, match_candidate
from app.scoring.job import parse_job

__all__ = ["build_scorecard", "match_candidate", "parse_job"]
