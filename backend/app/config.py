"""Centralised runtime configuration for SkillSphere.

All environment access flows through this module so behaviour is consistent
across local dev (``.env``), tests, and production (real env vars). Loading
``.env`` here is a no-op in production where variables are already exported.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

try:  # python-dotenv is optional at runtime; real env vars win regardless.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001 - never let config loading crash the app
    pass


def _get(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _get_bool(name: str, default: bool) -> bool:
    raw = _get(name, "true" if default else "false").lower()
    return raw in {"1", "true", "yes", "on"}


class Settings:
    """Immutable-ish view over environment configuration."""

    # --- Auth / Supabase ---
    supabase_jwt_secret: str = _get("SUPABASE_JWT_SECRET")
    supabase_url: str = _get("SUPABASE_URL") or _get("VITE_SUPABASE_URL")
    supabase_service_key = _get("SUPABASE_SERVICE_ROLE_KEY")
    
    # --- AI engine (Hugging Face Inference Providers) ---
    llm_enabled: bool = _get_bool("LLM_ENABLED", True)
    hf_api_token: str = _get("HF_API_TOKEN") or _get("HUGGINGFACE_API_TOKEN")
    hf_model: str = _get("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    hf_base_url: str = _get("HF_BASE_URL", "https://router.huggingface.co/v1")
    llm_timeout_seconds: float = float(_get_int("LLM_TIMEOUT_SECONDS", 45))
    llm_max_tokens: int = _get_int("LLM_MAX_TOKENS", 900)

    # --- External data sources ---
    github_token: str = _get("GITHUB_TOKEN")
    github_api: str = _get("GITHUB_API", "https://api.github.com")
    codeforces_api: str = _get("CODEFORCES_API", "https://codeforces.com/api")

    # --- Uploads / limits ---
    max_upload_bytes: int = _get_int("MAX_UPLOAD_BYTES", 5 * 1024 * 1024)
    rate_limit_window_seconds: int = _get_int("RATE_LIMIT_WINDOW_SECONDS", 60)
    rate_limit_default: int = _get_int("RATE_LIMIT_REQUESTS_PER_WINDOW", 120)

    @property
    def llm_ready(self) -> bool:
        return bool(self.llm_enabled and self.hf_api_token and self.hf_model)

    def cors_origins(self) -> List[str]:
        raw = _get("CORS_ORIGINS")
        if raw:
            return [o.strip() for o in raw.split(",") if o.strip()]
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
