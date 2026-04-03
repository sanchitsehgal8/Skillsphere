import os
import time
from asyncio import Lock

from fastapi import Header, HTTPException
import httpx
from jose import JWTError, jwt

_HS_ALGORITHMS = ["HS256"]
_ASYMMETRIC_ALGORITHMS = ["RS256", "ES256"]

_jwks_cache = None
_jwks_cached_at = 0.0
_jwks_lock = Lock()
_jwks_ttl_seconds = int(os.environ.get("SUPABASE_JWKS_CACHE_TTL_SECONDS", "3600"))


def _get_jwt_secret() -> str:
    secret = os.getenv("SUPABASE_JWT_SECRET", "").strip()
    if not secret:
        raise HTTPException(status_code=500, detail="Server auth is not configured")
    return secret


def _get_supabase_url() -> str:
    base = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=500, detail="SUPABASE_URL is not configured")
    return base


def _is_jwks_cache_valid() -> bool:
    if _jwks_cache is None:
        return False
    return (time.time() - _jwks_cached_at) < _jwks_ttl_seconds


async def _get_jwks(force_refresh: bool = False):
    global _jwks_cache, _jwks_cached_at

    if not force_refresh and _is_jwks_cache_valid():
        return _jwks_cache

    async with _jwks_lock:
        if not force_refresh and _is_jwks_cache_valid():
            return _jwks_cache

        try:
            url = f"{_get_supabase_url()}/auth/v1/.well-known/jwks.json"
            timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                _jwks_cache = resp.json()
                _jwks_cached_at = time.time()
                return _jwks_cache
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="Unable to validate auth token right now")


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer" or not token.strip():
            raise ValueError("Invalid auth scheme")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth header format")

    raw_token = token.strip()

    try:
        header = jwt.get_unverified_header(raw_token)
        alg = str(header.get("alg") or "").upper()
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token header")

    payload = None
    if alg in _HS_ALGORITHMS:
        try:
            payload = jwt.decode(
                raw_token,
                _get_jwt_secret(),
                algorithms=_HS_ALGORITHMS,
                options={"verify_aud": False},
            )
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    elif alg in _ASYMMETRIC_ALGORITHMS:
        try:
            payload = jwt.decode(
                raw_token,
                await _get_jwks(),
                algorithms=[alg],
                options={"verify_aud": False},
            )
        except JWTError:
            # Retry once in case keys rotated and cache is stale.
            try:
                payload = jwt.decode(
                    raw_token,
                    await _get_jwks(force_refresh=True),
                    algorithms=[alg],
                    options={"verify_aud": False},
                )
            except JWTError:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
    else:
        raise HTTPException(status_code=401, detail="Unsupported token algorithm")

    owner = str(
        payload.get("sub")
        or payload.get("user_id")
        or payload.get("id")
        or ""
    ).strip()
    if not owner:
        raise HTTPException(status_code=401, detail="Invalid auth token payload")

    payload["id"] = owner
    return payload