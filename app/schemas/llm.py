from pydantic import BaseModel, Field


class LLMGenerateRequest(BaseModel):
    """Request schema for text generation."""

    prompt: str = Field(
        min_length=1,
        max_length=10000,
        description="The prompt sent to the language model.",
    )


class LLMGenerateResponse(BaseModel):
    """Response schema for generated text."""

    response: str
