"""Deep, server-side GitHub evidence miner.

Replaces the shallow client-side fetch (languages + repo count from one
unauthenticated page). Runs on the backend so it can use ``GITHUB_TOKEN`` for a
5000/hr budget and inspect repository structure (languages by bytes, CI, tests,
docs, recency, OSS signal).

Everything is best-effort and non-throwing: if GitHub is unreachable or rate
limited, ``fetched_ok`` is ``False`` and a ``note`` explains why. We never
fabricate structural signals we could not observe.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.models import GithubEvidence, RepoInsight

logger = logging.getLogger("skillsphere.github")

# Framework / tool fingerprints keyed by substrings found in topics, repo names,
# descriptions and language keys.
_FRAMEWORK_HINTS = {
    "react": "React", "next": "Next.js", "vue": "Vue", "nuxt": "Nuxt",
    "angular": "Angular", "svelte": "Svelte", "django": "Django",
    "flask": "Flask", "fastapi": "FastAPI", "express": "Express",
    "spring": "Spring", "rails": "Rails", "laravel": "Laravel",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "keras": "Keras",
    "scikit": "scikit-learn", "pandas": "pandas", "numpy": "NumPy",
    "kubernetes": "Kubernetes", "docker": "Docker", "terraform": "Terraform",
    "graphql": "GraphQL", "kafka": "Kafka", "spark": "Spark",
    "flutter": "Flutter", "android": "Android", "swift": "Swift",
    "node": "Node.js", "postgres": "PostgreSQL", "mongodb": "MongoDB",
    "redis": "Redis", "llm": "LLM", "langchain": "LangChain",
}


def _headers() -> Dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "SkillSphere"}
    if settings.github_token:
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h


def _days_since(iso: Optional[str]) -> Optional[int]:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - dt).days)
    except (ValueError, TypeError):
        return None


def _years_between(iso: Optional[str]) -> float:
    d = _days_since(iso)
    return round(d / 365.25, 1) if d is not None else 0.0


def _detect_frameworks(blobs: List[str]) -> List[str]:
    hay = " ".join(b.lower() for b in blobs if b)
    found = {label for key, label in _FRAMEWORK_HINTS.items() if key in hay}
    return sorted(found)


class GithubAnalyzer:
    def __init__(self) -> None:
        self._base = settings.github_api.rstrip("/")
        self._authed = bool(settings.github_token)
        # Call budgets — deeper when authenticated.
        self._deep_lang = 15 if self._authed else 6
        self._deep_tree = 10 if self._authed else 0

    async def _get(self, client: httpx.AsyncClient, path: str, **params: Any) -> Any:
        resp = await client.get(f"{self._base}{path}", params=params or None)
        if resp.status_code == 404:
            raise ValueError("not-found")
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise ValueError("rate-limited")
        resp.raise_for_status()
        return resp.json()

    async def _list_repos(self, client: httpx.AsyncClient, username: str) -> List[dict]:
        repos: List[dict] = []
        for page in range(1, 4):  # up to 300 repos
            batch = await self._get(
                client, f"/users/{username}/repos",
                per_page=100, sort="pushed", page=page,
            )
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
        return repos

    async def _repo_languages(self, client: httpx.AsyncClient, full_name: str) -> Dict[str, int]:
        try:
            data = await self._get(client, f"/repos/{full_name}/languages")
            return {k: int(v) for k, v in data.items()} if isinstance(data, dict) else {}
        except (ValueError, httpx.HTTPError):
            return {}

    async def _repo_structure(
        self, client: httpx.AsyncClient, full_name: str, default_branch: str
    ) -> Dict[str, bool]:
        """One tree call → detect CI / tests / docs from the file listing."""
        try:
            data = await self._get(
                client, f"/repos/{full_name}/git/trees/{default_branch}", recursive="1"
            )
        except (ValueError, httpx.HTTPError):
            return {}
        paths = [t.get("path", "").lower() for t in (data.get("tree") or [])]
        joined = "\n".join(paths)
        return {
            "has_ci": ".github/workflows" in joined or ".gitlab-ci" in joined or ".circleci" in joined,
            "has_tests": any(
                seg in joined for seg in ("test/", "tests/", "__tests__", "spec/", "_test.", ".test.", ".spec.")
            ),
            "has_docs": any(
                p.startswith("readme") or p.startswith("docs/") or "documentation" in p for p in paths
            ),
        }

    async def analyze(self, username: str) -> GithubEvidence:
        username = (username or "").strip().lstrip("@")
        profile_url = f"https://github.com/{username}"
        ev = GithubEvidence(username=username, profile_url=profile_url)
        if not username:
            ev.note = "No GitHub username provided."
            return ev

        timeout = httpx.Timeout(connect=5.0, read=20.0, write=10.0, pool=20.0)
        try:
            async with httpx.AsyncClient(timeout=timeout, headers=_headers()) as client:
                user = await self._get(client, f"/users/{username}")
                repos_raw = await self._list_repos(client, username)
                try:
                    orgs = await self._get(client, f"/users/{username}/orgs")
                    ev.contributed_orgs = [o.get("login") for o in orgs if o.get("login")][:10]
                except (ValueError, httpx.HTTPError):
                    ev.contributed_orgs = []

                await self._populate(client, ev, user, repos_raw)
                ev.fetched_ok = True
                if not self._authed:
                    ev.note = "Unauthenticated GitHub access — set GITHUB_TOKEN for structural (CI/test/docs) analysis and higher rate limits."
        except ValueError as exc:
            ev.note = {
                "not-found": f"GitHub user '{username}' not found.",
                "rate-limited": "GitHub rate limit hit — set GITHUB_TOKEN to raise the limit.",
            }.get(str(exc), f"GitHub error: {exc}")
        except httpx.HTTPError as exc:
            ev.note = f"GitHub request failed: {exc}"
        return ev

    async def _populate(
        self, client: httpx.AsyncClient, ev: GithubEvidence, user: dict, repos_raw: List[dict]
    ) -> None:
        ev.name = user.get("name")
        ev.bio = user.get("bio")
        ev.company = user.get("company")
        ev.location = user.get("location")
        ev.hireable = user.get("hireable")
        ev.public_repos = int(user.get("public_repos") or 0)
        ev.followers = int(user.get("followers") or 0)
        ev.following = int(user.get("following") or 0)
        ev.account_created_at = user.get("created_at")
        ev.account_age_years = _years_between(user.get("created_at"))

        originals = [r for r in repos_raw if not r.get("fork")]
        forks = [r for r in repos_raw if r.get("fork")]
        ev.original_repo_count = len(originals)
        ev.forked_repo_count = len(forks)

        # Rank original repos: stars first, then recency.
        originals.sort(
            key=lambda r: (int(r.get("stargazers_count") or 0), r.get("pushed_at") or ""),
            reverse=True,
        )

        lang_repo_count: Dict[str, int] = {}
        push_days: List[int] = []
        topics_all: List[str] = []
        framework_blobs: List[str] = []

        # Concurrent deep fetches, bounded by a semaphore.
        sem = asyncio.Semaphore(6)

        async def enrich(repo: dict, idx: int) -> RepoInsight:
            full = repo.get("full_name") or f"{ev.username}/{repo.get('name')}"
            insight = RepoInsight(
                name=repo.get("name") or "",
                url=repo.get("html_url") or f"https://github.com/{full}",
                description=repo.get("description"),
                primary_language=repo.get("language"),
                stars=int(repo.get("stargazers_count") or 0),
                forks=int(repo.get("forks_count") or 0),
                is_fork=bool(repo.get("fork")),
                topics=list(repo.get("topics") or []),
                size_kb=int(repo.get("size") or 0),
                pushed_at=repo.get("pushed_at"),
                created_at=repo.get("created_at"),
                open_issues=int(repo.get("open_issues_count") or 0),
            )
            async with sem:
                if idx < self._deep_lang:
                    insight.languages_bytes = await self._repo_languages(client, full)
                if idx < self._deep_tree:
                    struct = await self._repo_structure(
                        client, full, repo.get("default_branch") or "main"
                    )
                    insight.has_ci = struct.get("has_ci", False)
                    insight.has_tests = struct.get("has_tests", False)
                    insight.has_docs = struct.get("has_docs", False)
            return insight

        insights = await asyncio.gather(
            *(enrich(r, i) for i, r in enumerate(originals[: max(self._deep_lang, 20)]))
        )
        # Include remaining originals as lightweight insights (no deep calls).
        for r in originals[max(self._deep_lang, 20):]:
            insights = list(insights) + [
                RepoInsight(
                    name=r.get("name") or "",
                    url=r.get("html_url") or "",
                    primary_language=r.get("language"),
                    stars=int(r.get("stargazers_count") or 0),
                    forks=int(r.get("forks_count") or 0),
                    topics=list(r.get("topics") or []),
                    size_kb=int(r.get("size") or 0),
                    pushed_at=r.get("pushed_at"),
                )
            ]

        deep_count = min(len(insights), max(self._deep_tree, 1))
        docs_hits = tests_hits = ci_hits = 0

        for ins in insights:
            # Aggregate language bytes.
            if ins.languages_bytes:
                for lang, b in ins.languages_bytes.items():
                    ev.languages_bytes[lang] = ev.languages_bytes.get(lang, 0) + b
            if ins.primary_language:
                lang_repo_count[ins.primary_language] = lang_repo_count.get(ins.primary_language, 0) + 1
            ev.total_stars += ins.stars
            ev.total_forks += ins.forks
            topics_all.extend(ins.topics)
            framework_blobs.extend([ins.name, ins.description or "", " ".join(ins.topics)])
            d = _days_since(ins.pushed_at)
            if d is not None:
                push_days.append(d)
            if ins.has_docs:
                docs_hits += 1
            if ins.has_tests:
                tests_hits += 1
            if ins.has_ci:
                ci_hits += 1
            ins.complexity = self._repo_complexity(ins)

        ev.languages_repo_count = lang_repo_count
        ev.frameworks = _detect_frameworks(framework_blobs + list(ev.languages_bytes.keys()))
        ev.topics = sorted(set(topics_all))[:20]
        ev.most_recent_push_days = min(push_days) if push_days else None
        ev.active_repos_last_year = sum(1 for d in push_days if d <= 365)

        if self._deep_tree > 0 and deep_count > 0:
            ev.documented_repo_ratio = round(docs_hits / deep_count, 2)
            ev.tested_repo_ratio = round(tests_hits / deep_count, 2)
            ev.ci_repo_ratio = round(ci_hits / deep_count, 2)
            ev.structural_analysis_available = True

        ev.oss_signal = self._oss_signal(ev)
        # Keep the richest repos on the record for evidence display.
        ev.repos = sorted(insights, key=lambda x: (x.stars, x.complexity), reverse=True)[:15]

    @staticmethod
    def _repo_complexity(ins: RepoInsight) -> float:
        import math

        size_c = min(1.0, math.log1p(ins.size_kb) / math.log1p(50000))
        lang_c = min(1.0, len(ins.languages_bytes) / 5.0)
        star_c = min(1.0, math.log1p(ins.stars) / math.log1p(500))
        rigor = 0.15 * ins.has_ci + 0.15 * ins.has_tests + 0.1 * ins.has_docs
        return round(min(1.0, 0.4 * size_c + 0.25 * lang_c + 0.2 * star_c + rigor), 3)

    @staticmethod
    def _oss_signal(ev: GithubEvidence) -> float:
        import math

        followers_c = min(1.0, math.log1p(ev.followers) / math.log1p(1000))
        forks_c = min(1.0, math.log1p(ev.total_forks) / math.log1p(200))
        stars_c = min(1.0, math.log1p(ev.total_stars) / math.log1p(2000))
        orgs_c = min(1.0, len(ev.contributed_orgs) / 4.0)
        return round(0.3 * followers_c + 0.25 * forks_c + 0.3 * stars_c + 0.15 * orgs_c, 3)


github_analyzer = GithubAnalyzer()
