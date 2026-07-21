import asyncio

from app.scoring.job import parse_job


def test_parse_job_extracts_taxonomy_skills():
    job = asyncio.run(parse_job("j1", "Backend Engineer", "We need Python, FastAPI and AWS experience."))
    names = {r.name for r in job.requirements}
    assert {"python", "fastapi", "aws"}.issubset(names)


def test_parse_job_word_boundary_avoids_false_positive():
    # "go" must not match inside "going" or "algorithm" etc.
    job = asyncio.run(parse_job("j2", "Role", "We are going to interview soon."))
    names = {r.name for r in job.requirements}
    assert "go" not in names


def test_parse_job_falls_back_when_nothing_matches():
    job = asyncio.run(parse_job("j3", "Mystery Role", "Some entirely unrelated fluff text."))
    assert len(job.requirements) >= 1
    assert job.requirements[0].source == "fallback"


def test_parse_job_detects_seniority():
    job = asyncio.run(parse_job("j4", "Senior Backend Engineer", "Python required."))
    assert job.seniority == "senior"
