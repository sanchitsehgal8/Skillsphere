# SkillSphere

## Overview

SkillSphere is an agentic, AI-powered talent intelligence engine that thinks like your best recruiter. Instead of blindly keyword-matching resumes, it uses specialised AI agents to:

- Understand job descriptions as structured requirement graphs.
- Scout public signals across platforms (GitHub, LeetCode, LinkedIn, Kaggle, portfolios).
- Build a Skill DNA graph per candidate and estimate learning velocity.
- Rank candidates by a mix of present fit and growth potential.
- Run a fairness pass to surface potential demographic bias.
- Provide a recruiter co-pilot interface that explains every recommendation.

This repository currently ships a fully runnable backend prototype implemented in Python with FastAPI.

## Backend (FastAPI) – `backend/`

### Key Components

- Job Intelligence Agent: parses a free-form JD into a role requirement graph.
- Talent Scout Agent: simulates evidence gathering across platforms.
- Skill Graph Builder Agent: creates candidate Skill DNA and learning velocity.
- Matching & Ranking Agent: computes cosine-like similarity between roles and skills.
- Bias Auditor Agent: runs a lightweight fairness audit over ranked candidates.
- Recruiter Co-Pilot Agent: returns readable explanations for candidates and shortlists.

All logic is deterministic and runs locally without external APIs; the architecture is designed so you can later plug in real LLMs, vector DBs, and platform APIs.

## Getting Started

### 1. Create and activate a virtual environment (recommended)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # on macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the API server

```bash
uvicorn app.main:app --reload
```

The API will be available at: http://127.0.0.1:8000
Interactive docs (Swagger UI) are at: http://127.0.0.1:8000/docs

## Example Flow (End-to-End)

1. Create a job description:

	 ```bash
	 curl -X POST http://127.0.0.1:8000/jobs \
		 -H "Content-Type: application/json" \
		 -d '{
			 "job_id": "backend-engineer-1",
			 "title": "Backend Engineer (Python/LLMs)",
			 "description": "We are looking for a backend engineer with strong Python, FastAPI, and machine learning experience, plus good communication and ownership."
		 }'
	 ```

2. Create one or more candidates:

	 ```bash
	 curl -X POST http://127.0.0.1:8000/candidates \
		 -H "Content-Type: application/json" \
		 -d '{
			 "candidate_id": "cand-1",
			 "name": "Aisha Dev",
			 "headline": "Backend + ML Engineer",
			 "summary": "Works on LLM tooling and high-scale APIs.",
			 "platforms": [
				 {"platform": "github", "metadata": {"top_repo": "llm-routing-service"}},
				 {"platform": "leetcode", "metadata": {"rating": "advanced"}},
				 {"platform": "linkedin", "metadata": {}}
			 ],
			 "demographics": {"gender": "female"}
		 }'
	 ```

3. Run matching for the job and candidates:

	 ```bash
	 curl -X POST http://127.0.0.1:8000/match \
		 -H "Content-Type: application/json" \
		 -d '{
			 "job_id": "backend-engineer-1",
			 "candidate_ids": ["cand-1"]
		 }'
	 ```

4. Inspect the bias audit log:

	 ```bash
	 curl http://127.0.0.1:8000/audit/backend-engineer-1
	 ```

5. Ask the Recruiter Co-Pilot for an explanation:

	 ```bash
	 curl -X POST http://127.0.0.1:8000/copilot \
		 -H "Content-Type: application/json" \
		 -d '{
			 "job_id": "backend-engineer-1",
			 "candidate_id": "cand-1"
		 }'
	 ```

This will return a natural-language-style summary of the candidate, their Skill DNA, learning velocity, match score, and any fairness flags.

## Next Steps

- Swap heuristic components for real LLMs using LangGraph or similar.
- Plug in actual platform APIs (GitHub, LeetCode, LinkedIn, Kaggle, portfolios).
- Replace in-memory stores with a database and vector store (e.g., FAISS).
- Extend the fairness and DEI auditing layer with more robust metrics.