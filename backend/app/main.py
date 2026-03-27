import os
import time
import logging
from collections import defaultdict, deque
from typing import Deque, Dict, List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.agents.job_intelligence import JobIntelligenceAgent, RoleRequirementGraph
from app.agents.talent_scout import TalentScoutAgent, TalentSignals
from app.agents.skill_graph_builder import SkillGraphBuilderAgent
from app.agents.matching import MatchingAndRankingAgent
from app.agents.bias_auditor import BiasAuditorAgent
from app.agents.recruiter_copilot import RecruiterCopilotAgent
from app.models import CandidateProfile, JobDescription, SkillGraph
from app.schemas.api import (
    CreateJobRequest,
    ExtractJobDescriptionResponse,
    ExtractResumeResponse,
    CreateCandidateRequest,
    RunMatchingRequest,
    RunMatchingResponse,
    RankedCandidate,
    CopilotQueryRequest,
    CopilotResponse,
    AuditLogResponse,
    AuditEntryResponse,
    CodeforcesAnalysisResponse,
)
from app.services.codeforces_analyzer import analyze_codeforces_handle
from app.services.jd_parser import extract_text_from_pdf_bytes, suggest_title_from_jd
from app.services.resume_parser import (
    extract_text_from_resume_bytes,
    infer_resume_skills,
    infer_years_experience,
)
from app.auth import get_current_user
from app.services.persistence import persistence, PersistenceError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skillsphere.api")


def _get_cors_origins() -> List[str]:
    raw = os.environ.get("CORS_ORIGINS", "")
    if raw.strip():
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


app = FastAPI(title="SkillSphere Talent Intelligence Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> Dict[str, object]:
    return {"success": True, "data": {"status": "ok"}}


@app.get("/ping")
async def ping() -> Dict[str, object]:
    return {"success": True, "data": {"message": "pong"}}

# In-memory storage retained for ephemeral computed state.
_SKILL_GRAPHS: Dict[str, Dict[str, SkillGraph]] = {}

_job_agent = JobIntelligenceAgent()
_talent_agent = TalentScoutAgent()
_skill_agent = SkillGraphBuilderAgent()
_match_agent = MatchingAndRankingAgent()
_bias_agent = BiasAuditorAgent()
_copilot_agent = RecruiterCopilotAgent()

_MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", "5242880"))
_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
_DEFAULT_RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS_PER_WINDOW", "120"))
_ROUTE_RATE_LIMITS = {
    "/jobs/extract-jd-pdf": 20,
    "/candidates/extract-resume-pdf": 30,
    "/match": 30,
    "/copilot": 90,
    "/codeforces": 60,
}


@app.on_event("startup")
async def validate_runtime_config() -> None:
    assert os.getenv("SUPABASE_JWT_SECRET"), "SUPABASE_JWT_SECRET is required"
    assert os.getenv("CORS_ORIGINS"), "CORS_ORIGINS is required"
    logger.info("Runtime config validated successfully")


def _owner_id(user: Dict) -> str:
    owner = str(user.get("sub") or user.get("user_id") or "").strip()
    if not owner:
        raise HTTPException(status_code=401, detail="Invalid auth token payload")
    return owner


def _store_for_owner(store: Dict[str, Dict], owner: str) -> Dict:
    return store.setdefault(owner, {})


def _enforce_rate_limit(owner: str, route: str) -> None:
    buckets: Dict[str, Deque[float]] = getattr(app.state, "rate_limit_buckets", None)
    if buckets is None:
        buckets = defaultdict(deque)
        app.state.rate_limit_buckets = buckets

    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW_SECONDS
    key = f"{owner}:{route}"
    bucket = buckets[key]

    while bucket and bucket[0] < window_start:
        bucket.popleft()

    max_requests = _ROUTE_RATE_LIMITS.get(route, _DEFAULT_RATE_LIMIT_REQUESTS)
    if len(bucket) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please retry shortly.")

    bucket.append(now)


@app.post("/jobs", response_model=JobDescription)
async def create_job(req: CreateJobRequest, user=Depends(get_current_user)) -> JobDescription:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/jobs")
    graph = _job_agent.build_role_graph(job_id=req.job_id, title=req.title, description=req.description)

    try:
        persistence.upsert_job(owner, graph.job)
    except PersistenceError as exc:
        logger.exception("Failed to persist job")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return graph.job


@app.post("/jobs/extract-jd-pdf", response_model=ExtractJobDescriptionResponse)
async def extract_jd_pdf(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> ExtractJobDescriptionResponse:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/jobs/extract-jd-pdf")

    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    if file.content_type and file.content_type not in {
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream",
        "binary/octet-stream",
    }:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a valid PDF.")

    raw = await file.read(_MAX_UPLOAD_BYTES + 1)
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded PDF is too large. Max allowed size is {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        extracted = extract_text_from_pdf_bytes(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {exc}") from exc

    if not extracted:
        raise HTTPException(status_code=400, detail="Could not extract readable text from this PDF.")

    return ExtractJobDescriptionResponse(
        extracted_text=extracted,
        suggested_title=suggest_title_from_jd(extracted),
    )


@app.post("/candidates/extract-resume-pdf", response_model=ExtractResumeResponse)
async def extract_candidate_resume_pdf(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> ExtractResumeResponse:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/candidates/extract-resume-pdf")

    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a resume PDF file.")

    if file.content_type and file.content_type not in {
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream",
        "binary/octet-stream",
    }:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a valid resume PDF.")

    raw = await file.read(_MAX_UPLOAD_BYTES + 1)
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded resume PDF is too large. Max allowed size is {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        extracted = extract_text_from_resume_bytes(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Failed to read resume PDF: {exc}") from exc

    if not extracted:
        raise HTTPException(status_code=400, detail="Could not extract readable text from this resume.")

    inferred_skills = infer_resume_skills(extracted)
    years_experience = infer_years_experience(extracted)

    return ExtractResumeResponse(
        extracted_text=extracted,
        inferred_skills=inferred_skills,
        estimated_years_experience=years_experience,
    )



@app.get("/jobs/{job_id}", response_model=JobDescription)
async def get_job(job_id: str, user=Depends(get_current_user)) -> JobDescription:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/jobs/{job_id}")
    try:
        job = persistence.get_job(owner, job_id)
    except PersistenceError as exc:
        logger.exception("Failed to fetch job")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/candidates", response_model=CandidateProfile)
async def create_candidate(req: CreateCandidateRequest, user=Depends(get_current_user)) -> CandidateProfile:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/candidates")
    skill_graphs = _store_for_owner(_SKILL_GRAPHS, owner)

    profile = CandidateProfile(
        id=req.candidate_id,
        name=req.name,
        headline=req.headline,
        summary=req.summary,
        platforms=req.platforms,
        demographics=req.demographics,
    )
    signals: TalentSignals = _talent_agent.gather_signals(profile)
    graph: SkillGraph = _skill_agent.build_skill_graph(signals)

    try:
        persistence.upsert_candidate(owner, profile)
    except PersistenceError as exc:
        logger.exception("Failed to persist candidate")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    skill_graphs[profile.id] = graph

    return profile


@app.get("/candidates/{candidate_id}", response_model=CandidateProfile)
async def get_candidate(candidate_id: str, user=Depends(get_current_user)) -> CandidateProfile:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/candidates/{candidate_id}")
    try:
        cand = persistence.get_candidate(owner, candidate_id)
    except PersistenceError as exc:
        logger.exception("Failed to fetch candidate")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand


@app.post("/match", response_model=RunMatchingResponse)
async def run_matching(req: RunMatchingRequest, user=Depends(get_current_user)) -> RunMatchingResponse:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/match")
    skill_graphs = _store_for_owner(_SKILL_GRAPHS, owner)

    try:
        persisted_job = persistence.get_job(owner, req.job_id)
    except PersistenceError as exc:
        logger.exception("Failed to fetch job for matching")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not persisted_job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_graph = _job_agent.build_role_graph(
        job_id=persisted_job.id,
        title=persisted_job.title,
        description=persisted_job.description,
    )

    graphs: List[SkillGraph] = []
    candidates_by_id: Dict[str, CandidateProfile] = {}
    for cid in req.candidate_ids:
        try:
            cand = persistence.get_candidate(owner, cid)
        except PersistenceError as exc:
            logger.exception("Failed to fetch candidate for matching")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        if cand is None:
            continue

        candidates_by_id[cid] = cand
        sg = skill_graphs.get(cid)
        if sg is None:
            signals: TalentSignals = _talent_agent.gather_signals(cand)
            sg = _skill_agent.build_skill_graph(signals)
            skill_graphs[cid] = sg
        graphs.append(sg)

    if not graphs:
        raise HTTPException(status_code=400, detail="No candidates with skill graphs available")

    ranked_scores = _match_agent.rank_candidates(job_graph.job, graphs)
    audit_logs = _bias_agent.audit(job_graph.job.id, ranked_scores, candidates_by_id)

    ranked = [
        RankedCandidate(
            candidate_id=s.candidate_id,
            score=s.score,
            explanation=s.explanation,
            time_to_productivity_pomodoros=s.time_to_productivity_pomodoros,
            time_to_productivity_hours=s.time_to_productivity_hours,
            time_to_productivity_sprints=s.time_to_productivity_sprints,
            time_to_productivity_explanation=s.time_to_productivity_explanation,
            direct_matches=s.direct_matches,
            adjacent_support=s.adjacent_support,
            xai=s.xai.model_dump() if s.xai is not None else None,
        )
        for s in ranked_scores
    ]

    # Store audit logs in memory keyed by job
    app.state.audit_logs = getattr(app.state, "audit_logs", {})
    owner_logs = app.state.audit_logs.setdefault(owner, {})
    owner_logs[req.job_id] = audit_logs

    return RunMatchingResponse(job_id=req.job_id, ranked=ranked)


@app.get("/audit/{job_id}", response_model=AuditLogResponse)
async def get_audit(job_id: str, user=Depends(get_current_user)) -> AuditLogResponse:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/audit/{job_id}")
    all_logs: Dict[str, Dict[str, List]] = getattr(app.state, "audit_logs", {})
    owner_logs = all_logs.get(owner, {})
    logs = owner_logs.get(job_id, [])

    entries = [
        AuditEntryResponse(
            candidate_id=log.candidate_id,
            bias_flags=[f.reason for f in log.bias_flags],
        )
        for log in logs
    ]

    return AuditLogResponse(job_id=job_id, entries=entries)


@app.post("/copilot", response_model=CopilotResponse)
async def copilot(query: CopilotQueryRequest, user=Depends(get_current_user)) -> CopilotResponse:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/copilot")
    graphs_store = _store_for_owner(_SKILL_GRAPHS, owner)

    try:
        persisted_job = persistence.get_job(owner, query.job_id)
    except PersistenceError as exc:
        logger.exception("Failed to fetch job for copilot")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not persisted_job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_graph = _job_agent.build_role_graph(
        job_id=persisted_job.id,
        title=persisted_job.title,
        description=persisted_job.description,
    )

    if query.candidate_id:
        try:
            cand = persistence.get_candidate(owner, query.candidate_id)
        except PersistenceError as exc:
            logger.exception("Failed to fetch candidate for copilot")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        graph = graphs_store.get(query.candidate_id)
        if cand and graph is None:
            signals: TalentSignals = _talent_agent.gather_signals(cand)
            graph = _skill_agent.build_skill_graph(signals)
            graphs_store[query.candidate_id] = graph

        if not cand or not graph:
            raise HTTPException(status_code=404, detail="Candidate or skill graph not found")

        ranked_scores = _match_agent.rank_candidates(job_graph.job, [graph])
        match = ranked_scores[0] if ranked_scores else None

        all_logs: Dict[str, Dict[str, List]] = getattr(app.state, "audit_logs", {})
        logs_for_job = all_logs.get(owner, {}).get(query.job_id, [])
        audit = next((l for l in logs_for_job if l.candidate_id == cand.id), None)

        answer = _copilot_agent.summarize_candidate(cand, graph, match, audit)
        return CopilotResponse(answer=answer)

    # Otherwise summarize the whole shortlist if we have logs
    all_logs: Dict[str, Dict[str, List]] = getattr(app.state, "audit_logs", {})
    logs_for_job = all_logs.get(owner, {}).get(query.job_id, [])
    try:
        candidates = persistence.list_candidates(owner)
    except PersistenceError as exc:
        logger.exception("Failed to list candidates for copilot")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    graphs: List[SkillGraph] = []
    for cand in candidates:
        graph = graphs_store.get(cand.id)
        if graph is None:
            signals: TalentSignals = _talent_agent.gather_signals(cand)
            graph = _skill_agent.build_skill_graph(signals)
            graphs_store[cand.id] = graph
        graphs.append(graph)

    # If we have no matches yet, just describe the role
    if not logs_for_job:
        answer = f"Role {job_graph.job.title} expects: " + ", ".join(
            r.name for r in job_graph.core_requirements
        )
        return CopilotResponse(answer=answer)

    ranked_scores = _match_agent.rank_candidates(job_graph.job, graphs)
    answer = _copilot_agent.summarize_shortlist(
        job_graph.job,
        candidates,
        graphs,
        ranked_scores,
        logs_for_job,
    )
    return CopilotResponse(answer=answer)


@app.get("/codeforces/{handle}/analysis", response_model=CodeforcesAnalysisResponse)
async def codeforces_analysis(handle: str, user=Depends(get_current_user)) -> CodeforcesAnalysisResponse:
    owner = _owner_id(user)
    _enforce_rate_limit(owner, "/codeforces")
    try:
        data = analyze_codeforces_handle(handle)
        return CodeforcesAnalysisResponse(**data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Codeforces analysis failed: {exc}") from exc
