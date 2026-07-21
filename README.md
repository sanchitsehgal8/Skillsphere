# SkillSphere

SkillSphere is an evidence-based engineering talent intelligence platform. It combines a React frontend, a FastAPI backend, a modular explainable scoring engine, and an AI recruiter copilot (Qwen 2.5, via Hugging Face Inference Providers) to evaluate candidate fit from observable GitHub activity, resume content, and competitive-programming history — never from arbitrary heuristics or unexplained numbers.

Every score the system produces carries **evidence**, a **confidence**, a plain-language **reasoning** string, and — where the score is not already strong — a concrete **improvement suggestion**. Nothing is asserted without a traceable source.

---

## Overview

Recruiters give SkillSphere a job description and a candidate's GitHub username (and optionally a resume PDF and Codeforces handle). The backend:

1. Mines the candidate's public GitHub footprint at the byte level (languages, frameworks, CI/test/docs presence, recency, OSS signal) — server-side, not from the browser.
2. Parses the resume with a rules engine (contact info, skills, years of experience — always available) plus an optional LLM structuring pass (education, experience, projects, certifications — grounded strictly to the resume text).
3. Runs the modular scoring engine to produce a 17-dimension **Engineering Scorecard**, an **Evidence-Based Skill Verification** list, and an observable-only **Culture Fit** profile.
4. Matches the candidate against the job's parsed requirements, producing a **Fit Score**, per-requirement coverage (direct / adjacent / missing), and an evidence-weighted **Time-to-Productivity** estimate.
5. Runs a deterministic **fairness audit** comparing outcomes across any self-reported demographic groups.
6. Answers natural-language recruiter questions through the **AI Recruiter Copilot**, which is deterministic-by-default and only ever uses the LLM to rephrase already-computed facts — a built-in grounding validator discards any AI phrasing that misattributes a fact, so the deterministic answer is always the fallback of last resort.

---

## Features

### Evidence-Based Engineering Scorecard
17 explainable dimensions — Programming, Problem Solving, Backend, Frontend, AI/ML, Cloud, DevOps, System Design, Code Quality, Documentation, Testing, Open Source, Collaboration, Ownership, Learning Velocity, Consistency, Project Complexity. Each carries score, confidence, evidence, reasoning, and suggestions. The **overall score is confidence-weighted** across dimensions — a dimension with little evidence automatically contributes less, rather than using a hand-picked importance weight.

### Evidence-Based Skill Verification
No skill is shown as a bare percentage. Every verified skill lists the repositories, byte-count of code, frameworks, last-active date, and (if present) resume corroboration behind its score.

### Explainable Culture Fit
Observable-signal-only: collaboration (forks received, org membership), documentation habits, ownership language and tenure, consistency of activity, initiative (side projects, hackathons), maintainer behaviour, technical breadth vs. depth. Personality is never inferred.

### AI Recruiter Copilot
Natural-language Q&A — "Find strong backend engineers," "Compare Candidate A vs Candidate B," "Explain why this candidate ranks higher," "What skills are missing for this JD?" Intent routing and fact retrieval are deterministic; the LLM only rephrases retrieved facts, and a post-hoc grounding check rejects any AI phrasing that attributes a fact to the wrong candidate, falling back to the deterministic (always-correct) answer.

### Time-to-Productivity
A hard time range (hours/days/sprints), not a single fake-precision number, derived from each requirement's coverage status, the candidate's evidenced skill strength, and their learning-velocity score. Every constant (sprint length, ramp-up ranges) is a named, documented assumption in `app/scoring/ttp.py`.

### Fairness Audit
Compares mean fit-score between any self-reported demographic group and the rest of the pool, and flags rank concentration in the bottom half. No ML bias classifier — the previous implementation ran a 1.6GB zero-shot NLI model against rationale text that is now 100% numeric and structurally cannot carry demographic language, so it was replaced with a direct, inspectable statistical comparison.

### Resume Parsing
Rules-based extraction (contact info, links, a 34-term skill taxonomy, years of experience) always runs and is instant. An optional LLM pass structures education, experience, projects, certifications, hackathons, and internships — strictly grounded to resume text, never inferred.

### GitHub Integration
Server-side, byte-level mining: languages by bytes (not just primary language), frameworks (detected from repo metadata), CI/test/docs presence (with a `GITHUB_TOKEN`), stars/forks/followers as OSS signal, push recency, and per-repo structural complexity. Degrades honestly — if GitHub is rate-limited or the user doesn't exist, the evidence object says so explicitly (`fetched_ok: false` + a note) rather than fabricating data.

### Codeforces Integration
Rating trajectory, contest consistency, comfort/struggle difficulty zones, tag gaps, and an honest mentor-style verdict. Handles are normalized from bare handles, `@handle`, or full profile URLs.

---

## Architecture

```
Browser (React)
   │  Supabase JWT on every request (axios interceptor)
   ▼
FastAPI backend
   ├─ auth.py            Supabase JWT verification (HS256 + JWKS RS256/ES256)
   ├─ config.py          Centralized environment configuration
   ├─ services/
   │   ├─ llm.py               Hugging Face Inference Providers client (Qwen 2.5)
   │   ├─ github_analyzer.py   Server-side byte-level GitHub miner
   │   ├─ resume_parser.py     Rules + optional LLM resume structuring
   │   ├─ codeforces_analyzer.py
   │   ├─ jd_parser.py
   │   ├─ skill_adjacency.py   Hand-curated skill transferability graph
   │   └─ persistence.py       Supabase-backed store, in-memory dev fallback
   ├─ scoring/            The scoring engine (see below)
   ├─ agents/
   │   ├─ recruiter_copilot.py  Deterministic Q&A + grounded LLM rephrasing
   │   └─ bias_auditor.py       Deterministic fairness audit
   └─ main.py             Route handlers, rate limiting, CORS
   │
   ▼
Supabase (Postgres)   jobs / candidates / analyses (JSON payload columns)
Hugging Face Router   Qwen/Qwen2.5-7B-Instruct (OpenAI-compatible /v1/chat/completions)
GitHub REST API       (optionally authenticated via GITHUB_TOKEN)
Codeforces API
```

### The scoring engine (`backend/app/scoring/`)

- `common.py` — normalizers (log/linear scaling, recency decay) and the skill taxonomy shared by every other module.
- `skills.py` — turns GitHub language bytes + resume claims into `VerifiedSkill` objects, each with evidence.
- `dimensions.py` — the 17 dimension scorers, each a pure function of evidence.
- `culture.py` — culture-fit signals derived from the dimension scores plus resume-only initiative signals.
- `job.py` — job description → structured requirements (61-term taxonomy, word-boundary matched, plus optional LLM extraction for requirements outside the taxonomy — grounded to the JD text).
- `ttp.py` — evidence-based, reproducible time-to-productivity estimation.
- `engine.py` — orchestrates the above into an `EngineeringScorecard` and, per job, a `MatchResult`.

Every function here is deterministic and side-effect-free (the one exception — LLM-based resume/JD enrichment — degrades to its rules-only result if the LLM is unavailable), which is why the backend test suite can assert exact reproducibility.

---

## Tech Stack

**Backend:** Python 3.11, FastAPI, Pydantic v2, `python-jose` (JWT), `httpx`, `requests`, `pypdf`, Supabase Python client, pytest.

**Frontend:** React 18, Vite 5, React Router 6, Axios, `@supabase/supabase-js`.

**AI:** Hugging Face Inference Providers, `Qwen/Qwen2.5-7B-Instruct` (OpenAI-compatible chat completions endpoint). Every LLM call has a deterministic fallback — the product is fully functional with `LLM_ENABLED=false` or no `HF_API_TOKEN` set.

**Data:** Supabase (Postgres) for jobs, candidates, and match results (JSON payload columns for the nested evidence/scorecard objects). Falls back transparently to in-process storage if the schema migration hasn't been applied yet, so local development never depends on a manual SQL step.

---

## Folder Structure

```
backend/
  app/
    agents/            recruiter_copilot.py, bias_auditor.py
    scoring/           the scoring engine (common, skills, dimensions, culture, job, ttp, engine)
    services/          llm, github_analyzer, resume_parser, codeforces_analyzer, jd_parser,
                        skill_adjacency, persistence
    auth.py            Supabase JWT verification
    config.py          environment configuration
    models.py           domain model (Evidence, GithubEvidence, ResumeEvidence,
                        EngineeringScorecard, MatchResult, FairnessReport, ...)
    schemas/api.py      thin request/response wrappers not already covered by models.py
    main.py             FastAPI routes
  tests/                pytest suite for the scoring engine, copilot, and services
  sql/supabase_init.sql schema migration (run manually in the Supabase SQL editor)
frontend/
  src/
    api/client.js       typed API client (auto-attaches the Supabase access token)
    components/         ScorecardBreakdown, SkillEvidenceList, CultureFitPanel,
                        CopilotPanel, SkillRadarChart, AdjacencyPathGraph, ...
    pages/              Dashboard, Candidates, Analyze, Copilot, Profile, Settings, Login
    context/            Supabase auth context
README.md
```

---

## Installation

### 1. Backend

```bash
cd backend
python3.11 -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` (see [Environment Variables](#environment-variables)), then run the Supabase migration once (see below), then:

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

### 2. Supabase schema migration

The app runs against a live Postgres schema (`jobs`, `candidates`, `analyses`). Open the Supabase SQL editor for your project and run `backend/sql/supabase_init.sql` — every statement is additive and idempotent, safe to run against a database that already has data.

If you skip this step, the backend still runs: persistence transparently falls back to in-process storage (with a logged warning) so local development is never blocked, but nothing survives a restart until the migration is applied.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://127.0.0.1:5173

---

## Environment Variables

### `backend/.env`

| Variable | Required | Purpose |
|---|---|---|
| `SUPABASE_JWT_SECRET` | Yes | Verifies Supabase-issued JWTs (HS256). Startup fails without it. |
| `SUPABASE_URL` | Yes | Supabase project URL — persistence and JWKS (RS256/ES256) lookup. |
| `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_ANON_KEY` | Yes (one of) | Supabase client credential for persistence. |
| `HF_API_TOKEN` | No | Hugging Face token. Without it, `LLM_ENABLED` is effectively false and every AI feature uses its deterministic fallback. |
| `HF_MODEL` | No | Defaults to `Qwen/Qwen2.5-7B-Instruct`. Any Qwen2.5/Qwen3 instruct model hosted on the HF router works. |
| `HF_BASE_URL` | No | Defaults to `https://router.huggingface.co/v1`. |
| `GITHUB_TOKEN` | No (strongly recommended) | Raises GitHub's unauthenticated 60 req/hr limit to 5000/hr and unlocks CI/test/docs structural analysis. Without it, Code Quality/Documentation/Testing dimensions score a low-confidence placeholder. |
| `CORS_ORIGINS` | No | Comma-separated allowed origins. Defaults to localhost. |
| `MAX_UPLOAD_BYTES` | No | Default 5MB. |
| `RATE_LIMIT_REQUESTS_PER_WINDOW` / `RATE_LIMIT_WINDOW_SECONDS` | No | Default 120 req / 60s, with per-route overrides in `main.py`. |

### `frontend/.env`

| Variable | Required | Purpose |
|---|---|---|
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` | Yes | Supabase auth (login, session, token issuance). |
| `VITE_API_BASE_URL` | No | Defaults to `http://127.0.0.1:8000`. Point at your deployed backend in production. |

---

## API Overview

All routes except `/health` and `/ping` require `Authorization: Bearer <supabase-jwt>`.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/jobs` | Parse a job description into structured requirements, persist it |
| `GET` | `/jobs` | List your jobs |
| `GET` | `/jobs/{job_id}` | Fetch a job |
| `POST` | `/jobs/extract-jd-pdf` | Extract text + suggested title from a JD PDF |
| `POST` | `/candidates` | Mine GitHub, parse resume, fetch Codeforces, score — in one call |
| `GET` | `/candidates` | List all candidates with their scorecards |
| `GET` | `/candidates/{candidate_id}` | Fetch one candidate + scorecard |
| `POST` | `/candidates/extract-resume-pdf` | Fast rules-only resume preview (upload feedback) |
| `POST` | `/match` | Score persisted candidates against a job, persist the results |
| `GET` | `/match/{job_id}` | Reload persisted match results for a job |
| `GET` | `/analyses` | Cross-job view of every persisted match result (dashboard) |
| `GET` | `/audit/{job_id}` | Fairness audit for a job's match results |
| `POST` | `/copilot` | Ask the AI Recruiter Copilot a natural-language question |
| `GET` | `/codeforces/{handle}/analysis` | Standalone Codeforces analysis |

---

## Development Guide

Backend: standard FastAPI dev loop — `uvicorn app.main:app --reload`, edit, the reloader picks it up.

Frontend: `npm run dev`, Vite HMR.

The scoring engine is pure and deterministic (see [Architecture](#the-scoring-engine-backendappscoring)) — when changing a dimension or the matching logic, add/update the corresponding test in `backend/tests/` rather than only spot-checking via the API.

---

## Testing

```bash
cd backend
source .venv311/bin/activate
pytest tests/ -v
```

40 tests covering: scoring normalizers, skill verification (including a regression test for a real bug caught during development — AI/ML frameworks like PyTorch were briefly miscategorized into a generic "framework" bucket, zeroing out the AI/ML dimension), the full scoring engine's determinism and confidence-weighting, time-to-productivity bounds and monotonicity, job-description parsing, Codeforces handle normalization, resume parsing, the fairness audit's disparity math, and the recruiter copilot's deterministic intent handlers (including the grounding validator that rejects LLM misattribution).

Tests are network-free by design — the LLM client is forced "not ready" via an autouse fixture, so the suite exercises the deterministic paths every request can fall back to.

No frontend test suite exists yet (see Roadmap) — `npm run build` is the current safety net for compile/import errors.

---

## Deployment Guide

- **Backend:** any ASGI host (Fly.io, Render, Railway, a container on Cloudflare/AWS/GCP). Set the environment variables above; run the Supabase migration first.
- **Frontend:** static hosting (Cloudflare Pages, Vercel, Netlify) — `npm run build` outputs `frontend/dist`. Set `VITE_API_BASE_URL` to your deployed backend URL and `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`.
- **CORS:** set `CORS_ORIGINS` on the backend to your deployed frontend origin(s); `*.pages.dev` preview URLs are allowed automatically via a regex match.

---

## Known Limitations

- Scoring is evidence-based and deterministic, not a trained model — it is reproducible and explainable by design, not a prediction calibrated against real hiring outcomes.
- GitHub evidence quality depends on public profile completeness; without `GITHUB_TOKEN`, structural analysis (CI/tests/docs) is unavailable and those dimensions report a low-confidence placeholder rather than a real score.
- The AI Recruiter Copilot's LLM-assisted phrasing is rejected outright (falling back to deterministic text) whenever it can't be verified against the underlying facts — so "AI-assisted" answers are intentionally rarer than a naive LLM wrapper would produce.
- Fairness audit compares only self-reported demographic fields a recruiter chooses to enter; it cannot detect bias along attributes nobody records.

## Future Roadmap

- Frontend test suite (component + integration tests).
- Persisted per-owner job/candidate list pagination (currently returns full lists).
- Richer LLM-assisted JD requirement extraction with multi-pass grounding checks.
- Background job queue for GitHub mining on very large repositories, rather than inline request-time fetching.
- Team-level benchmark dashboards across multiple recruiters' pipelines.
