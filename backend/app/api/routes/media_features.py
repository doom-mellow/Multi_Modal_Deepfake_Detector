
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.detectors.image.analyzer import analyze_image
from app.detectors.video.analyzer import analyze_video
from app.schemas.media import (
    ImageFeaturesResponse,
    VideoFeaturesResponse,
)
from app.services.file_service import validate_uploaded_file


router = APIRouter(
    prefix="/features",
    tags=["Media Feature Analysis"],
)


@router.post("/image", response_model=ImageFeaturesResponse)
async def image_features(file: UploadFile = File(...)):
    await validate_uploaded_file(file, "image")
    content = await file.read()

    try:
        return analyze_image(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/video", response_model=VideoFeaturesResponse)
async def video_features(file: UploadFile = File(...)):
    await validate_uploaded_file(file, "video")
    content = await file.read()

    try:
        return analyze_video(
            content,
            filename=file.filename or "upload.mp4",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
