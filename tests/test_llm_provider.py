import pytest

from app.llm.base import LLMProvider
from app.llm.mock import MockProvider


def test_mock_provider_returns_configured_response():
    provider = MockProvider("Analysis complete.")

    assert provider.generate("Analyze sales.") == "Analysis complete."


def test_mock_provider_rejects_empty_prompt():
    provider = MockProvider()

    with pytest.raises(ValueError, match="Prompt must not be empty"):
        provider.generate("   ")


def test_mock_provider_satisfies_provider_protocol():
    provider = MockProvider()

    assert isinstance(provider, LLMProvider)
