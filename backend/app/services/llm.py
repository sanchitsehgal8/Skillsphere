"""Hugging Face Inference Providers client (OpenAI-compatible chat router).

Design principles:
- **Never crashes the request.** Any transport/model error returns ``None`` so
  callers fall back to the deterministic engine. The product must work with the
  LLM unavailable (no key, rate limited, model cold, network down).
- **Grounded only.** Prompts are constructed by callers to include the candidate
  evidence; this module never invents context. It also strips markdown fences so
  both general and Coder Qwen variants parse cleanly.
- **Async-first** to avoid blocking the FastAPI event loop; a sync helper exists
  for scripts/tests.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger("skillsphere.llm")

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def _strip_to_json(text: str) -> str:
    """Remove markdown fences and isolate the first JSON object."""
    cleaned = _FENCE_RE.sub("", text or "").strip()
    match = _JSON_OBJ_RE.search(cleaned)
    return match.group(0) if match else cleaned


class LLMClient:
    def __init__(self) -> None:
        self._model = settings.hf_model
        self._base = settings.hf_base_url.rstrip("/")
        self._token = settings.hf_api_token
        self._timeout = settings.llm_timeout_seconds
        self._max_tokens = settings.llm_max_tokens

    @property
    def is_ready(self) -> bool:
        return settings.llm_ready

    @property
    def model(self) -> str:
        return self._model

    def _payload(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        json_mode: bool,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }
        # Best-effort JSON mode; ignored by providers that don't support it, in
        # which case _strip_to_json still recovers the object.
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _extract_content(data: Dict[str, Any]) -> Optional[str]:
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None

    async def achat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> Optional[str]:
        if not self.is_ready:
            return None

        url = f"{self._base}/chat/completions"
        payload = self._payload(messages, temperature, max_tokens, json_mode)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, headers=self._headers(), json=payload)
                if resp.status_code != 200:
                    logger.warning("LLM call non-200 (%s): %s", resp.status_code, resp.text[:300])
                    return None
                content = self._extract_content(resp.json())
                return content.strip() if content else None
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("LLM call failed: %s", exc)
            return None

    async def achat_json(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        raw = await self.achat(
            messages, temperature=temperature, max_tokens=max_tokens, json_mode=True
        )
        if not raw:
            return None
        try:
            return json.loads(_strip_to_json(raw))
        except (json.JSONDecodeError, TypeError):
            logger.warning("LLM returned non-JSON payload: %s", raw[:200])
            return None

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> Optional[str]:
        """Synchronous convenience wrapper for scripts/tests."""
        if not self.is_ready:
            return None
        url = f"{self._base}/chat/completions"
        payload = self._payload(
            messages,
            kwargs.get("temperature", 0.2),
            kwargs.get("max_tokens"),
            kwargs.get("json_mode", False),
        )
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(url, headers=self._headers(), json=payload)
                if resp.status_code != 200:
                    return None
                content = self._extract_content(resp.json())
                return content.strip() if content else None
        except (httpx.HTTPError, ValueError):
            return None


llm = LLMClient()
