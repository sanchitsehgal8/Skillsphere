from __future__ import annotations

import re
from io import BytesIO

from pypdf import PdfReader

SKILL_KEYWORDS = {
    "python": ["python", "pandas", "numpy", "scikit-learn"],
    "fastapi": ["fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "react": ["react", "next.js", "nextjs"],
    "typescript": ["typescript", "ts"],
    "javascript": ["javascript", "node.js", "nodejs"],
    "sql": ["sql", "postgres", "mysql"],
    "aws": ["aws", "ec2", "s3", "lambda"],
    "docker": ["docker", "kubernetes", "k8s"],
    "system design": ["system design", "microservices", "distributed systems"],
    "machine learning": ["machine learning", "ml", "deep learning", "llm"],
    "communication": ["communication", "stakeholder", "cross-functional"],
}


def extract_text_from_resume_bytes(raw_bytes: bytes) -> str:
    
    if not raw_bytes:
        return ""

    reader = PdfReader(BytesIO(raw_bytes))
    pages_text: list[str] = []
    for page in reader.pages:
        page_text = (page.extract_text() or "").strip()
        if page_text:
            pages_text.append(page_text)

    return "\n\n".join(pages_text).strip()


def infer_resume_skills(text: str) -> list[str]:
    if not text:
        return []

    lowered = text.lower()
    found: list[str] = []
    for canonical, aliases in SKILL_KEYWORDS.items():
        if any(alias in lowered for alias in aliases):
            found.append(canonical)

    return sorted(set(found))


def infer_years_experience(text: str) -> float | None:
    if not text:
        return None

    lowered = text.lower()
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s+years?\s+(?:of\s+)?experience",
        r"experience\s+of\s+(\d+(?:\.\d+)?)\+?\s+years?",
        r"(\d+(?:\.\d+)?)\+?\s+yrs?\s+(?:of\s+)?experience",
    ]

    matches: list[float] = []
    for pattern in patterns:
        for m in re.finditer(pattern, lowered):
            try:
                value = float(m.group(1))
                if 0.0 <= value <= 40.0:
                    matches.append(value)
            except (TypeError, ValueError):
                continue

    if not matches:
        return None

    return max(matches)
