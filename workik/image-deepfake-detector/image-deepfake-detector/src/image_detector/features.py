"""Deterministic handcrafted image artifact features for a trainable baseline."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage
from scipy.fft import dctn

FEATURE_VERSION = 1
IMAGE_SIZE = 256


def _names_per_image() -> list[str]:
    names: list[str] = []
    for channel in ("r", "g", "b"):
        names.extend(f"{channel}_hist_{i}" for i in range(16))
        names.extend(f"{channel}_block_{i}_mean" for i in range(16))
    names.extend(f"gray_dct_band_{i}" for i in range(16))
    names.extend(f"fft_radial_band_{i}" for i in range(16))
    names.extend([
        "gray_mean", "gray_std", "gray_skew", "gray_kurtosis",
        "laplacian_variance", "laplacian_abs_mean", "gradient_mean", "gradient_std",
        "high_frequency_residual_mean", "high_frequency_residual_std",
        "jpeg_blockiness_h", "jpeg_blockiness_v", "edge_density", "edge_orientation_entropy",
        "color_rg_correlation", "color_rb_correlation", "color_gb_correlation",
        "saturation_mean", "saturation_std", "hue_entropy", "exif_present",
        "alpha_channel", "image_width_log", "image_height_log", "aspect_ratio",
        "file_size_log", "unique_color_fraction", "border_to_center_difference",
    ])
    return names


def feature_names() -> list[str]:
    return _names_per_image()


def extract_image_features(path: str | Path, image_size: int = IMAGE_SIZE) -> dict[str, float]:
    """Extract RGB/statistical/frequency/compression-proxy features from an image."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Image does not exist: {path}")
    if image_size < 64:
        raise ValueError("image_size must be at least 64")
    try:
        with Image.open(path) as source:
            original_width, original_height = source.size
            exif_present = bool(source.getexif())
            alpha = source.mode in ("RGBA", "LA") or "transparency" in source.info
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.load()
            file_size = path.stat().st_size
    except Exception as exc:
        raise ValueError(f"Could not decode image {path}: {exc}") from exc
    rgb = np.asarray(image.resize((image_size, image_size), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0
    gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]).astype(np.float32)
    values: list[float] = []
    for channel_index in range(3):
        plane = rgb[:, :, channel_index]
        hist, _ = np.histogram(plane, bins=16, range=(0.0, 1.0), density=False)
        values.extend((hist / max(1, hist.sum())).tolist())
        values.extend(_grid_means(plane, 4))
    values.extend(_dct_bands(gray, 16))
    values.extend(_fft_bands(gray, 16))
    centered = gray.astype(np.float64) - float(gray.mean())
    std = float(gray.std())
    gray_skew = float(np.mean((centered / max(std, 1e-8)) ** 3))
    gray_kurtosis = float(np.mean((centered / max(std, 1e-8)) ** 4) - 3.0)
    laplacian = ndimage.laplace(gray.astype(np.float64))
    gy, gx = np.gradient(gray.astype(np.float64))
    magnitude = np.hypot(gx, gy)
    residual = gray.astype(np.float64) - ndimage.gaussian_filter(gray.astype(np.float64), sigma=1.0)
    blockiness_h, blockiness_v = _blockiness(gray)
    orientation = np.mod(np.arctan2(gy, gx), np.pi)
    orientation_hist, _ = np.histogram(orientation, bins=16, range=(0, np.pi), weights=magnitude)
    orientation_prob = orientation_hist / max(1.0, orientation_hist.sum())
    orientation_entropy = -float(np.sum(orientation_prob[orientation_prob > 0] * np.log2(orientation_prob[orientation_prob > 0])))
    edges = magnitude > (float(np.percentile(magnitude, 80)) if magnitude.size else 0)
    correlations = []
    for a, b in ((0, 1), (0, 2), (1, 2)):
        first, second = rgb[:, :, a].ravel(), rgb[:, :, b].ravel()
        first_std, second_std = float(first.std()), float(second.std())
        corr = float(np.mean((first - first.mean()) * (second - second.mean())) / (first_std * second_std)) if first_std > 1e-8 and second_std > 1e-8 else 0.0
        correlations.append(corr if np.isfinite(corr) else 0.0)
    hsv = np.asarray(image.resize((image_size, image_size), Image.Resampling.LANCZOS).convert("HSV"), dtype=np.float32)
    saturation = hsv[:, :, 1] / 255.0
    hue_hist, _ = np.histogram(hsv[:, :, 0], bins=16, range=(0, 256))
    hue_prob = hue_hist / max(1, hue_hist.sum())
    hue_entropy = -float(np.sum(hue_prob[hue_prob > 0] * np.log2(hue_prob[hue_prob > 0])))
    border = np.concatenate([gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]])
    center = gray[image_size // 4:3 * image_size // 4, image_size // 4:3 * image_size // 4]
    rgb_quantized = (rgb * 31).astype(np.uint8).reshape(-1, 3)
    unique_color_fraction = len(np.unique(rgb_quantized, axis=0)) / len(rgb_quantized)
    values.extend([
        float(gray.mean()), std, gray_skew, gray_kurtosis,
        float(np.var(laplacian)), float(np.mean(np.abs(laplacian))),
        float(magnitude.mean()), float(magnitude.std()),
        float(np.abs(residual).mean()), float(residual.std()),
        blockiness_h, blockiness_v, float(edges.mean()), orientation_entropy,
        *correlations, float(saturation.mean()), float(saturation.std()), hue_entropy,
        float(exif_present), float(alpha), float(np.log1p(original_width)),
        float(np.log1p(original_height)), float(original_width / max(1, original_height)),
        float(np.log1p(file_size)), float(unique_color_fraction),
        float(abs(border.mean() - center.mean())),
    ])
    if len(values) != len(feature_names()):
        raise RuntimeError(f"Image feature schema mismatch: got {len(values)}, expected {len(feature_names())}")
    return {name: float(value) for name, value in zip(feature_names(), values)}


def _grid_means(image: np.ndarray, grid: int) -> list[float]:
    h, w = image.shape
    return [float(image[y * h // grid:(y + 1) * h // grid,
                        x * w // grid:(x + 1) * w // grid].mean())
            for y in range(grid) for x in range(grid)]


def _dct_bands(gray: np.ndarray, bands: int) -> list[float]:
    coefficients = dctn(gray.astype(np.float64), type=2, norm="ortho")
    h, w = coefficients.shape
    y, x = np.indices((h, w))
    radius = np.sqrt((y / h) ** 2 + (x / w) ** 2) / np.sqrt(2)
    edges = np.linspace(0, 1, bands + 1)
    energies = []
    for index in range(bands):
        mask = (radius >= edges[index]) & (radius < edges[index + 1])
        energies.append(float(np.log1p(np.mean(np.abs(coefficients[mask])))) if np.any(mask) else 0.0)
    total = sum(energies) + 1e-12
    return [value / total for value in energies]


def _fft_bands(gray: np.ndarray, bands: int) -> list[float]:
    spectrum = np.abs(np.fft.fftshift(np.fft.fft2(gray.astype(np.float64))))
    h, w = spectrum.shape
    y, x = np.indices((h, w))
    radius = np.sqrt(((y - h / 2) / (h / 2)) ** 2 + ((x - w / 2) / (w / 2)) ** 2) / np.sqrt(2)
    radial_edges = np.linspace(0, 1, bands + 1)
    energy = []
    for index in range(bands):
        mask = (radius >= radial_edges[index]) & (radius < radial_edges[index + 1])
        energy.append(float(np.mean(spectrum[mask])) if np.any(mask) else 0.0)
    total = sum(energy) + 1e-12
    return [value / total for value in energy]


def _blockiness(gray: np.ndarray) -> tuple[float, float]:
    horizontal = np.abs(np.diff(gray, axis=1))
    vertical = np.abs(np.diff(gray, axis=0))
    h_regular = horizontal[:, 7::8].mean() if horizontal.shape[1] >= 8 else 0.0
    h_other = np.delete(horizontal, np.arange(7, horizontal.shape[1], 8), axis=1).mean() if horizontal.shape[1] > 1 else 0.0
    v_regular = vertical[7::8, :].mean() if vertical.shape[0] >= 8 else 0.0
    v_other = np.delete(vertical, np.arange(7, vertical.shape[0], 8), axis=0).mean() if vertical.shape[0] > 1 else 0.0
    return float(h_regular / (h_other + 1e-8)), float(v_regular / (v_other + 1e-8))
