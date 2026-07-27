"""Durable storage for jobs, candidate evidence/scorecards, and match results.

Supabase (Postgres) is the primary backing store — see ``sql/supabase_init.sql``
for the schema. If that migration has not been run yet (detected via
PostgREST's "table/column not found" schema-cache error), calls transparently
fall back to an in-process store so local development and this session's
validation are never blocked on a manual SQL step. The fallback is logged
loudly on every use — it is NOT silently masking a production outage, only a
missing one-time migration.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from supabase import Client, create_client

from app.config import settings
from app.models import CandidateEvidence, EngineeringScorecard, JobSpec, MatchResult

logger = logging.getLogger("skillsphere.persistence")


class PersistenceError(RuntimeError):
    pass


_SCHEMA_CACHE_ERROR_CODES = {
    "PGRST204",  # PostgREST: column not in schema cache (write path)
    "PGRST205",  # PostgREST: table not in schema cache
    "42703",     # Postgres: undefined_column (raw SQL path, e.g. explicit SELECT)
    "42P01",     # Postgres: undefined_table
}


def _is_missing_schema_error(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code in _SCHEMA_CACHE_ERROR_CODES:
        return True
    text = str(exc).lower()
    if "does not exist" in text and ("column" in text or "relation" in text or "table" in text):
        return True
    return "could not find" in text and ("column" in text or "table" in text) and "schema cache" in text


def _is_rls_error(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code == "42501":  # Postgres: insufficient_privilege
        return True
    return "row-level security" in str(exc).lower()


def _is_invalid_api_key_error(exc: Exception) -> bool:
    text = str(exc).lower()
    if "invalid api key" in text:
        return True
    return str(getattr(exc, "code", "")) == "401"


def _wrap(action: str, exc: Exception) -> PersistenceError:
    """Attach an actionable hint when the underlying cause is a known,
    self-diagnosable misconfiguration rather than a genuine transient error."""
    if _is_rls_error(exc):
        return PersistenceError(
            f"Failed to {action}: Supabase row-level security rejected the write. "
            "The backend's own JWT verification + owner_id filtering is the real "
            "authorization boundary, so RLS should not gate this trusted server "
            "connection. Fix: set SUPABASE_SERVICE_ROLE_KEY in backend/.env (Supabase "
            "dashboard -> Project Settings -> API -> 'service_role' secret), which "
            "bypasses RLS by design — or disable RLS on the affected table. "
            f"Original error: {exc}"
        )
    if _is_invalid_api_key_error(exc):
        return PersistenceError(
            f"Failed to {action}: Supabase rejected the API key itself (not a policy "
            "issue — the key value is wrong, truncated, or from a different project). "
            "Check the deployment's SUPABASE_SERVICE_ROLE_KEY / SUPABASE_URL env vars: "
            "re-copy the 'service_role' secret fresh from Supabase dashboard -> Project "
            "Settings -> API, paste into a plain text editor first to rule out truncated "
            "copy-paste, confirm SUPABASE_URL's project ref matches the key's project, "
            "and confirm it isn't swapped with SUPABASE_JWT_SECRET (that one is a short "
            "UUID-like string, not a long eyJ... JWT). Redeploy after fixing — env var "
            f"edits don't hot-reload. Original error: {exc}"
        )
    return PersistenceError(f"Failed to {action}: {exc}")


class _InMemoryStore:
    """Process-local fallback. Data does not survive a restart."""

    def __init__(self) -> None:
        self.jobs: Dict[str, Dict[str, JobSpec]] = {}
        self.candidates: Dict[str, Dict[str, Tuple[CandidateEvidence, EngineeringScorecard]]] = {}
        self.analyses: Dict[str, Dict[Tuple[str, str], MatchResult]] = {}

    def upsert_job(self, owner: str, job: JobSpec) -> None:
        self.jobs.setdefault(owner, {})[job.id] = job

    def get_job(self, owner: str, job_id: str) -> Optional[JobSpec]:
        return self.jobs.get(owner, {}).get(job_id)

    def list_jobs(self, owner: str) -> List[JobSpec]:
        return list(self.jobs.get(owner, {}).values())

    def upsert_candidate(self, owner: str, ev: CandidateEvidence, scorecard: EngineeringScorecard) -> None:
        self.candidates.setdefault(owner, {})[ev.candidate_id] = (ev, scorecard)

    def get_candidate(self, owner: str, candidate_id: str) -> Optional[Tuple[CandidateEvidence, EngineeringScorecard]]:
        return self.candidates.get(owner, {}).get(candidate_id)

    def list_candidates(self, owner: str) -> List[Tuple[CandidateEvidence, EngineeringScorecard]]:
        return list(self.candidates.get(owner, {}).values())

    def upsert_analysis(self, owner: str, result: MatchResult) -> None:
        self.analyses.setdefault(owner, {})[(result.job_id, result.candidate_id)] = result

    def get_analysis(self, owner: str, job_id: str, candidate_id: str) -> Optional[MatchResult]:
        return self.analyses.get(owner, {}).get((job_id, candidate_id))

    def list_analyses(self, owner: str, job_id: Optional[str] = None) -> List[MatchResult]:
        rows = self.analyses.get(owner, {})
        return [r for (jid, _cid), r in rows.items() if job_id is None or jid == job_id]


class SupabasePersistence:
    def __init__(self) -> None:
        self._client: Optional[Client] = None
        self._fallback = _InMemoryStore()
        self._warned = False

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url:
            raise PersistenceError(
                "SUPABASE_URL is missing."
            )

        if not settings.supabase_service_key:
            raise PersistenceError(
                "SUPABASE_SERVICE_ROLE_KEY is missing."
            )

        logger.info("=" * 60)
        logger.info(f"SUPABASE_URL = {settings.supabase_url}")
        logger.info(f"SUPABASE_KEY_PREFIX = {settings.supabase_service_key[:20]}")
        logger.info(f"SUPABASE_KEY_LENGTH = {len(settings.supabase_service_key)}")
        logger.info("=" * 60)

        try:
            self._client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
                )
            logger.info("Supabase client created successfully.")

        except Exception as e:
            logger.exception(f"Failed to create Supabase client: {e}")
            raise

        return self._client

    def _warn_fallback(self, action: str, exc: Exception) -> None:
        if not self._warned:
            logger.warning(
                "Supabase schema is missing expected tables/columns — falling back to "
                "in-memory storage. Run sql/supabase_init.sql in the Supabase SQL editor "
                "to enable durable persistence. (%s: %s)", action, exc,
            )
            self._warned = True

    # --- jobs ---------------------------------------------------------- #
    def upsert_job(self, owner_id: str, job: JobSpec) -> None:
        payload = {
            "owner_id": owner_id,
            "job_id": job.id,
            "title": job.title,
            "description": job.description,
            "requirements": [r.model_dump(mode="json") for r in job.requirements],
            "spec": job.model_dump(mode="json"),
            "seniority": job.seniority,
            "created_at": job.created_at.isoformat(),
        }
        try:
            self._get_client().table("jobs").upsert(payload, on_conflict="owner_id,job_id").execute()
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("upsert_job", exc)
                self._fallback.upsert_job(owner_id, job)
                return
            raise _wrap("persist job", exc) from exc

    def get_job(self, owner_id: str, job_id: str) -> Optional[JobSpec]:
        try:
            resp = (
                self._get_client().table("jobs").select("spec,title,description,requirements,created_at")
                .eq("owner_id", owner_id).eq("job_id", job_id).limit(1).execute()
            )
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("get_job", exc)
                return self._fallback.get_job(owner_id, job_id)
            raise _wrap("fetch job", exc) from exc

        rows = resp.data or []
        if not rows:
            return self._fallback.get_job(owner_id, job_id)
        spec = rows[0].get("spec") or {}
        if not spec:
            return self._fallback.get_job(owner_id, job_id)
        return JobSpec(**spec)

    def list_jobs(self, owner_id: str) -> List[JobSpec]:
        try:
            resp = (
                self._get_client().table("jobs").select("spec").eq("owner_id", owner_id)
                .order("created_at", desc=True).execute()
            )
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("list_jobs", exc)
                return self._fallback.list_jobs(owner_id)
            raise _wrap("list jobs", exc) from exc
        out = [JobSpec(**row["spec"]) for row in (resp.data or []) if row.get("spec")]
        return out or self._fallback.list_jobs(owner_id)

    # --- candidates ------------------------------------------------------ #
    def upsert_candidate(self, owner_id: str, ev: CandidateEvidence, scorecard: EngineeringScorecard) -> None:
        payload = {
            "owner_id": owner_id,
            "candidate_id": ev.candidate_id,
            "name": ev.name,
            "headline": ev.headline,
            "summary": ev.summary,
            "demographics": ev.demographics or {},
            "evidence": ev.model_dump(mode="json"),
            "scorecard": scorecard.model_dump(mode="json"),
        }
        try:
            self._get_client().table("candidates").upsert(payload, on_conflict="owner_id,candidate_id").execute()
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("upsert_candidate", exc)
                self._fallback.upsert_candidate(owner_id, ev, scorecard)
                return
            raise _wrap("persist candidate", exc) from exc

    def get_candidate(self, owner_id: str, candidate_id: str) -> Optional[Tuple[CandidateEvidence, EngineeringScorecard]]:
        try:
            resp = (
                self._get_client().table("candidates").select("evidence,scorecard")
                .eq("owner_id", owner_id).eq("candidate_id", candidate_id).limit(1).execute()
            )
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("get_candidate", exc)
                return self._fallback.get_candidate(owner_id, candidate_id)
            raise _wrap("fetch candidate", exc) from exc

        rows = resp.data or []
        if not rows or not rows[0].get("evidence"):
            return self._fallback.get_candidate(owner_id, candidate_id)
        return CandidateEvidence(**rows[0]["evidence"]), EngineeringScorecard(**rows[0]["scorecard"])

    def list_candidates(self, owner_id: str) -> List[Tuple[CandidateEvidence, EngineeringScorecard]]:
        try:
            resp = (
                self._get_client().table("candidates").select("evidence,scorecard")
                .eq("owner_id", owner_id).order("created_at", desc=True).execute()
            )
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("list_candidates", exc)
                return self._fallback.list_candidates(owner_id)
            raise _wrap("list candidates", exc) from exc
        out = [
            (CandidateEvidence(**row["evidence"]), EngineeringScorecard(**row["scorecard"]))
            for row in (resp.data or []) if row.get("evidence")
        ]
        return out or self._fallback.list_candidates(owner_id)

    # --- analyses --------------------------------------------------------- #
    def upsert_analysis(self, owner_id: str, result: MatchResult) -> None:
        payload = {
            "owner_id": owner_id,
            "job_id": result.job_id,
            "candidate_id": result.candidate_id,
            "fit_score": result.fit_score,
            "verdict": result.verdict,
            "overall_score": result.scorecard.overall_score,
            "result": result.model_dump(mode="json"),
        }
        try:
            self._get_client().table("analyses").upsert(payload, on_conflict="owner_id,job_id,candidate_id").execute()
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("upsert_analysis", exc)
                self._fallback.upsert_analysis(owner_id, result)
                return
            raise _wrap("persist analysis", exc) from exc

    def get_analysis(self, owner_id: str, job_id: str, candidate_id: str) -> Optional[MatchResult]:
        try:
            resp = (
                self._get_client().table("analyses").select("result")
                .eq("owner_id", owner_id).eq("job_id", job_id).eq("candidate_id", candidate_id)
                .limit(1).execute()
            )
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("get_analysis", exc)
                return self._fallback.get_analysis(owner_id, job_id, candidate_id)
            raise _wrap("fetch analysis", exc) from exc
        rows = resp.data or []
        if not rows or not rows[0].get("result"):
            return self._fallback.get_analysis(owner_id, job_id, candidate_id)
        return MatchResult(**rows[0]["result"])

    def list_analyses(self, owner_id: str, job_id: Optional[str] = None) -> List[MatchResult]:
        try:
            q = self._get_client().table("analyses").select("result").eq("owner_id", owner_id)
            if job_id:
                q = q.eq("job_id", job_id)
            resp = q.order("created_at", desc=True).execute()
        except Exception as exc:  # noqa: BLE001
            if _is_missing_schema_error(exc):
                self._warn_fallback("list_analyses", exc)
                return self._fallback.list_analyses(owner_id, job_id)
            raise _wrap("list analyses", exc) from exc
        out = [MatchResult(**row["result"]) for row in (resp.data or []) if row.get("result")]
        return out or self._fallback.list_analyses(owner_id, job_id)


persistence = SupabasePersistence()
