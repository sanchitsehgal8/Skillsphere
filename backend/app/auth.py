import os
from pathlib import Path

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

bearer_scheme = HTTPBearer()
_jwks_cache = None


def _read_env_file_var(key: str) -> str | None:
    root = Path(__file__).resolve().parents[2]
    candidate_files = [
        root / "backend" / ".env",
        root / "frontend" / ".env",
    ]

    for env_path in candidate_files:
        if not env_path.exists():
            continue

        for line in env_path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            k, v = raw.split("=", 1)
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    return None


def _get_supabase_base_url() -> str:
    raw = (
        os.environ.get("SUPABASE_URL")
        or _read_env_file_var("SUPABASE_URL")
        or _read_env_file_var("VITE_SUPABASE_URL")
        or ""
    ).strip().rstrip("/")
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL is not configured.",
        )
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    return raw


async def get_jwks():
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    url = f"{_get_supabase_base_url()}/auth/v1/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            r.raise_for_status()
            _jwks_cache = r.json()
            return _jwks_cache
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch Supabase JWKS: {exc}",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials
    jwks = await get_jwks()
    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["ES256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
        )
