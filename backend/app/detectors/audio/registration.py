
from fastapi import HTTPException, UploadFile

from app.services.detector_registry import detector_registry
from app.detectors.audio.analyzer import analyze_audio


async def detect_audio(
    content: str | None = None,
    url: str | None = None,
    file: UploadFile | None = None,
    file_metadata: dict | None = None,
    language_hint: str | None = None,
) -> dict:
    """
    Audio analysis adapter.

    Performs PCM WAV validation, signal measurements,
    and basic spectral analysis.

    This is not an AI-generated audio classifier.
    """

    if file is None:
        raise HTTPException(
            status_code=400,
            detail="Please upload an audio file.",
        )

    try:
        audio_bytes = await file.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded audio file is empty.",
            )

        analysis = analyze_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "upload.wav",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "result": "analysis-complete",
        "explanation": (
            "Audio analysis completed. The uploaded WAV file was "
            "inspected for format, duration, signal energy, silence, "
            "clipping, zero-crossing rate, and spectral characteristics. "
            "These measurements do not determine whether the audio "
            "was AI-generated or authentic."
        ),
        "indicators": [
            f"Audio format: {analysis['format']} ({analysis['encoding']})",
            f"Duration: {analysis['duration_seconds']} seconds",
            f"Sample rate: {analysis['sample_rate_hz']} Hz",
            f"Channels: {analysis['channels']}",
            f"Bit depth: {analysis['bit_depth']}-bit",
            f"RMS energy: {analysis['rms_energy']}",
            f"Silence ratio: {analysis['silence_ratio']}",
            f"Clipping ratio: {analysis['clipping_ratio']}",
            (
                f"Spectral centroid: "
                f"{analysis['spectral_centroid_hz']} Hz"
            ),
        ],
        "metadata": analysis,
    }


def register_audio_detector() -> bool:
    detector_registry.register("audio", detect_audio)
    return True
