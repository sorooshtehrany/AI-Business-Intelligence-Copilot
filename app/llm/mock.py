from app.llm.base import LLMProvider


class MockProvider:
    """Deterministic LLM provider for local development and tests."""

    def __init__(self, response: str = "Mock response"):
        self.response = response

    def generate(self, prompt: str) -> str:
        """Return a predefined response without external API calls."""
        if not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        return self.response
