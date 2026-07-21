import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.agents.bias_auditor import audit as run_fairness_audit
from app.agents.recruiter_copilot import CandidateContext, CopilotAnswer, answer_query
from app.auth import get_current_user
from app.config import settings
from app.models import (
    CandidateEvidence,
    FairnessReport,
    JobSpec,
    MatchResult,
    ResumeEvidence,
)
from app.schemas.api import (
    CandidateWithScorecard,
    CodeforcesAnalysisResponse,
    CopilotQueryRequest,
    CreateCandidateRequest,
    CreateJobRequest,
    ExtractJobDescriptionResponse,
    RunMatchingRequest,
)
from app.scoring.engine import build_scorecard, match_candidate
from app.scoring.job import parse_job
from app.services.codeforces_analyzer import analyze_codeforces_handle
from app.services.github_analyzer import github_analyzer
from app.services.jd_parser import extract_text_from_pdf_bytes, suggest_title_from_jd
from app.services.persistence import PersistenceError, persistence
from app.services.resume_parser import (
    extract_text_from_resume_bytes,
    parse_resume,
    parse_resume_preview,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skillsphere.api")


app = FastAPI(title="SkillSphere Talent Intelligence Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    # Allow Cloudflare Pages preview + production URLs
    allow_origin_regex=r"https://.*\.pages\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> Dict[str, object]:
    return {"success": True, "data": {"status": "ok", "llm_ready": settings.llm_ready}}


@app.get("/ping")
async def ping() -> Dict[str, object]:
    return {"success": True, "data": {"message": "pong"}}


_ROUTE_RATE_LIMITS = {
    "/jobs": 40,
    "/jobs/extract-jd-pdf": 20,
    "/candidates": 40,
    "/candidates/extract-resume-pdf": 30,
    "/match": 30,
    "/copilot": 90,
    "/codeforces": 60,
    "/audit": 60,
}


@app.on_event("startup")
async def validate_runtime_config() -> None:
    assert settings.supabase_jwt_secret, "SUPABASE_JWT_SECRET is required"
    if not settings.cors_origins():
        logger.warning("CORS_ORIGINS not set — falling back to localhost defaults")
    if not settings.llm_ready:
        logger.warning(
            "HF_API_TOKEN not set — AI copilot phrasing and resume/JD LLM enrichment are "
            "disabled; deterministic fallbacks remain active."
        )
    logger.info("Runtime config validated successfully")


def _owner_id(user: Dict) -> str:
    owner = str(user.get("id") or user.get("sub") or user.get("user_id") or "").strip()
    if not owner:
        raise HTTPException(status_code=401, detail="Invalid auth token payload")
    return owner


def _enforce_rate_limit(owner: str, route: str) -> None:
    buckets: Optional[Dict[str, Deque[float]]] = getattr(app.state, "rate_limit_buckets", None)
    if buckets is None:
        buckets = defaultdict(deque)
        app.state.rate_limit_buckets = buckets

    now = time.time()
    window_start = now - settings.rate_limit_window_seconds
    key = f"{owner}:{route}"
    bucket = buckets[key]

    while bucket and bucket[0] < window_start:
        bucket.popleft()

    max_requests = _ROUTE_RATE_LIMITS.get(route, settings.rate_limit_default)
    if len(bucket) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please retry shortly.")
    bucket.append(now)


def _read_upload_or_400(raw: bytes, kind: str) -> None:
    if not raw:
        raise HTTPException(status_code=400, detail=f"Uploaded {kind} is empty.")
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded {kind} is too large. Max allowed size is {settings.max_upload_bytes // (1024 * 1024)} MB.",
        )


def _validate_pdf_upload(file: UploadFile, kind: str) -> None:
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"Please upload a {kind} PDF file.")
    if file.content_type and file.content_type not in {
        "application/pdf", "application/x-pdf", "application/octet-stream", "binary/octet-stream",
    }:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Please upload a valid {kind} PDF.")


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
@app.post("/jobs", response_model=JobSpec)
async def create_job(req: CreateJobRequest, user=Depends(get_current_user)) -> JobSpec:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/jobs")
    job = await parse_job(req.job_id, req.title, req.description)
    try:
        persistence.upsert_job(owner, job)
    except PersistenceError as exc:
        logger.exception("Failed to persist job")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return job


@app.get("/jobs", response_model=List[JobSpec])
async def list_jobs(user=Depends(get_current_user)) -> List[JobSpec]:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/jobs")
    try:
        return persistence.list_jobs(owner)
    except PersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/jobs/{job_id}", response_model=JobSpec)
async def get_job(job_id: str, user=Depends(get_current_user)) -> JobSpec:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/jobs/{job_id}")
    try:
        job = persistence.get_job(owner, job_id)
    except PersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/jobs/extract-jd-pdf", response_model=ExtractJobDescriptionResponse)
async def extract_jd_pdf(file: UploadFile = File(...), user=Depends(get_current_user)) -> ExtractJobDescriptionResponse:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/jobs/extract-jd-pdf")
    _validate_pdf_upload(file, "JD")

    raw = await file.read(settings.max_upload_bytes + 1)
    _read_upload_or_400(raw, "PDF")

    try:
        extracted = extract_text_from_pdf_bytes(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {exc}") from exc
    if not extracted:
        raise HTTPException(status_code=400, detail="Could not extract readable text from this PDF.")

    return ExtractJobDescriptionResponse(extracted_text=extracted, suggested_title=suggest_title_from_jd(extracted))


# --------------------------------------------------------------------------- #
# Candidates
# --------------------------------------------------------------------------- #
@app.post("/candidates/extract-resume-pdf", response_model=ResumeEvidence)
async def extract_candidate_resume_pdf(file: UploadFile = File(...), user=Depends(get_current_user)) -> ResumeEvidence:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/candidates/extract-resume-pdf")
    _validate_pdf_upload(file, "resume")

    raw = await file.read(settings.max_upload_bytes + 1)
    _read_upload_or_400(raw, "resume file")

    try:
        extracted = extract_text_from_resume_bytes(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Failed to read resume PDF: {exc}") from exc
    if not extracted:
        raise HTTPException(status_code=400, detail="Could not extract readable text from this resume.")

    return parse_resume_preview(extracted)


async def _safe_codeforces(handle: str) -> Optional[dict]:
    if not handle:
        return None
    try:
        return await asyncio.to_thread(analyze_codeforces_handle, handle)
    except Exception as exc:  # noqa: BLE001
        logger.info("Codeforces analysis unavailable for %s: %s", handle, exc)
        return None


@app.post("/candidates", response_model=CandidateWithScorecard)
async def create_candidate(req: CreateCandidateRequest, user=Depends(get_current_user)) -> CandidateWithScorecard:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/candidates")

    github_evidence = None
    if req.github_username:
        github_evidence = await github_analyzer.analyze(req.github_username)

    resume_evidence = None
    if req.resume_text and req.resume_text.strip():
        resume_evidence = await parse_resume(req.resume_text)

    codeforces_data = await _safe_codeforces(req.codeforces_handle or "")

    ev = CandidateEvidence(
        candidate_id=req.candidate_id,
        name=req.name,
        headline=req.headline,
        summary=req.summary,
        github=github_evidence,
        resume=resume_evidence,
        codeforces=codeforces_data,
        demographics=req.demographics,
    )
    scorecard = build_scorecard(ev)

    try:
        persistence.upsert_candidate(owner, ev, scorecard)
    except PersistenceError as exc:
        logger.exception("Failed to persist candidate")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return CandidateWithScorecard(evidence=ev, scorecard=scorecard)


@app.get("/candidates", response_model=List[CandidateWithScorecard])
async def list_candidates(user=Depends(get_current_user)) -> List[CandidateWithScorecard]:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/candidates")
    try:
        rows = persistence.list_candidates(owner)
    except PersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return [CandidateWithScorecard(evidence=ev, scorecard=sc) for ev, sc in rows]


@app.get("/candidates/{candidate_id}", response_model=CandidateWithScorecard)
async def get_candidate(candidate_id: str, user=Depends(get_current_user)) -> CandidateWithScorecard:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/candidates/{candidate_id}")
    try:
        row = persistence.get_candidate(owner, candidate_id)
    except PersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    ev, sc = row
    return CandidateWithScorecard(evidence=ev, scorecard=sc)


# --------------------------------------------------------------------------- #
# Matching
# --------------------------------------------------------------------------- #
@app.post("/match", response_model=List[MatchResult])
async def run_matching(req: RunMatchingRequest, user=Depends(get_current_user)) -> List[MatchResult]:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/match")

    try:
        job = persistence.get_job(owner, req.job_id)
    except PersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results: List[MatchResult] = []
    for cid in req.candidate_ids:
        try:
            row = persistence.get_candidate(owner, cid)
        except PersistenceError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        if not row:
            continue
        ev, scorecard = row
        result = match_candidate(job, ev, scorecard)
        try:
            persistence.upsert_analysis(owner, result)
        except PersistenceError as exc:
            logger.exception("Failed to persist analysis")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        results.append(result)

    if not results:
        raise HTTPException(status_code=400, detail="No candidates with stored evidence were found for this job.")

    results.sort(key=lambda r: r.fit_score, reverse=True)
    return results


@app.get("/match/{job_id}", response_model=List[MatchResult])
async def get_match_results(job_id: str, user=Depends(get_current_user)) -> List[MatchResult]:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/match")
    try:
        results = persistence.list_analyses(owner, job_id)
    except PersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    results.sort(key=lambda r: r.fit_score, reverse=True)
    return results


@app.get("/analyses", response_model=List[MatchResult])
async def list_all_analyses(user=Depends(get_current_user)) -> List[MatchResult]:
    """Cross-job view of every persisted match result — used by the dashboard,
    which is not scoped to a single role."""
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/match")
    try:
        results = persistence.list_analyses(owner, None)
    except PersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    results.sort(key=lambda r: r.created_at, reverse=True)
    return results


@app.get("/audit/{job_id}", response_model=FairnessReport)
async def get_audit(job_id: str, user=Depends(get_current_user)) -> FairnessReport:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/audit")
    try:
        results = persistence.list_analyses(owner, job_id)
        candidates_by_id: Dict[str, CandidateEvidence] = {}
        for r in results:
            row = persistence.get_candidate(owner, r.candidate_id)
            if row:
                candidates_by_id[r.candidate_id] = row[0]
    except PersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return run_fairness_audit(job_id, results, candidates_by_id)


# --------------------------------------------------------------------------- #
# Recruiter Copilot
# --------------------------------------------------------------------------- #
@app.post("/copilot", response_model=CopilotAnswer)
async def copilot(req: CopilotQueryRequest, user=Depends(get_current_user)) -> CopilotAnswer:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/copilot")

    job: Optional[JobSpec] = None
    if req.job_id:
        try:
            job = persistence.get_job(owner, req.job_id)
        except PersistenceError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    candidate_ids = req.candidate_ids
    matches_by_candidate: Dict[str, MatchResult] = {}
    if not candidate_ids and req.job_id:
        try:
            job_results = persistence.list_analyses(owner, req.job_id)
        except PersistenceError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        candidate_ids = [r.candidate_id for r in job_results]
        matches_by_candidate = {r.candidate_id: r for r in job_results}
    elif candidate_ids and req.job_id:
        for cid in candidate_ids:
            m = persistence.get_analysis(owner, req.job_id, cid)
            if m:
                matches_by_candidate[cid] = m

    if not candidate_ids:
        try:
            rows = persistence.list_candidates(owner)
        except PersistenceError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        contexts = [
            CandidateContext(candidate_id=ev.candidate_id, name=ev.name, scorecard=sc, match=None)
            for ev, sc in rows
        ]
    else:
        contexts = []
        for cid in candidate_ids:
            row = persistence.get_candidate(owner, cid)
            if not row:
                continue
            ev, sc = row
            contexts.append(
                CandidateContext(
                    candidate_id=ev.candidate_id, name=ev.name, scorecard=sc, match=matches_by_candidate.get(cid)
                )
            )

    return await answer_query(req.query, contexts, job)


# --------------------------------------------------------------------------- #
# Codeforces
# --------------------------------------------------------------------------- #
@app.get("/codeforces/{handle}/analysis", response_model=CodeforcesAnalysisResponse)
async def codeforces_analysis(handle: str, user=Depends(get_current_user)) -> CodeforcesAnalysisResponse:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/codeforces")
    try:
        data = await asyncio.to_thread(analyze_codeforces_handle, handle)
        return CodeforcesAnalysisResponse(**data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Codeforces analysis failed: {exc}") from exc
