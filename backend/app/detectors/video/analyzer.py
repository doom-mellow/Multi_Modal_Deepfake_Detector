
import math
import os
import tempfile
from pathlib import Path

import cv2


MAX_SAMPLED_FRAMES = 12
MAX_FRAME_DIMENSION = 640


def _detect_container(content: bytes) -> str:
    if len(content) >= 8 and content[4:8] == b"ftyp":
        return "isobmff"

    if content.startswith(b"\x1A\x45\xDF\xA3"):
        return "ebml"

    if (
        len(content) >= 12
        and content[:4] == b"RIFF"
        and content[8:12] == b"AVI "
    ):
        return "avi"

    raise ValueError(
        "The uploaded file does not have a recognized video container signature."
    )


def _sample_frame_indices(frame_count: int) -> list[int]:
    if frame_count <= 0:
        return []

    sample_count = min(frame_count, MAX_SAMPLED_FRAMES)

    if sample_count == 1:
        return [0]

    indices = {
        round(
            index * (frame_count - 1) / (sample_count - 1)
        )
        for index in range(sample_count)
    }

    return sorted(indices)


def _resize_frame(frame):
    height, width = frame.shape[:2]

    largest_dimension = max(width, height)

    if largest_dimension <= MAX_FRAME_DIMENSION:
        return frame

    scale = MAX_FRAME_DIMENSION / largest_dimension

    new_width = max(1, round(width * scale))
    new_height = max(1, round(height * scale))

    return cv2.resize(
        frame,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA,
    )


def analyze_video(content: bytes, filename: str = "upload.mp4") -> dict:
    if not content:
        raise ValueError("Video file is empty.")

    container = _detect_container(content)

    suffix = Path(filename).suffix.lower()

    if not suffix:
        suffix = ".mp4"

    temp_path = None
    capture = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        capture = cv2.VideoCapture(temp_path)

        if not capture.isOpened():
            raise ValueError(
                "The video container was recognized, but OpenCV could not open the video."
            )

        fps = capture.get(cv2.CAP_PROP_FPS)
        total_frames = int(
            capture.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        original_width = int(
            capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        )
        original_height = int(
            capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        if (
            not math.isfinite(fps)
            or fps <= 0
            or total_frames <= 0
            or original_width <= 0
            or original_height <= 0
        ):
            raise ValueError(
                "The video could not provide valid frame-rate or dimension information."
            )

        duration = total_frames / fps
        frame_indices = _sample_frame_indices(total_frames)

        sampled_frames = []

        for frame_index in frame_indices:
            capture.set(
                cv2.CAP_PROP_POS_FRAMES,
                frame_index,
            )

            success, frame = capture.read()

            if not success or frame is None:
                continue

            frame = _resize_frame(frame)

            height, width = frame.shape[:2]

            grayscale = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY,
            )

            brightness = float(
                cv2.mean(grayscale)[0]
            )

            sharpness = float(
                cv2.Laplacian(
                    grayscale,
                    cv2.CV_64F,
                ).var()
            )

            sampled_frames.append({
                "frame_index": frame_index,
                "timestamp_seconds": round(
                    frame_index / fps,
                    3,
                ),
                "width": width,
                "height": height,
                "mean_brightness": round(
                    brightness,
                    2,
                ),
                "sharpness_score": round(
                    sharpness,
                    2,
                ),
            })

        if not sampled_frames:
            raise ValueError(
                "The video opened, but no frames could be decoded."
            )

        return {
            "container": container,
            "file_size_bytes": len(content),
            "header_valid": True,
            "fps": round(fps, 3),
            "duration_seconds": round(duration, 3),
            "total_frames": total_frames,
            "original_width": original_width,
            "original_height": original_height,
            "frames_extracted": len(sampled_frames),
            "sampled_frames": sampled_frames,
            "analysis_stage": "frame_sampling_and_basic_visual_features",
        }

    except cv2.error as exc:
        raise ValueError(
            "An error occurred while decoding the video."
        ) from exc

    finally:
        if capture is not None:
            capture.release()

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
