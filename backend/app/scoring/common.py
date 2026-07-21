"""Shared normalizers, taxonomy, and evidence helpers for the scoring engine.

The scoring engine is deliberately deterministic and reproducible: the same
evidence always yields the same scores. Every coefficient below is a documented
*evidence weight* — a statement about how strongly a signal evidences ability —
not an arbitrary preference knob. They are collected here so they can be
inspected, tuned, and explained in one place.
"""

from __future__ import annotations

import math
from typing import Dict, List

# --------------------------------------------------------------------------- #
# Normalizers — all return 0..1
# --------------------------------------------------------------------------- #
def log_norm(value: float, ceiling: float) -> float:
    """Log-scaled 0..1 where ``value == ceiling`` maps to ~1.0.

    Log scaling reflects diminishing returns: the difference between 10 and 100
    repos matters more than between 1000 and 1090.
    """
    if value <= 0 or ceiling <= 0:
        return 0.0
    return min(1.0, math.log1p(value) / math.log1p(ceiling))


def linear_norm(value: float, ceiling: float) -> float:
    if ceiling <= 0:
        return 0.0
    return max(0.0, min(1.0, value / ceiling))


def recency_score(days: int | None, half_life_days: float = 365.0) -> float:
    """1.0 for activity today, decaying to ~0.5 at ``half_life_days``."""
    if days is None:
        return 0.0
    return max(0.0, math.exp(-math.log(2) * days / half_life_days))


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def to_100(x01: float) -> float:
    return round(100.0 * clamp01(x01), 1)


# --------------------------------------------------------------------------- #
# Skill taxonomy — canonical skill -> category, and language ownership of
# frameworks so a framework's evidence attaches to its language.
# --------------------------------------------------------------------------- #
SKILL_CATEGORY = {
    # languages
    "python": "language", "java": "language", "c++": "language", "c": "language",
    "go": "language", "rust": "language", "javascript": "language",
    "typescript": "language", "kotlin": "language", "swift": "language",
    "ruby": "language", "php": "language", "scala": "language", "r": "language",
    # backend
    "fastapi": "backend", "django": "backend", "flask": "backend",
    "express": "backend", "spring": "backend", "rails": "backend",
    "node.js": "backend", "graphql": "backend",
    # frontend
    "react": "frontend", "next.js": "frontend", "vue": "frontend",
    "nuxt": "frontend", "angular": "frontend", "svelte": "frontend",
    "css": "frontend", "html": "frontend", "tailwind": "frontend",
    # ai/ml
    "machine learning": "ai/ml", "llm": "ai/ml", "pytorch": "ai/ml",
    "tensorflow": "ai/ml", "keras": "ai/ml", "scikit-learn": "ai/ml",
    "langchain": "ai/ml", "pandas": "ai/ml", "numpy": "ai/ml",
    # cloud / devops
    "aws": "cloud", "gcp": "cloud", "azure": "cloud",
    "docker": "devops", "kubernetes": "devops", "terraform": "devops",
    "ci/cd": "devops",
    # data
    "sql": "data", "nosql": "data", "data engineering": "data",
    "spark": "data", "kafka": "data", "airflow": "data",
    # cs fundamentals / soft
    "system design": "architecture", "distributed systems": "architecture",
    "algorithms": "problem-solving", "data structures": "problem-solving",
    "communication": "soft-skill", "leadership": "soft-skill",
    "ownership": "soft-skill", "collaboration": "soft-skill",
}

# Which language a framework primarily exercises (evidence attribution).
FRAMEWORK_LANGUAGE = {
    "FastAPI": "python", "Django": "python", "Flask": "python",
    "PyTorch": "python", "TensorFlow": "python", "Keras": "python",
    "scikit-learn": "python", "pandas": "python", "NumPy": "python",
    "LangChain": "python", "React": "javascript", "Next.js": "javascript",
    "Vue": "javascript", "Nuxt": "javascript", "Angular": "typescript",
    "Svelte": "javascript", "Express": "javascript", "Node.js": "javascript",
    "Spring": "java", "Rails": "ruby", "Laravel": "php",
}

# Dimensions requested by the product, grouped by which skill categories and
# evidence feed them.
DIMENSIONS = [
    ("programming", "Programming"),
    ("problem_solving", "Problem Solving"),
    ("backend", "Backend"),
    ("frontend", "Frontend"),
    ("ai_ml", "AI/ML"),
    ("cloud", "Cloud"),
    ("devops", "DevOps"),
    ("system_design", "System Design"),
    ("code_quality", "Code Quality"),
    ("documentation", "Documentation"),
    ("testing", "Testing"),
    ("open_source", "Open Source"),
    ("collaboration", "Collaboration"),
    ("ownership", "Ownership"),
    ("learning_velocity", "Learning Velocity"),
    ("consistency", "Consistency"),
    ("project_complexity", "Project Complexity"),
]

# Canonical language display-name normalisation (GitHub uses mixed case).
LANGUAGE_ALIASES = {
    "c#": "c#", "c++": "c++", "jupyter notebook": "python", "shell": "shell",
    "html": "html", "css": "css", "scss": "css", "less": "css",
    "vue": "vue", "svelte": "svelte",
}


def canon_lang(name: str) -> str:
    low = (name or "").strip().lower()
    return LANGUAGE_ALIASES.get(low, low)


def category_of(skill: str) -> str:
    return SKILL_CATEGORY.get((skill or "").lower(), "skill")


def merge_counts(a: Dict[str, int], b: Dict[str, int]) -> Dict[str, int]:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
    return out


def top_n(items: List, key, n: int) -> List:
    return sorted(items, key=key, reverse=True)[:n]
