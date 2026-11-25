"""CPU-friendly visual and temporal features from sampled video frames.

These handcrafted features are a research baseline, not a forensic guarantee.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

FEATURE_VERSION = 1
DEFAULT_FRAMES = 16
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def _frame_feature_names() -> list[str]:
    names: list[str] = []
    for channel in "rgb":
        names.extend(f"tile_{channel}_{i}_mean" for i in range(16))
    for channel in "hsv":
        names.extend(f"{channel}_hist_{i}" for i in range(8))
    names.extend(f"edge_orientation_{i}" for i in range(8))
    for channel in "rgb":
        names.extend((f"{channel}_mean", f"{channel}_std", f"{channel}_skew"))
    names.extend([
        "laplacian_log_variance", "highfreq_mean", "highfreq_std",
        "jpeg_blockiness_h", "jpeg_blockiness_v", "color_rg_correlation", "color_rb_correlation",
    ])
    return names


def feature_names() -> list[str]:
    frame_names = _frame_feature_names()
    summary_names = ["face_detected_fraction", "face_area_fraction",
                     "temporal_diff_mean", "temporal_diff_std", "temporal_diff_p95", "temporal_diff_face_mean"]
    return ([f"frame_mean_{name}" for name in frame_names]
            + [f"frame_std_{name}" for name in frame_names] + summary_names)


def extract_video_features(path: str | Path, sample_frames: int = DEFAULT_FRAMES,
                           face_cascade_path: str = FACE_CASCADE_PATH) -> dict[str, float]:
    """Decode evenly-spaced frames and summarize face/scene visual cues."""
    source = Path(path)
    if sample_frames < 2:
        raise ValueError("sample_frames must be at least 2")
    if not source.is_file():
        raise ValueError(f"Video does not exist: {source}")
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {source}")
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0:
            raise ValueError(f"Video has no readable frame metadata: {source}")
        selected = np.unique(np.linspace(0, frame_count - 1, min(sample_frames, frame_count), dtype=int))
        detector = cv2.CascadeClassifier(face_cascade_path)
        if detector.empty():
            raise ValueError(f"Could not load face detector: {face_cascade_path}")
        frames: list[np.ndarray] = []
        visual_features: list[list[float]] = []
        detected: list[bool] = []
        face_areas: list[float] = []
        for frame_index in selected:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
            ok, frame_bgr = capture.read()
            if not ok or frame_bgr is None:
                continue
            frame, is_face, area = _face_or_center_crop(frame_bgr, detector)
            frames.append(frame)
            detected.append(is_face)
            face_areas.append(area)
            visual_features.append(_frame_features(frame))
        if len(frames) < 2:
            raise ValueError(f"Could not decode at least two frames from: {source}")
        frame_matrix = np.asarray(visual_features, dtype=np.float64)
        diffs = np.asarray([np.mean(np.abs(frames[i].astype(np.float32) - frames[i - 1].astype(np.float32)))
                            for i in range(1, len(frames))], dtype=np.float64)
        face_diffs = np.asarray([np.mean(np.abs(frames[i].astype(np.float32) - frames[i - 1].astype(np.float32)))
                                 for i in range(1, len(frames)) if detected[i] and detected[i - 1]], dtype=np.float64)
        aggregate = np.concatenate([frame_matrix.mean(axis=0), frame_matrix.std(axis=0)])
        summary = np.array([
            float(np.mean(detected)), float(np.mean(face_areas)),
            float(diffs.mean()), float(diffs.std()), float(np.percentile(diffs, 95)),
            float(face_diffs.mean()) if len(face_diffs) else 0.0,
        ])
        return {name: float(value) for name, value in zip(feature_names(), np.concatenate([aggregate, summary]))}
    finally:
        capture.release()


def _face_or_center_crop(frame_bgr: np.ndarray, detector: cv2.CascadeClassifier) -> tuple[np.ndarray, bool, float]:
    height, width = frame_bgr.shape[:2]
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                      minSize=(max(24, width // 12), max(24, height // 12)))
    if len(faces):
        x, y, w, h = max(faces, key=lambda box: int(box[2]) * int(box[3]))
        pad_x, pad_y = int(w * 0.15), int(h * 0.15)
        x0, y0 = max(0, x - pad_x), max(0, y - pad_y)
        x1, y1 = min(width, x + w + pad_x), min(height, y + h + pad_y)
        crop = frame_bgr[y0:y1, x0:x1]
        area = float(w * h / max(1, width * height))
        return _resize_rgb(crop), True, area
    # Fallback keeps non-face and difficult footage usable; it is not face detection.
    side = min(height, width)
    y0, x0 = (height - side) // 2, (width - side) // 2
    return _resize_rgb(frame_bgr[y0:y0 + side, x0:x0 + side]), False, 0.0


def _resize_rgb(frame_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(cv2.resize(frame_bgr, (128, 128), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)


def _frame_features(rgb: np.ndarray) -> list[float]:
    values: list[float] = []
    height, width = rgb.shape[:2]
    for y in range(4):
        for x in range(4):
            tile = rgb[y * height // 4:(y + 1) * height // 4, x * width // 4:(x + 1) * width // 4]
            values.extend(tile.mean(axis=(0, 1)).tolist())
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    for channel, upper in ((0, 180), (1, 256), (2, 256)):
        hist = cv2.calcHist([hsv], [channel], None, [8], [0, upper]).ravel()
        values.extend((hist / max(1.0, float(hist.sum()))).tolist())
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    angle = np.mod(np.arctan2(gy, gx), np.pi)
    edge_hist, _ = np.histogram(angle, bins=8, range=(0, np.pi), weights=np.hypot(gx, gy))
    values.extend((edge_hist / max(1.0, float(edge_hist.sum()))).tolist())
    float_rgb = rgb.astype(np.float32)
    for channel in range(3):
        plane = float_rgb[:, :, channel]
        mean, std = float(plane.mean()), float(plane.std())
        skew = float(np.mean(((plane - mean) / max(1e-5, std)) ** 3))
        values.extend((mean, std, skew))
    lap_var = float(cv2.Laplacian(gray, cv2.CV_32F).var())
    smooth = cv2.GaussianBlur(float_rgb, (0, 0), 1.0)
    residual = float_rgb - smooth
    block_h = np.abs(np.diff(float_rgb, axis=1))
    block_v = np.abs(np.diff(float_rgb, axis=0))
    regular_h = block_h[:, 7::8, :].mean() if block_h.shape[1] >= 8 else 0.0
    other_h = np.delete(block_h, np.arange(7, block_h.shape[1], 8), axis=1).mean() if block_h.shape[1] > 1 else 0.0
    regular_v = block_v[7::8, :, :].mean() if block_v.shape[0] >= 8 else 0.0
    other_v = np.delete(block_v, np.arange(7, block_v.shape[0], 8), axis=0).mean() if block_v.shape[0] > 1 else 0.0
    values.extend((np.log1p(lap_var), float(np.abs(residual).mean()), float(residual.std()),
                   float(regular_h / (other_h + 1e-5)), float(regular_v / (other_v + 1e-5))))
    corr_rg = float(np.corrcoef(float_rgb[:, :, 0].ravel(), float_rgb[:, :, 1].ravel())[0, 1])
    corr_rb = float(np.corrcoef(float_rgb[:, :, 0].ravel(), float_rgb[:, :, 2].ravel())[0, 1])
    values.extend((0.0 if not np.isfinite(corr_rg) else corr_rg,
                   0.0 if not np.isfinite(corr_rb) else corr_rb))
    return values
