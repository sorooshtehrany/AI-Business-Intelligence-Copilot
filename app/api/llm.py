import httpx
from fastapi import APIRouter, HTTPException

from app.llm.ollama_provider import OllamaProvider
from app.schemas.llm import (
    LLMGenerateRequest,
    LLMGenerateResponse,
)


router = APIRouter(
    prefix="/api/llm",
    tags=["Language Model"],
)


@router.post(
    "/generate",
    response_model=LLMGenerateResponse,
)
def generate_text(
    request: LLMGenerateRequest,
) -> LLMGenerateResponse:
    """Generate text using the configured local language model."""

    if not request.prompt.strip():
        raise HTTPException(
            status_code=422,
            detail="Prompt must not be empty.",
        )

    provider = OllamaProvider()

    try:
        generated_text = provider.generate(request.prompt)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="The language model service returned an error.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="The language model service is unavailable.",
        ) from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="The language model returned an invalid response.",
        ) from exc

    return LLMGenerateResponse(response=generated_text)
