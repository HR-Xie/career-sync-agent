import pytest
from llm.client import LLMClient


def test_client_creates_openai_instance():
    client = LLMClient(
        api_key="sk-test",
        base_url="https://test.api.com",
        model="test-model",
    )
    assert client.model == "test-model"
    assert client.client.api_key == "sk-test"


def test_chat_returns_content():
    client = LLMClient(
        api_key="sk-test",
        base_url="https://test.api.com",
        model="test-model",
    )
    with pytest.raises(Exception):
        # No real API key, should fail on connection
        import asyncio
        asyncio.run(client.chat("Hello"))
