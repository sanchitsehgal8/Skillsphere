import os

from fastapi import Header, HTTPException
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer" or not token.strip():
            raise ValueError("Invalid auth scheme")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth header format")

    user = supabase.auth.get_user(token.strip())

    if not user or not user.user:
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = user.user.model_dump()
    # Normalize owner identifier for downstream code.
    payload["id"] = str(payload.get("id") or "").strip()
    return payload
