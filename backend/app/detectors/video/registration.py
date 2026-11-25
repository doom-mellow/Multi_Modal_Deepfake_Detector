
from fastapi import HTTPException, UploadFile

from app.services.detector_registry import detector_registry
from app.detectors.video.analyzer import analyze_video


async def detect_video(
    content: str | None = None,
    url: str | None = None,
    file: UploadFile | None = None,
    file_metadata: dict | None = None,
    language_hint: str | None = None,
) -> dict:
    """
    Video analysis adapter.

    Performs container validation, frame extraction,
    and basic visual feature analysis.

    This is not an AI-generated video classifier.
    """

    if file is None:
        raise HTTPException(
            status_code=501,
            detail="Video URL analysis is not implemented yet. Please upload a video file.",
        )

    try:
        video_bytes = await file.read()

        analysis = analyze_video(
            content=video_bytes,
            filename=file.filename or "upload.mp4",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "result": "analysis-complete",
        "explanation": (
            "Video analysis completed. The uploaded video was inspected "
            "for container validity, frame information, brightness, and "
            "sharpness. These measurements do not determine whether the "
            "video was AI-generated."
        ),
        "indicators": [
            f"Container format: {analysis['container']}",
            f"Video duration: {analysis['duration_seconds']} seconds",
            f"Frame rate: {analysis['fps']} FPS",
            f"Total frames: {analysis['total_frames']}",
            f"Frames successfully analyzed: {analysis['frames_extracted']}",
            (
                f"Original resolution: "
                f"{analysis['original_width']}x{analysis['original_height']}"
            ),
        ],
        "metadata": analysis,
    }


def register_video_detector() -> bool:
    detector_registry.register("video", detect_video)
    return True
