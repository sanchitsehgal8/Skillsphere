import json
from collections import Counter
from typing import Tuple, List

import requests
import streamlit as st

from app.agents.job_intelligence import JobIntelligenceAgent
from app.agents.matching import MatchingAndRankingAgent
from app.models import CandidateProfile, PlatformSignal, SkillGraph, SkillNode


GITHUB_API_BASE = "https://api.github.com"


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
                    "languages": ",".join(sorted(languages.keys())),
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

    # Learning velocity heuristic: more repos + more languages => faster
    diversity = len({s.name for s in skills})
    base_velocity = 0.4 + 0.05 * min(diversity, 6) + 0.05 * min(repo_count / 10.0, 2.0)
    learning_velocity = max(0.0, min(1.0, base_velocity))

    graph = SkillGraph(candidate_id=candidate.id, skills=skills, learning_velocity=learning_velocity)
    raw_summary = {
        "languages": dict(languages),
        "total_stars": total_stars,
        "repo_count": repo_count,
    }
    return candidate, graph, raw_summary


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

    job_agent = JobIntelligenceAgent()
    match_agent = MatchingAndRankingAgent()

    if run_button:
        if not github_username.strip():
            st.error("Please provide a GitHub username.")
            return

        with st.spinner("Contacting GitHub and analysing signals..."):
            try:
                role_graph = job_agent.build_role_graph(
                    job_id="demo-job", title=jd_title, description=jd_description
                )
                candidate, graph, raw_summary = build_skill_graph_from_github(github_username.strip())
                scores = match_agent.rank_candidates(role_graph.job, [graph])
                match = scores[0]
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
            st.markdown(f"**Match score:** {match.score:.2f}")
            st.markdown(f"**Learning velocity:** {graph.learning_velocity:.2f}")

            # Derive matched vs missing skills for explanation
            role_skill_names = [r.name.lower() for r in role_graph.core_requirements]
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
            st.write(match.explanation)

            st.markdown("**We believe this candidate has X because Y:**")
            for node in graph.skills:
                if not node.evidence:
                    continue
                st.write(f"- {node.name}: {node.evidence[0]}")

    else:
        with col_left:
            st.info("Fill in the sidebar and click *Run evaluation* to see results.")
        with col_right:
            st.info("This panel will show match scores, matched/missing skills, and explanations.")


if __name__ == "__main__":
    main()
