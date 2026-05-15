import asyncio
from unittest.mock import AsyncMock

import pytest
from llm.client import LLMClient
from llm.fallback import LLMRouter


@pytest.fixture
def primary():
    return LLMClient(api_key="sk-a", base_url="https://api.deepseek.com", model="deepseek-chat")


@pytest.fixture
def fallback():
    return LLMClient(api_key="sk-b", base_url="https://api.moonshot.cn/v1", model="moonshot-v1-8k")


def test_router_has_clients(primary, fallback):
    router = LLMRouter(primary=primary, fallback=fallback)
    assert router.primary is primary
    assert router.fallback is fallback


def test_router_uses_primary_first(primary, fallback, monkeypatch):
    router = LLMRouter(primary=primary, fallback=fallback)
    mock_chat = AsyncMock(return_value="deepseek response")
    monkeypatch.setattr(primary, 'chat', mock_chat)
    result = asyncio.run(router.chat("sys", "msg"))
    assert result == "deepseek response"
    mock_chat.assert_awaited_once()


def test_router_falls_back_on_failure(primary, fallback, monkeypatch):
    router = LLMRouter(primary=primary, fallback=fallback)
    monkeypatch.setattr(primary, 'chat', AsyncMock(side_effect=Exception("API error")))
    mock_fallback_chat = AsyncMock(return_value="kimi response")
    monkeypatch.setattr(fallback, 'chat', mock_fallback_chat)
    result = asyncio.run(router.chat("sys", "msg"))
    assert result == "kimi response"
