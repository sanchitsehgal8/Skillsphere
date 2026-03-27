import os
from typing import List, Optional

from supabase import Client, create_client

from app.models import CandidateProfile, JobDescription


class PersistenceError(RuntimeError):
    pass


class SupabasePersistence:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        url = (
            os.environ.get("SUPABASE_URL")
            or os.environ.get("VITE_SUPABASE_URL")
            or ""
        ).strip()
        key = (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or os.environ.get("VITE_SUPABASE_ANON_KEY")
            or ""
        ).strip()

        if not url or not key:
            raise PersistenceError(
                "Supabase persistence is not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.",
            )

        self._client = create_client(url, key)
        return self._client

    def upsert_job(self, owner_id: str, job: JobDescription) -> None:
        payload = {
            "owner_id": owner_id,
            "job_id": job.id,
            "title": job.title,
            "description": job.description,
            "requirements": [r.model_dump(mode="json") for r in (job.requirements or [])],
            "created_at": job.created_at.isoformat(),
        }

        try:
            self._get_client().table("jobs").upsert(payload, on_conflict="owner_id,job_id").execute()
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"Failed to persist job: {exc}") from exc

    def get_job(self, owner_id: str, job_id: str) -> Optional[JobDescription]:
        try:
            response = (
                self._get_client()
                .table("jobs")
                .select("job_id,title,description,requirements,created_at")
                .eq("owner_id", owner_id)
                .eq("job_id", job_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"Failed to fetch job: {exc}") from exc

        rows = response.data or []
        if not rows:
            return None

        row = rows[0]
        return JobDescription(
            id=row["job_id"],
            title=row["title"],
            description=row["description"],
            requirements=row.get("requirements") or [],
            created_at=row.get("created_at"),
        )

    def upsert_candidate(self, owner_id: str, candidate: CandidateProfile) -> None:
        payload = {
            "owner_id": owner_id,
            "candidate_id": candidate.id,
            "name": candidate.name,
            "headline": candidate.headline,
            "summary": candidate.summary,
            "platforms": [p.model_dump(mode="json") for p in (candidate.platforms or [])],
            "demographics": candidate.demographics or {},
        }

        try:
            self._get_client().table("candidates").upsert(payload, on_conflict="owner_id,candidate_id").execute()
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"Failed to persist candidate: {exc}") from exc

    def get_candidate(self, owner_id: str, candidate_id: str) -> Optional[CandidateProfile]:
        try:
            response = (
                self._get_client()
                .table("candidates")
                .select("candidate_id,name,headline,summary,platforms,demographics")
                .eq("owner_id", owner_id)
                .eq("candidate_id", candidate_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"Failed to fetch candidate: {exc}") from exc

        rows = response.data or []
        if not rows:
            return None

        row = rows[0]
        return CandidateProfile(
            id=row["candidate_id"],
            name=row["name"],
            headline=row.get("headline"),
            summary=row.get("summary"),
            platforms=row.get("platforms") or [],
            demographics=row.get("demographics") or {},
        )

    def list_candidates(self, owner_id: str) -> List[CandidateProfile]:
        try:
            response = (
                self._get_client()
                .table("candidates")
                .select("candidate_id,name,headline,summary,platforms,demographics")
                .eq("owner_id", owner_id)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"Failed to list candidates: {exc}") from exc

        rows = response.data or []
        return [
            CandidateProfile(
                id=row["candidate_id"],
                name=row["name"],
                headline=row.get("headline"),
                summary=row.get("summary"),
                platforms=row.get("platforms") or [],
                demographics=row.get("demographics") or {},
            )
            for row in rows
        ]


persistence = SupabasePersistence()
