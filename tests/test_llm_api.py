import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_returns_model_response(monkeypatch):
    """The API should return the generated text as JSON."""

    def fake_generate(self, prompt):
        assert prompt == "Analyze sales."
        return "Sales revenue is increasing."

    monkeypatch.setattr(
        "app.api.llm.OllamaProvider.generate",
        fake_generate,
    )

    response = client.post(
        "/api/llm/generate",
        json={"prompt": "Analyze sales."},
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Sales revenue is increasing."
    }


def test_generate_rejects_empty_prompt():
    """An empty prompt should fail request validation."""

    response = client.post(
        "/api/llm/generate",
        json={"prompt": ""},
    )

    assert response.status_code == 422


def test_generate_rejects_whitespace_prompt():
    """A prompt containing only whitespace should be rejected."""

    response = client.post(
        "/api/llm/generate",
        json={"prompt": "   "},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Prompt must not be empty."


def test_generate_rejects_prompt_over_maximum_length():
    """Prompts longer than 10000 characters should be rejected."""

    response = client.post(
        "/api/llm/generate",
        json={"prompt": "a" * 10001},
    )

    assert response.status_code == 422


def test_generate_handles_ollama_http_error(monkeypatch):
    """An HTTP error from Ollama should become a 502 response."""

    def fake_generate(self, prompt):
        request = httpx.Request(
            "POST",
            "http://localhost:11434/api/generate",
        )
        response = httpx.Response(500, request=request)

        raise httpx.HTTPStatusError(
            "Ollama server error",
            request=request,
            response=response,
        )

    monkeypatch.setattr(
        "app.api.llm.OllamaProvider.generate",
        fake_generate,
    )

    response = client.post(
        "/api/llm/generate",
        json={"prompt": "Analyze sales."},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "The language model service returned an error."
    )


def test_generate_handles_unavailable_ollama(monkeypatch):
    """A connection error should become a 503 response."""

    def fake_generate(self, prompt):
        request = httpx.Request(
            "POST",
            "http://localhost:11434/api/generate",
        )

        raise httpx.ConnectError(
            "Connection refused",
            request=request,
        )

    monkeypatch.setattr(
        "app.api.llm.OllamaProvider.generate",
        fake_generate,
    )

    response = client.post(
        "/api/llm/generate",
        json={"prompt": "Analyze sales."},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The language model service is unavailable."
    )
