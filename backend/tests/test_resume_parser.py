from app.services.resume_parser import parse_resume_preview


SAMPLE = """Jane Doe
jane.doe@example.com | github.com/janedoe | linkedin.com/in/janedoe

Summary
Backend engineer with 6 years of experience in Python and distributed systems.

Skills
Python, FastAPI, PostgreSQL, Docker, Kubernetes, React

Certifications
AWS Certified Solutions Architect
"""


def test_parse_resume_preview_extracts_contact():
    ev = parse_resume_preview(SAMPLE)
    assert ev.contact.email == "jane.doe@example.com"
    assert ev.contact.github == "janedoe"
    assert ev.contact.linkedin == "janedoe"


def test_parse_resume_preview_extracts_skills_and_years():
    ev = parse_resume_preview(SAMPLE)
    assert "python" in ev.skills
    assert "fastapi" in ev.skills
    assert ev.total_experience_years == 6.0


def test_parse_resume_preview_is_rules_only():
    ev = parse_resume_preview(SAMPLE)
    assert ev.parsed_by == "rules"


def test_parse_resume_preview_handles_empty_text():
    ev = parse_resume_preview("")
    assert ev.skills == []
    assert ev.total_experience_years is None
