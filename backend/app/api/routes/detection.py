
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from typing import Optional

from app.core.modalities import MODALITIES
from app.services.file_service import validate_uploaded_file
from app.services.input_validator import validate_detection_input
from app.services.detector_registry import detector_registry

router = APIRouter(prefix="/detect", tags=["Detection"])


@router.post("/{media_type}")
async def detect_content(
    media_type: str,
    content: Optional[str] = Form(default=None),
    url: Optional[str] = Form(default=None),
    language_hint: Optional[str] = Form(default=None),
    embedding_model: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
):
    if media_type not in MODALITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported modality: {media_type}",
        )

    await validate_detection_input(
        media_type=media_type,
        content=content,
        url=url,
        file=file,
    )

    file_metadata = None

    if file is not None:
        file_metadata = await validate_uploaded_file(
            file=file,
            media_type=media_type,
        )

    detector = detector_registry.get(media_type)

    if detector is None:
        raise HTTPException(
            status_code=501,
            detail=f"The {media_type} detector is not connected yet. Input validation passed, but no analysis was performed.",
        )

    return await detector(
        content=content,
        url=url,
        file=file,
        file_metadata=file_metadata,
        language_hint=language_hint,
        embedding_model=embedding_model,
    )
