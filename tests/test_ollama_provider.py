import httpx
import pytest

from app.llm.ollama_provider import OllamaProvider


def test_generate_returns_model_response(monkeypatch):
    """A successful Ollama response should return generated text."""

    def fake_post(url, json, timeout):
        assert url == "http://localhost:11434/api/generate"
        assert json["model"] == "qwen3:0.6b"
        assert json["prompt"] == "Analyze sales."
        assert json["stream"] is False

        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={"response": "Sales are increasing."},
            request=request,
        )

    monkeypatch.setattr(
        "app.llm.ollama_provider.httpx.post",
        fake_post,
    )

    provider = OllamaProvider()

    result = provider.generate("Analyze sales.")

    assert result == "Sales are increasing."


def test_generate_rejects_empty_prompt():
    """An empty prompt should be rejected before making an HTTP request."""

    provider = OllamaProvider()

    with pytest.raises(ValueError, match="Prompt must not be empty"):
        provider.generate("   ")


def test_generate_raises_http_error(monkeypatch):
    """An HTTP error from Ollama should be propagated to the caller."""

    def fake_post(url, json, timeout):
        request = httpx.Request("POST", url)
        return httpx.Response(
            500,
            json={"error": "Internal server error"},
            request=request,
        )

    monkeypatch.setattr(
        "app.llm.ollama_provider.httpx.post",
        fake_post,
    )

    provider = OllamaProvider()

    with pytest.raises(httpx.HTTPStatusError):
        provider.generate("Analyze sales.")


def test_custom_model_and_base_url():
    """The provider should support a custom model and server URL."""

    provider = OllamaProvider(
        model="qwen3:0.6b",
        base_url="http://127.0.0.1:11434/",
    )

    assert provider.model == "qwen3:0.6b"
    assert provider.base_url == "http://127.0.0.1:11434"
