from fastapi import APIRouter, Form, HTTPException

from app.detectors.text.analyzer import analyze_text_features
from app.detectors.code.analyzer import analyze_code_features
from app.schemas.features import (
    TextFeaturesResponse,
    CodeFeaturesResponse,
)

router = APIRouter(prefix="/features", tags=["Feature Analysis"])


@router.post("/text", response_model=TextFeaturesResponse)
async def analyze_text(content: str = Form(...)):
    try:
        return analyze_text_features(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/code", response_model=CodeFeaturesResponse)
async def analyze_code(
    content: str = Form(...),
    language_hint: str = Form(default="auto"),
):
    try:
        return analyze_code_features(content, language_hint)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))