import asyncio
import json

import httpx
import pytest

from src.services.llm_adapters.azure_openai_adapter import AzureOpenAIAdapter


def make_adapter(handler, model="gpt-6.2-sol", endpoint="https://res.openai.azure.com/openai/v1/"):
    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    adapter = AzureOpenAIAdapter(
        api_key="secret",
        model=model,
        endpoint=endpoint,
        transport=httpx.MockTransport(handler),
        sleep=fake_sleep,
    )
    return adapter, sleeps


def ok_response():
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "SCORE: 80/100"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        },
    )


@pytest.mark.parametrize(
    "raw",
    [
        "https://res.openai.azure.com",
        "https://res.openai.azure.com/",
        "https://res.openai.azure.com/openai",
        "https://res.openai.azure.com/openai/v1/",
    ],
)
def test_endpoint_normalization(raw):
    assert AzureOpenAIAdapter._normalize_endpoint(raw) == "https://res.openai.azure.com"


def test_retry_on_429_then_success_and_request_shape(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_REASONING", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_REASONING_EFFORT", raising=False)
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={"retry-after": "3"})
        return ok_response()

    adapter, sleeps = make_adapter(handler)
    result = asyncio.run(adapter.analyze_cv("cv", "offre"))

    assert result.content == "SCORE: 80/100"
    assert len(calls) == 2
    assert sleeps == [3.0]
    request = calls[0]
    assert str(request.url) == "https://res.openai.azure.com/openai/v1/chat/completions"
    assert request.headers["api-key"] == "secret"
    assert "authorization" not in request.headers
    body = json.loads(request.content)
    assert body["model"] == "gpt-6.2-sol"
    assert "temperature" not in body
    assert body["max_completion_tokens"] == 16000
    assert body["reasoning_effort"] == "medium"


def test_legacy_model_uses_temperature():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return ok_response()

    adapter, _ = make_adapter(handler, model="gpt-4o")
    asyncio.run(adapter.analyze_cv("cv", "offre"))
    assert seen["temperature"] == 0.2
    assert "reasoning_effort" not in seen


def test_404_deployment_not_found():
    adapter, _ = make_adapter(lambda r: httpx.Response(404, json={"error": {"message": "x"}}))
    with pytest.raises(Exception, match="Deploiement introuvable"):
        asyncio.run(adapter.analyze_cv("cv", "offre"))
    result = asyncio.run(adapter.test_connection())
    assert result["status"] == "error"
    assert "Deploiement introuvable" in result["message"]


def test_401_invalid_key():
    adapter, _ = make_adapter(lambda r: httpx.Response(401))
    with pytest.raises(Exception, match="invalide"):
        asyncio.run(adapter.analyze_cv("cv", "offre"))


def test_retries_exhausted_and_wait_capped():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503, headers={"retry-after": "999"})

    adapter, sleeps = make_adapter(handler)
    with pytest.raises(Exception, match="5 tentatives"):
        asyncio.run(adapter.analyze_cv("cv", "offre"))
    assert len(calls) == 5
    assert sleeps == [60.0] * 4


def test_empty_content_suggests_lower_effort():
    adapter, _ = make_adapter(
        lambda r: httpx.Response(200, json={"choices": [{"message": {"content": ""}}]})
    )
    with pytest.raises(Exception, match="REASONING_EFFORT"):
        asyncio.run(adapter.analyze_cv("cv", "offre"))


def test_connect_error_retries_with_backoff():
    def handler(request):
        raise httpx.ConnectError("boom")

    adapter, sleeps = make_adapter(handler)
    with pytest.raises(Exception, match="connecter"):
        asyncio.run(adapter.analyze_cv("cv", "offre"))
    assert sleeps == [1.0, 2.0, 4.0, 8.0]


def test_env_fallback(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "envkey")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://env.openai.azure.com/openai")
    adapter = AzureOpenAIAdapter(model="d")
    assert adapter.api_key == "envkey"
    assert adapter.endpoint == "https://env.openai.azure.com"


def test_reasoning_override(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_REASONING", "0")
    adapter = AzureOpenAIAdapter(api_key="k", model="gpt-6.2-sol", endpoint="https://e")
    assert adapter.is_reasoning_model is False
