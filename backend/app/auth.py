import os
import time
from asyncio import Lock
from pathlib import Path

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

bearer_scheme = HTTPBearer(auto_error=False)
_jwks_cache = None
_jwks_cached_at = 0.0
_jwks_lock = Lock()
_jwks_ttl_seconds = int(os.environ.get("SUPABASE_JWKS_CACHE_TTL_SECONDS", "3600"))


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


def _is_jwks_cache_valid() -> bool:
    if _jwks_cache is None:
        return False
    return (time.time() - _jwks_cached_at) < _jwks_ttl_seconds


async def get_jwks(force_refresh: bool = False):
    global _jwks_cache, _jwks_cached_at

    if not force_refresh and _is_jwks_cache_valid():
        return _jwks_cache

    async with _jwks_lock:
        if not force_refresh and _is_jwks_cache_valid():
            return _jwks_cache

        url = f"{_get_supabase_base_url()}/auth/v1/.well-known/jwks.json"
        try:
            timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(url)
                r.raise_for_status()
                _jwks_cache = r.json()
                _jwks_cached_at = time.time()
                return _jwks_cache
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch Supabase JWKS: {exc}",
            ) from exc


def _validate_payload_claims(payload: dict) -> None:
    expected_issuer = f"{_get_supabase_base_url()}/auth/v1"
    issuer = payload.get("iss")
    if issuer and issuer != expected_issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer.",
        )

    expected_aud = os.environ.get("SUPABASE_JWT_AUD")
    if expected_aud:
        aud = payload.get("aud")
        if isinstance(aud, list):
            aud_ok = expected_aud in aud
        else:
            aud_ok = aud == expected_aud
        if not aud_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience.",
            )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    token = credentials.credentials

    jwks = await get_jwks()
    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["ES256"],
            options={"verify_aud": False},
        )
        _validate_payload_claims(payload)
        return payload
    except JWTError as e:
        # Retry once in case Supabase rotated keys and cached JWKS is stale.
        try:
            payload = jwt.decode(
                token,
                await get_jwks(force_refresh=True),
                algorithms=["ES256"],
                options={"verify_aud": False},
            )
            _validate_payload_claims(payload)
            return payload
        except JWTError as retry_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {str(retry_error)}",
            ) from retry_error
