import math

import cv2
import numpy as np

from video_detector.features import extract_video_features, feature_names


def make_video(path, seed):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 8.0, (96, 96))
    assert writer.isOpened()
    rng = np.random.default_rng(seed)
    for frame_index in range(6):
        frame = rng.integers(0, 256, (96, 96, 3), dtype=np.uint8)
        cv2.circle(frame, (48 + frame_index % 3, 48), 18, (20, 180, 240), -1)
        writer.write(frame)
    writer.release()


def test_extract_video_features(tmp_path):
    video = tmp_path / "clip.avi"
    make_video(video, 1)
    features = extract_video_features(video, sample_frames=4)
    assert list(features) == feature_names()
    assert all(math.isfinite(value) for value in features.values())
    assert features["temporal_diff_mean"] >= 0


def test_bad_video_path():
    try:
        extract_video_features("missing.avi")
        assert False, "Expected path validation error"
    except ValueError as error:
        assert "does not exist" in str(error)
