
from typing import Literal
from pydantic import BaseModel, Field


class DetectionResponse(BaseModel):
    result: Literal["real", "ai-generated"]
    confidence: float = Field(ge=0, le=100)
    explanation: str
    indicators: list[str] = Field(default_factory=list)

    codeBreakdown: dict | None = None
    embeddingBreakdown: dict | None = None
    watermarkBreakdown: dict | None = None


class ErrorResponse(BaseModel):
    detail: str
