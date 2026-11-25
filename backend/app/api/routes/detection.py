
import re
import random
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.modalities import MODALITIES
from app.services.file_service import validate_uploaded_file
from app.services.input_validator import validate_detection_input
from app.services.detector_registry import detector_registry


router = APIRouter(prefix="/detect", tags=["Detection"])


# Temporary filename-based demonstration rules.
AI_FILENAME_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])AI(?![A-Za-z0-9])",
    re.IGNORECASE,
)

REAL_FILENAME_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])REAL(?![A-Za-z0-9])",
    re.IGNORECASE,
)



def create_demo_override_response(
    media_type: str,
    filename: str,
    classification: str,
) -> dict:
    """Return a frontend-compatible demonstration result."""

    confidence = round(random.uniform(65, 97), 2)

    is_ai = classification == "ai-generated"

    if is_ai:
        explanation = (
            "The submitted file is likely AI-generated based on "
            "the temporary demonstration indicator. This result "
            "does not independently verify the content's origin."
        )

        indicators = [
            "AI-related demonstration indicator identified.",
            "The content is likely AI-generated.",
        ]

        trigger = "filename_contains_ai"

    else:
        explanation = (
            "No AI-generation indicator was identified by this "
            "demonstration check. This does not establish that "
            "the content is human-created."
        )

        indicators = [
            "No AI-generation indicator identified.",
            "Content origin remains unverified.",
        ]

        trigger = "filename_contains_real"

    return {
        "modality": media_type,
        "result": classification,
        "confidence": confidence,
        "explanation": explanation,
        "indicators": indicators,
        "metadata": {
            "demo_override": True,
            "trigger": trigger,
            "filename": filename,
            "actual_model_inference_performed": False,
            "confidence_is_simulated": True,
        },
    }



@router.post("/{media_type}")
async def detect_content(
    media_type: str,
    content: Optional[str] = Form(default=None),
    url: Optional[str] = Form(default=None),
    language_hint: Optional[str] = Form(default=None),
    filename: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
):
    # 1. Validate the requested modality.
    if media_type not in MODALITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported modality: {media_type}",
        )

    # 2. Validate the supplied input.
    await validate_detection_input(
        media_type=media_type,
        content=content,
        url=url,
        file=file,
    )

    # 3. Validate uploaded files and collect metadata.
    file_metadata = None

    if file is not None:
        file_metadata = await validate_uploaded_file(
            file=file,
            media_type=media_type,
        )

    # 4. Determine the filename.
    # For uploaded files, use the actual uploaded filename.
    # For text content submitted from a .txt upload, use the
    # separately supplied filename form field.
    submitted_filename = (
        file.filename
        if file is not None and file.filename
        else filename or ""
    )

    # 5. Temporary filename-based demonstration behavior.
    if submitted_filename:
        if AI_FILENAME_PATTERN.search(submitted_filename):
            return create_demo_override_response(
                media_type,
                submitted_filename,
                "ai-generated",
            )

        if REAL_FILENAME_PATTERN.search(submitted_filename):
            return create_demo_override_response(
                media_type,
                submitted_filename,
                "real",
            )

    # 6. Retrieve the registered detector.
    detector = detector_registry.get(media_type)

    if detector is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"The {media_type} detector "
                "is not currently available."
            ),
        )

    # 7. Execute the registered detector.
    result = await detector(
        content=content,
        url=url,
        file=file,
        file_metadata=file_metadata,
        language_hint=language_hint,
    )

    return result
