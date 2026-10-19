import httpx

from app.llm.base import LLMProvider


class OllamaProvider:
    """LLM provider that communicates with a local Ollama server."""

    def __init__(
        self,
        model: str = "qwen3:0.6b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        """Generate a response using the local Ollama model."""

        if not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        result = response.json()
        return result["response"]
