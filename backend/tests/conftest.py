"""Shared test fixtures.

Unit tests must be deterministic and network-free. The LLM client is forced
"not ready" by default so tests exercise the rules-based/deterministic paths;
tests that specifically want to verify LLM-assisted behaviour monkeypatch
``llm.achat`` / ``llm.achat_json`` directly instead of hitting the network.
"""

import pytest

from app.services.llm import llm


@pytest.fixture(autouse=True)
def _disable_llm_by_default(monkeypatch):
    monkeypatch.setattr(type(llm), "is_ready", property(lambda self: False))
    yield
