from pydantic import BaseModel


class ImageFeaturesResponse(BaseModel):
    format: str | None
    width: int
    height: int
    color_mode: str
    frame_count: int
    file_size_bytes: int
    is_animated: bool


class VideoFrameFeature(BaseModel):
    frame_index: int
    timestamp_seconds: float
    width: int
    height: int
    mean_brightness: float
    sharpness_score: float


class VideoFeaturesResponse(BaseModel):
    container: str
    file_size_bytes: int
    header_valid: bool
    fps: float
    duration_seconds: float
    total_frames: int
    original_width: int
    original_height: int
    frames_extracted: int
    sampled_frames: list[VideoFrameFeature]
    analysis_stage: str
