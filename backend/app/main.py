from typing import Dict, List

from fastapi import FastAPI, HTTPException
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
    CreateCandidateRequest,
    RunMatchingRequest,
    RunMatchingResponse,
    RankedCandidate,
    CopilotQueryRequest,
    CopilotResponse,
    AuditLogResponse,
    AuditEntryResponse,
)

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
async def create_job(req: CreateJobRequest) -> JobDescription:
    graph = _job_agent.build_role_graph(job_id=req.job_id, title=req.title, description=req.description)
    _JOBS[req.job_id] = graph
    return graph.job


@app.get("/jobs/{job_id}", response_model=JobDescription)
async def get_job(job_id: str) -> JobDescription:
    graph = _JOBS.get(job_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Job not found")
    return graph.job


@app.post("/candidates", response_model=CandidateProfile)
async def create_candidate(req: CreateCandidateRequest) -> CandidateProfile:
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
async def get_candidate(candidate_id: str) -> CandidateProfile:
    cand = _CANDIDATES.get(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand


@app.post("/match", response_model=RunMatchingResponse)
async def run_matching(req: RunMatchingRequest) -> RunMatchingResponse:
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
            time_to_productivity_days=s.time_to_productivity_days,
            direct_matches=s.direct_matches,
            adjacent_support=s.adjacent_support,
        )
        for s in ranked_scores
    ]

    # Store audit logs in memory keyed by job
    app.state.audit_logs = getattr(app.state, "audit_logs", {})
    app.state.audit_logs[req.job_id] = audit_logs

    return RunMatchingResponse(job_id=req.job_id, ranked=ranked)


@app.get("/audit/{job_id}", response_model=AuditLogResponse)
async def get_audit(job_id: str) -> AuditLogResponse:
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
async def copilot(query: CopilotQueryRequest) -> CopilotResponse:
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
