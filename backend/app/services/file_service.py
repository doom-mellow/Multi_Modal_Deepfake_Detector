
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS


async def validate_uploaded_file(
    file: UploadFile,
    media_type: str,
):
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    allowed = ALLOWED_EXTENSIONS.get(media_type, set())

    if extension not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"File extension '{extension}' is not supported for {media_type}.",
        )

    total_size = 0

    while chunk := await file.read(1024 * 1024):
        total_size += len(chunk)

        if total_size > MAX_FILE_SIZE:
            await file.seek(0)
            raise HTTPException(
                status_code=413,
                detail="File exceeds the 100 MB upload limit.",
            )

    if total_size == 0:
        await file.seek(0)
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    await file.seek(0)

    return {
        "filename": filename,
        "extension": extension,
        "size": total_size,
        "content_type": file.content_type,
    }
