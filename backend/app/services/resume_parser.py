"""Structured resume parsing.

Two-stage, deterministic-first:
1. **Rules** — regex/heuristics reliably extract contact details, links, a
   skill set from a broad taxonomy, years of experience, and section text.
   These are ground truth (regex does not hallucinate emails/URLs).
2. **LLM structuring (optional)** — when the HF model is available it structures
   the free-form sections (education, experience, projects, certifications,
   achievements) that are hard to parse with rules, strictly grounded to the
   text. Rules-derived contact/links/skills always win on conflict.

If the LLM is unavailable the rules result is returned unchanged, so parsing
always works.
"""

from __future__ import annotations

import re
from io import BytesIO
from typing import List, Optional

from pypdf import PdfReader

from app.models import (
    EducationItem,
    ExperienceItem,
    ProjectItem,
    ResumeContact,
    ResumeEvidence,
)
from app.services.llm import llm

# Broad, categorised skill taxonomy (canonical -> aliases).
SKILL_TAXONOMY = {
    "python": ["python", "pandas", "numpy", "scikit-learn", "pytest"],
    "java": ["java", "spring", "hibernate"],
    "c++": ["c++", "cpp"],
    "c": [" c ", "c language"],
    "go": ["golang", " go "],
    "rust": ["rust"],
    "javascript": ["javascript", "node.js", "nodejs", "node "],
    "typescript": ["typescript", "ts "],
    "react": ["react", "next.js", "nextjs"],
    "vue": ["vue", "nuxt"],
    "angular": ["angular"],
    "fastapi": ["fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "express": ["express.js", "expressjs"],
    "sql": ["sql", "postgres", "postgresql", "mysql", "sqlite"],
    "nosql": ["mongodb", "dynamodb", "cassandra", "redis"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "gcp": ["gcp", "google cloud"],
    "azure": ["azure"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "terraform": ["terraform"],
    "ci/cd": ["ci/cd", "jenkins", "github actions", "gitlab ci"],
    "system design": ["system design", "microservices", "distributed systems"],
    "machine learning": ["machine learning", "deep learning", "neural network"],
    "llm": ["llm", "large language model", "langchain", "transformer", "rag"],
    "data engineering": ["data engineering", "etl", "airflow", "spark", "kafka"],
    "tensorflow": ["tensorflow", "keras"],
    "pytorch": ["pytorch"],
    "graphql": ["graphql"],
    "git": ["git", "github", "gitlab"],
    "communication": ["communication", "stakeholder", "cross-functional"],
    "leadership": ["led ", "leadership", "mentored", "managed a team"],
}

_SECTION_HEADERS = {
    "education": ["education", "academic"],
    "experience": ["experience", "employment", "work history", "professional experience"],
    "projects": ["projects", "personal projects", "selected projects"],
    "certifications": ["certifications", "certificates", "licenses"],
    "achievements": ["achievements", "awards", "honors", "accomplishments"],
    "hackathons": ["hackathons", "hackathon"],
    "internships": ["internships", "internship"],
    "skills": ["skills", "technical skills", "technologies"],
    "summary": ["summary", "objective", "about"],
}

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,4})")
_GITHUB_RE = re.compile(r"github\.com/([A-Za-z0-9_-]+)", re.I)
_LINKEDIN_RE = re.compile(r"linkedin\.com/(?:in|pub)/([A-Za-z0-9_-]+)", re.I)
_URL_RE = re.compile(r"https?://[^\s)]+", re.I)
_YEARS_RE = [
    re.compile(r"(\d{1,2}(?:\.\d)?)\+?\s*years?\s+(?:of\s+)?experience", re.I),
    re.compile(r"experience\s*(?:of|:)?\s*(\d{1,2}(?:\.\d)?)\+?\s*years?", re.I),
    re.compile(r"(\d{1,2}(?:\.\d)?)\+?\s*yrs?", re.I),
]


def extract_text_from_resume_bytes(raw_bytes: bytes) -> str:
    if not raw_bytes:
        return ""
    reader = PdfReader(BytesIO(raw_bytes))
    pages = [(p.extract_text() or "").strip() for p in reader.pages]
    return "\n\n".join(t for t in pages if t).strip()


def _infer_skills(text_lower: str) -> List[str]:
    padded = f" {text_lower} "
    found = [
        canonical
        for canonical, aliases in SKILL_TAXONOMY.items()
        if any(alias in padded for alias in aliases)
    ]
    return sorted(set(found))


def _infer_years(text_lower: str) -> Optional[float]:
    matches: List[float] = []
    for pat in _YEARS_RE:
        for m in pat.finditer(text_lower):
            try:
                v = float(m.group(1))
                if 0.0 <= v <= 40.0:
                    matches.append(v)
            except (TypeError, ValueError):
                continue
    return max(matches) if matches else None


def _extract_contact(text: str) -> ResumeContact:
    emails = _EMAIL_RE.findall(text)
    phones = _PHONE_RE.findall(text)
    gh = _GITHUB_RE.search(text)
    li = _LINKEDIN_RE.search(text)
    urls = _URL_RE.findall(text)
    portfolio = next(
        (
            u for u in urls
            if "github.com" not in u.lower() and "linkedin.com" not in u.lower()
        ),
        None,
    )
    # First non-empty line is usually the name.
    name = next((ln.strip() for ln in text.splitlines() if ln.strip()), None)
    if name and (len(name) > 60 or "@" in name):
        name = None
    return ResumeContact(
        name=name,
        email=emails[0] if emails else None,
        phone=(phones[0].strip() if phones else None),
        github=gh.group(1) if gh else None,
        linkedin=li.group(1) if li else None,
        portfolio=portfolio,
        other_links=sorted(set(urls))[:8],
    )


def _split_sections(text: str) -> dict:
    """Slice the resume into sections by detected headers."""
    lines = text.splitlines()
    sections: dict = {}
    current = "header"
    buf: List[str] = []

    def flush(name: str, content: List[str]) -> None:
        if content:
            sections.setdefault(name, "")
            sections[name] += "\n".join(content).strip() + "\n"

    for line in lines:
        stripped = line.strip().lower().rstrip(":")
        matched = None
        if 0 < len(stripped) <= 40:
            for name, keys in _SECTION_HEADERS.items():
                if stripped in keys or any(stripped == k for k in keys):
                    matched = name
                    break
        if matched:
            flush(current, buf)
            buf = []
            current = matched
        else:
            buf.append(line)
    flush(current, buf)
    return sections


def _rules_parse(text: str) -> ResumeEvidence:
    lower = text.lower()
    sections = _split_sections(text)
    return ResumeEvidence(
        contact=_extract_contact(text),
        summary=(sections.get("summary") or "").strip() or None,
        skills=_infer_skills(lower),
        total_experience_years=_infer_years(lower),
        certifications=[
            ln.strip("-• \t")
            for ln in (sections.get("certifications") or "").splitlines()
            if ln.strip()
        ][:12],
        achievements=[
            ln.strip("-• \t")
            for ln in (sections.get("achievements") or "").splitlines()
            if ln.strip()
        ][:12],
        parsed_by="rules",
        raw_text=text,
    )


_LLM_SYSTEM = (
    "You are a precise resume parser. Extract ONLY information explicitly present "
    "in the resume text. Never invent employers, dates, degrees, or skills. If a "
    "field is absent, omit it or use an empty list. Return strict JSON only."
)

_LLM_SCHEMA_HINT = (
    'Return JSON with this shape: {"education":[{"institution":str,"degree":str,'
    '"field":str,"start_year":int,"end_year":int}],"experience":[{"company":str,'
    '"title":str,"start":str,"end":str,"is_current":bool,"description":str}],'
    '"projects":[{"name":str,"description":str,"tech":[str]}],'
    '"certifications":[str],"achievements":[str],"hackathons":[str],'
    '"internships":[{"company":str,"title":str,"start":str,"end":str}]}'
)


async def _llm_enrich(text: str, base: ResumeEvidence) -> ResumeEvidence:
    if not llm.is_ready:
        return base
    excerpt = text[:6000]
    data = await llm.achat_json(
        [
            {"role": "system", "content": _LLM_SYSTEM},
            {"role": "user", "content": f"{_LLM_SCHEMA_HINT}\n\nRESUME:\n{excerpt}"},
        ],
        max_tokens=1200,
    )
    if not isinstance(data, dict):
        return base

    def _items(key: str, model, fields):
        out = []
        for raw in data.get(key, []) or []:
            if not isinstance(raw, dict):
                continue
            try:
                out.append(model(**{f: raw.get(f) for f in fields if raw.get(f) is not None}))
            except Exception:  # noqa: BLE001 - skip malformed rows
                continue
        return out

    base.education = _items(
        "education", EducationItem,
        ["institution", "degree", "field", "start_year", "end_year", "gpa"],
    ) or base.education
    base.experience = _items(
        "experience", ExperienceItem,
        ["company", "title", "start", "end", "is_current", "description"],
    ) or base.experience
    base.internships = _items(
        "internships", ExperienceItem, ["company", "title", "start", "end"]
    ) or base.internships
    base.projects = _items(
        "projects", ProjectItem, ["name", "description", "tech", "url"]
    ) or base.projects
    for key in ("certifications", "achievements", "hackathons"):
        vals = [str(v).strip() for v in (data.get(key) or []) if str(v).strip()]
        if vals:
            setattr(base, key, vals[:15])
    base.parsed_by = "hybrid"
    return base


def parse_resume_preview(text: str) -> ResumeEvidence:
    """Fast, rules-only parse for instant upload feedback (no LLM round-trip)."""
    return _rules_parse(text)


async def parse_resume(text: str) -> ResumeEvidence:
    base = _rules_parse(text)
    if not text.strip():
        return base
    try:
        return await _llm_enrich(text, base)
    except Exception:  # noqa: BLE001 - LLM must never break parsing
        return base


# --- Backwards-compatible helpers still used by the extract endpoint ---
def infer_resume_skills(text: str) -> List[str]:
    return _infer_skills((text or "").lower())


def infer_years_experience(text: str) -> Optional[float]:
    return _infer_years((text or "").lower())
