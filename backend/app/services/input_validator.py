
from fastapi import HTTPException, UploadFile


async def validate_detection_input(
    media_type: str,
    content: str | None,
    url: str | None,
    file: UploadFile | None,
):
    if media_type == "text":
        if not content or not content.strip():
            raise HTTPException(
                status_code=400,
                detail="Text content is required.",
            )

    elif media_type == "code":
        if not content or not content.strip():
            raise HTTPException(
                status_code=400,
                detail="Source code is required.",
            )

    elif media_type == "audio":
        if file is None:
            raise HTTPException(
                status_code=400,
                detail="An audio file is required.",
            )

    elif media_type in {"image", "video"}:
        if file is None:
            raise HTTPException(
                status_code=400,
                detail=f"An uploaded file is required for {media_type} analysis.",
            )

    elif media_type == "watermark":
        if file is None:
            raise HTTPException(
                status_code=400,
                detail="An uploaded file is required for watermark analysis.",
            )
