import json
from collections import Counter
from typing import Tuple, List

import requests
import streamlit as st

from app.models import CandidateProfile, PlatformSignal, SkillGraph, SkillNode


GITHUB_API_BASE = "https://api.github.com"
FASTAPI_BASE = "http://127.0.0.1:8000"


def fetch_github_repos(username: str) -> List[dict]:
    url = f"{GITHUB_API_BASE}/users/{username}/repos?per_page=100&sort=updated"
    resp = requests.get(url, headers={"Accept": "application/vnd.github+json"}, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text[:200]}")
    return resp.json()  # type: ignore[return-value]


def summarise_github(username: str) -> Tuple[Counter, int, int]:
    """Return (language_counts, total_stars, repo_count) for a user."""
    repos = fetch_github_repos(username)
    lang_counter: Counter = Counter()
    total_stars = 0

    for repo in repos:
        lang = repo.get("language") or "Unknown"
        lang_counter[lang] += 1
        total_stars += int(repo.get("stargazers_count") or 0)

    return lang_counter, total_stars, len(repos)


def build_skill_graph_from_github(username: str) -> Tuple[CandidateProfile, SkillGraph, dict]:
    languages, total_stars, repo_count = summarise_github(username)

    candidate = CandidateProfile(
        id=username,
        name=username,
        headline="GitHub candidate",
        summary=f"Open-source footprint: {repo_count} public repos, {total_stars} total stars.",
        platforms=[
            PlatformSignal(
                platform="github",
                url=f"https://github.com/{username}",
                metadata={
                    # Human-readable list for display/debugging.
                    "languages": ",".join(sorted(languages.keys())),
                    # Machine-readable mapping used by the backend for scoring.
                    "languages_json": json.dumps(dict(languages)),
                    "total_stars": str(total_stars),
                    "repo_count": str(repo_count),
                },
            )
        ],
        demographics={},
    )

    skills: List[SkillNode] = []

    # Map languages to coarse skill scores
    if repo_count == 0:
        skills.append(
            SkillNode(
                name="limited public signal",
                score=0.4,
                evidence=["No public repositories found on GitHub."],
            )
        )
    else:
        max_repos = max(languages.values()) if languages else 1
        for lang, count in languages.items():
            if lang == "Unknown":
                continue
            usage_ratio = count / max_repos
            # Scale score by how frequently the language appears
            score = 0.6 + 0.35 * usage_ratio
            skills.append(
                SkillNode(
                    name=lang.lower(),
                    score=score,
                    evidence=[
                        f"Language {lang} used in {count} repos with {total_stars} total stars across the profile.",
                    ],
                )
            )

        if repo_count >= 5:
            skills.append(
                SkillNode(
                    name="open-source collaboration",
                    score=0.7,
                    evidence=[
                        f"Has {repo_count} public repos, indicating ongoing collaboration and code sharing.",
                    ],
                )
            )

    # Learning velocity heuristic: depends on diversity, repos, and stars.
    # This is intentionally sensitive so different GitHub profiles clearly
    # show different learning speeds in the UI.
    import math

    diversity = len({s.name for s in skills})
    diversity_factor = diversity / 8.0  # more unique skills => higher velocity

    repo_factor = math.log1p(repo_count) / 5.0  # ~0-1 as repos grow
    star_factor = math.log1p(total_stars) / 8.0  # ~0-1 as stars grow

    base_velocity = 0.25 + 0.25 * min(diversity_factor, 1.0)
    base_velocity += 0.25 * min(repo_factor, 1.0)
    base_velocity += 0.25 * min(star_factor, 1.0)

    learning_velocity = max(0.0, min(1.0, base_velocity))

    graph = SkillGraph(candidate_id=candidate.id, skills=skills, learning_velocity=learning_velocity)
    raw_summary = {
        "languages": dict(languages),
        "total_stars": total_stars,
        "repo_count": repo_count,
    }
    return candidate, graph, raw_summary


def call_backend_pipeline(
    jd_title: str,
    jd_description: str,
    candidate: CandidateProfile,
) -> Tuple[dict, dict, str, List[str]]:
    """Send data to the FastAPI backend and return (job, match, copilot_answer, bias_flags).

    This wires the Streamlit app into the SkillSphere backend instead of running
    matching locally, so the UI and API stay in sync.
    """

    job_id = f"streamlit-{candidate.id}"

    # 1) Create / overwrite the job definition in the backend
    job_payload = {"job_id": job_id, "title": jd_title, "description": jd_description}
    r_job = requests.post(f"{FASTAPI_BASE}/jobs", json=job_payload, timeout=10)
    r_job.raise_for_status()
    job = r_job.json()

    # 2) Register candidate with the backend (it will build its own skill graph)
    c_payload = {
        "candidate_id": candidate.id,
        "name": candidate.name,
        "headline": candidate.headline,
        "summary": candidate.summary,
        "platforms": [
            {"platform": p.platform, "url": p.url, "metadata": p.metadata}
            for p in candidate.platforms
        ],
        "demographics": candidate.demographics,
    }
    r_cand = requests.post(f"{FASTAPI_BASE}/candidates", json=c_payload, timeout=10)
    r_cand.raise_for_status()

    # 3) Run matching for this single candidate
    match_payload = {"job_id": job_id, "candidate_ids": [candidate.id]}
    r_match = requests.post(f"{FASTAPI_BASE}/match", json=match_payload, timeout=10)
    r_match.raise_for_status()
    match_resp = r_match.json()
    ranked = match_resp.get("ranked", [])
    if not ranked:
        raise RuntimeError("Backend returned no ranked candidates.")
    match = ranked[0]

    # 4) Call co-pilot for a natural-language explanation
    r_cop = requests.post(
        f"{FASTAPI_BASE}/copilot",
        json={"job_id": job_id, "candidate_id": candidate.id},
        timeout=10,
    )
    r_cop.raise_for_status()
    copilot_answer = r_cop.json().get("answer", "")

    # 5) Fetch bias audit info for this job and candidate
    r_audit = requests.get(f"{FASTAPI_BASE}/audit/{job_id}", timeout=10)
    r_audit.raise_for_status()
    audit = r_audit.json()
    bias_flags: List[str] = []
    for entry in audit.get("entries", []):
        if entry.get("candidate_id") == candidate.id:
            bias_flags = entry.get("bias_flags", [])
            break

    return job, match, copilot_answer, bias_flags


def skill_graph_to_dot(candidate_name: str, graph: SkillGraph) -> str:
    """Render the SkillGraph as a simple network diagram in Graphviz DOT.

    Candidate sits in the centre with edges to each skill, sized/coloured by score.
    """

    # Clamp and map scores to colours/sizes
    def norm(score: float) -> float:
        return max(0.0, min(1.0, score))

    lines: list[str] = []
    lines.append("digraph SkillGraph {")
    lines.append("  rankdir=LR;")
    lines.append("  node [fontname=Helvetica];")

    center_label = f"{candidate_name}\\n(learning v={graph.learning_velocity:.2f})"
    lines.append(
        f"  candidate [label=\"{center_label}\", shape=box, style=filled, fillcolor=lightblue];"
    )

    for idx, skill in enumerate(graph.skills):
        s = norm(skill.score)
        # Colour gradient: low = lightgrey, high = green.
        if s > 0.75:
            color = "#66bb6a"  # strong
        elif s > 0.5:
            color = "#ffeb3b"  # medium
        else:
            color = "#ef9a9a"  # weak

        size = 10 + 8 * s
        node_name = f"skill_{idx}"
        label = f"{skill.name}\\n({skill.score:.2f})"
        lines.append(
            f"  {node_name} [label=\"{label}\", shape=circle, style=filled, fillcolor=\"{color}\", fontsize={size:.1f}];"
        )
        lines.append(f"  candidate -> {node_name};")

    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    st.set_page_config(page_title="SkillSphere – GitHub Signal Screener", layout="wide")
    st.title("SkillSphere – GitHub Signal Screener")
    st.write(
        """Defeat AI resume spam by looking at real work.

Paste a real job description, enter a GitHub username, and SkillSphere will:

1. Analyse the candidate's GitHub footprint (languages, repos, stars).
2. Infer a Skill Graph + learning velocity.
3. Match the candidate to the role with an explainable score.
4. Show statements of the form: *We believe this candidate has X because Y.*
        """
    )

    with st.sidebar:
        st.header("Inputs")
        jd_title = st.text_input("Job title", value="Backend Engineer (Python/LLMs)")
        jd_description = st.text_area(
            "Job description",
            value=(
                "We are looking for a backend engineer with strong Python, FastAPI, "
                "and machine learning experience, plus good communication and ownership."
            ),
            height=160,
        )
        github_username = st.text_input("GitHub username", value="torvalds")
        run_button = st.button("Run evaluation", type="primary")

    col_left, col_right = st.columns(2)

    if run_button:
        if not github_username.strip():
            st.error("Please provide a GitHub username.")
            return

        with st.spinner("Contacting GitHub, backend API, and analysing signals..."):
            try:
                candidate, graph, raw_summary = build_skill_graph_from_github(github_username.strip())
                job, match, copilot_answer, bias_flags = call_backend_pipeline(
                    jd_title, jd_description, candidate
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"Failed to analyse profile: {e}")
                return

        with col_left:
            st.subheader("GitHub signal snapshot")
            st.write(f"Candidate: **{candidate.name}**")
            st.write(
                f"Public repos: **{raw_summary['repo_count']}**, "
                f"Total stars: **{raw_summary['total_stars']}**"
            )

            if raw_summary["repo_count"] == 0:
                st.warning("No public repositories found for this user.")
            else:
                st.markdown("**Top languages by repo count:**")
                lang_items = sorted(
                    raw_summary["languages"].items(), key=lambda kv: kv[1], reverse=True
                )
                for lang, count in lang_items:
                    st.write(f"- {lang}: {count} repos")

            st.markdown("**Raw summary (for debugging / judging):**")
            st.code(json.dumps(raw_summary, indent=2), language="json")

        with col_right:
            st.subheader("Role–candidate match (explainable)")
            st.markdown(f"**Match score:** {match.get('score', 0.0):.2f}")
            st.markdown(f"**Learning velocity:** {graph.learning_velocity:.2f}")

            ttp_poms = match.get("time_to_productivity_pomodoros")
            ttp_hours = match.get("time_to_productivity_hours")
            ttp_sprints = match.get("time_to_productivity_sprints")
            if ttp_poms is not None:
                st.markdown(
                    "**Estimated time-to-productivity:** "
                    f"{ttp_poms:.1f} pomodoros (~{(ttp_hours or 0):.1f}h, "
                    f"~{(ttp_sprints or 0):.2f} sprints)"
                )

            ttp_expl = match.get("time_to_productivity_explanation")
            if ttp_expl:
                st.markdown(f"**What this means:** {ttp_expl}")

            # Derive matched vs missing skills for explanation
            role_skill_names = [
                (r.get("name") or "").lower() for r in job.get("requirements", [])
            ]
            candidate_skill_names = [s.name.lower() for s in graph.skills]

            matched_skills = [s for s in role_skill_names if s in candidate_skill_names]
            missing_skills = [s for s in role_skill_names if s not in candidate_skill_names]

            st.markdown("**Matched skills (core requirements):**")
            if matched_skills:
                for s_name in matched_skills:
                    st.write(f"- {s_name}")
            else:
                st.write("- (none matched explicitly; relying on adjacent skills)")

            st.markdown("**Missing or weak skills:**")
            if missing_skills:
                for s_name in missing_skills:
                    st.write(f"- {s_name}")
            else:
                st.write("- All core textual requirements appear covered in the inferred skills.")

            st.markdown("**Why this score?**")
            st.write(match.get("explanation", "(no explanation returned by backend)"))

            direct_reqs = match.get("direct_matches") or []
            adj_support = match.get("adjacent_support") or []
            if direct_reqs:
                st.markdown("**Directly satisfied requirements:**")
                for r in sorted(set(direct_reqs)):
                    st.write(f"- {r}")
            if adj_support:
                st.markdown("**Adjacency-based potential (skill-distance reasoning):**")
                for desc in adj_support:
                    st.write(f"- {desc}")

            st.markdown("**We believe this candidate has X because Y:**")
            for node in graph.skills:
                if not node.evidence:
                    continue
                st.write(f"- {node.name}: {node.evidence[0]}")

            st.markdown("**Skill Graph (visual):**")
            dot = skill_graph_to_dot(candidate.name, graph)
            st.graphviz_chart(dot)

            st.markdown("**Recruiter Co-Pilot explanation (from backend):**")
            if copilot_answer:
                st.code(copilot_answer)
            else:
                st.write("(No co-pilot answer returned.)")

            if bias_flags:
                st.markdown("**Bias audit flags (backend):**")
                for reason in bias_flags:
                    st.write(f"- {reason}")
            else:
                st.markdown("**Bias audit:** no fairness concerns flagged for this candidate.")

    else:
        with col_left:
            st.info("Fill in the sidebar and click *Run evaluation* to see results.")
        with col_right:
            st.info("This panel will show match scores, matched/missing skills, and explanations.")


if __name__ == "__main__":
    main()
