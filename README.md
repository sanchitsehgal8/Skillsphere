# SkillSphere

SkillSphere is a full-stack talent intelligence platform for recruiter workflows. It combines a React frontend with a FastAPI backend and an agent-style scoring pipeline to analyze candidate fit beyond keyword matching.

---

## Current Product Scope

### Frontend (React + Vite)

- Dashboard, Candidates, Analyze, Profile, and Settings pages
- Analyze workflow supports **multiple candidates** in separate cards
- Upload and parse:
  - JD PDF (auto-fills job description)
  - Resume PDF per candidate (extracts text, inferred skills, and years of experience)
- Candidate enrichment from:
  - GitHub repositories/languages/stars
  - Optional Codeforces handle
  - Resume-derived signals
- Analysis results on the **same Analyze page** (form + results view)
- Explainable AI section with weighted metric breakdown, confidence, strengths, gaps, and recommendations
- Adjacency path visualization for transferable skills
- CSV export support on dashboard/analyze views

### Backend (FastAPI)

- Agent pipeline:
  - Job Intelligence Agent
  - Talent Scout Agent
  - Skill Graph Builder Agent
  - Matching & Ranking Agent
  - Bias Auditor Agent
  - Recruiter Copilot Agent
- Score combines:
  - Present Skill Fit (cosine alignment)
  - Learning Velocity
  - Productivity Readiness (TTP-derived)
- Structured XAI response included in `/match`
- Fairness audit endpoint and recruiter copilot summaries
- Codeforces analytics endpoint with profile/problem/contest insights

> Note: storage is currently in-memory (demo/prototype mode).

---

## Repository Structure

```text
backend/
  app/
    agents/
    services/
    schemas/
    main.py
  streamlit_app.py
frontend/
  src/
    pages/
    components/
README.md
```

---

## Quick Start

## 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend:
- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

## 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:
- App: http://127.0.0.1:5173

If needed, set `VITE_API_BASE` in frontend env to point to backend (defaults to `http://127.0.0.1:8000`).

---

## Core API Endpoints

### Jobs

- `POST /jobs` — create job and role graph
- `GET /jobs/{job_id}` — fetch job
- `POST /jobs/extract-jd-pdf` — extract text + suggested title from JD PDF

### Candidates

- `POST /candidates` — create candidate and build skill graph
- `GET /candidates/{candidate_id}` — fetch candidate
- `POST /candidates/extract-resume-pdf` — parse resume PDF, infer skills + years experience

### Matching + Explainability

- `POST /match` — rank candidates and return:
  - score
  - explanation
  - time-to-productivity metrics
  - direct matches
  - adjacency support
  - XAI block (components, confidence, strengths/gaps/recommendations)
- `GET /audit/{job_id}` — fairness audit output
- `POST /copilot` — natural-language recruiter summary

### Codeforces

- `GET /codeforces/{handle}/analysis` — rating trajectory, consistency, tag gaps, mentor-style verdict

---

## End-to-End Flow (UI)

1. Open **Analyze Candidate** page
2. Provide job title/description (or upload JD PDF)
3. Add one or more candidate cards
4. For each candidate:
   - GitHub username (required)
   - Codeforces URL/handle (optional)
   - Resume PDF (optional, but recommended)
5. Click **Analyze Candidate**
6. Review results on the same page:
   - score + TTP snapshot
   - role fit + adjacency graph
   - Codeforces benchmark (if available)
   - XAI breakdown
   - raw logs (advanced)

---

## Dependencies

Backend (`backend/requirements.txt`):
- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `requests`
- `pypdf`
- `streamlit`
- `transformers`

Frontend (`frontend/package.json`):
- `react`
- `react-dom`
- `react-router-dom`
- `axios`
- `vite`

---

## Optional Streamlit Prototype

```bash
cd backend
source .venv/bin/activate
streamlit run streamlit_app.py
```

---

## Known Limitations

- In-memory backend state resets on server restart
- Heuristic scoring (interpretable and deterministic) rather than a trained model
- External data quality depends on public profile availability (GitHub/Codeforces)

---

## Roadmap Ideas

- Persistent DB + vector store
- Async background analysis jobs
- Richer calibration/validation for learning velocity
- Team-level benchmark dashboards
- LLM-assisted recruiter co-pilot with grounded retrieval