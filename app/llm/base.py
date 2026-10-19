from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Common interface for language model providers."""

    def generate(self, prompt: str) -> str:
        """Generate a text response from a prompt."""
        ...