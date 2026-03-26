from typing import Dict, List

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

app = FastAPI(title="SkillSphere Talent Intelligence Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage just for demo purposes
_JOBS: Dict[str, RoleRequirementGraph] = {}
_CANDIDATES: Dict[str, CandidateProfile] = {}
_SKILL_GRAPHS: Dict[str, SkillGraph] = {}

_job_agent = JobIntelligenceAgent()
_talent_agent = TalentScoutAgent()
_skill_agent = SkillGraphBuilderAgent()
_match_agent = MatchingAndRankingAgent()
_bias_agent = BiasAuditorAgent()
_copilot_agent = RecruiterCopilotAgent()


@app.post("/jobs", response_model=JobDescription)
async def create_job(req: CreateJobRequest, user=Depends(get_current_user)) -> JobDescription:
    graph = _job_agent.build_role_graph(job_id=req.job_id, title=req.title, description=req.description)
    _JOBS[req.job_id] = graph
    return graph.job


@app.post("/jobs/extract-jd-pdf", response_model=ExtractJobDescriptionResponse)
async def extract_jd_pdf(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> ExtractJobDescriptionResponse:
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

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
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a resume PDF file.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

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
    graph = _JOBS.get(job_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Job not found")
    return graph.job


@app.post("/candidates", response_model=CandidateProfile)
async def create_candidate(req: CreateCandidateRequest, user=Depends(get_current_user)) -> CandidateProfile:
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

    _CANDIDATES[profile.id] = profile
    _SKILL_GRAPHS[profile.id] = graph

    return profile


@app.get("/candidates/{candidate_id}", response_model=CandidateProfile)
async def get_candidate(candidate_id: str, user=Depends(get_current_user)) -> CandidateProfile:
    cand = _CANDIDATES.get(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand


@app.post("/match", response_model=RunMatchingResponse)
async def run_matching(req: RunMatchingRequest, user=Depends(get_current_user)) -> RunMatchingResponse:
    job_graph = _JOBS.get(req.job_id)
    if not job_graph:
        raise HTTPException(status_code=404, detail="Job not found")

    graphs: List[SkillGraph] = []
    for cid in req.candidate_ids:
        sg = _SKILL_GRAPHS.get(cid)
        if sg is not None:
            graphs.append(sg)

    if not graphs:
        raise HTTPException(status_code=400, detail="No candidates with skill graphs available")

    ranked_scores = _match_agent.rank_candidates(job_graph.job, graphs)
    candidates_by_id = {cid: _CANDIDATES[cid] for cid in req.candidate_ids if cid in _CANDIDATES}
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
    app.state.audit_logs[req.job_id] = audit_logs

    return RunMatchingResponse(job_id=req.job_id, ranked=ranked)


@app.get("/audit/{job_id}", response_model=AuditLogResponse)
async def get_audit(job_id: str, user=Depends(get_current_user)) -> AuditLogResponse:
    all_logs: Dict[str, List] = getattr(app.state, "audit_logs", {})
    logs = all_logs.get(job_id, [])

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
    job_graph = _JOBS.get(query.job_id)
    if not job_graph:
        raise HTTPException(status_code=404, detail="Job not found")

    if query.candidate_id:
        cand = _CANDIDATES.get(query.candidate_id)
        graph = _SKILL_GRAPHS.get(query.candidate_id)
        if not cand or not graph:
            raise HTTPException(status_code=404, detail="Candidate or skill graph not found")

        ranked_scores = _match_agent.rank_candidates(job_graph.job, [graph])
        match = ranked_scores[0] if ranked_scores else None

        all_logs: Dict[str, List] = getattr(app.state, "audit_logs", {})
        logs_for_job = all_logs.get(query.job_id, [])
        audit = next((l for l in logs_for_job if l.candidate_id == cand.id), None)

        answer = _copilot_agent.summarize_candidate(cand, graph, match, audit)
        return CopilotResponse(answer=answer)

    # Otherwise summarize the whole shortlist if we have logs
    all_logs: Dict[str, List] = getattr(app.state, "audit_logs", {})
    logs_for_job = all_logs.get(query.job_id, [])
    candidates = list(_CANDIDATES.values())
    graphs = list(_SKILL_GRAPHS.values())

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
    try:
        data = analyze_codeforces_handle(handle)
        return CodeforcesAnalysisResponse(**data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Codeforces analysis failed: {exc}") from exc
