"""Minimal deterministic media loading shared by independent detectors."""

from __future__ import annotations

import io
import shutil
import subprocess
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageOps

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
AUDIO_EXTENSIONS = {".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac"}


def load_image_tensor(path: str | Path, size: int = 224) -> torch.Tensor:
    """Read EXIF-corrected RGB image, resize, and return normalized CHW float tensor."""
    with Image.open(path) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        image = ImageOps.fit(image, (size, size), method=Image.Resampling.BILINEAR)
        array = np.asarray(image, dtype=np.float32).copy() / 255.0
    tensor = torch.from_numpy(array).permute(2, 0, 1)
    return (tensor - 0.5) / 0.5


def decode_video_frames(path: str | Path, count: int = 8) -> list[Image.Image]:
    """Uniformly sample RGB frames via ffmpeg without loading the whole video."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to decode video frames")
    if count < 1:
        raise ValueError("frame count must be positive")
    # fps=N is omitted: select up to N frames from the first 5 minutes by stride.
    # -vf fps=1/2 avoids decoding an unbounded number of frames for long inputs.
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(path), "-vf", f"fps=1/2,select='lt(n,{count})'", "-vsync", "vfr", "-frames:v", str(count), "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace")[-500:]
        raise RuntimeError(f"ffmpeg could not decode video: {detail}")
    frames: list[Image.Image] = []
    # Split the concatenated MJPEG byte stream on JPEG start/end markers. The
    # entropy-coded data escapes embedded 0xFF bytes, so these delimiters are
    # safe framing boundaries for ffmpeg's image2pipe output.
    data = result.stdout
    cursor = 0
    while len(frames) < count:
        start = data.find(bytes((0xFF, 0xD8)), cursor)
        if start < 0:
            break
        end = data.find(bytes((0xFF, 0xD9)), start + 2)
        if end < 0:
            break
        payload = data[start : end + 2]
        with Image.open(io.BytesIO(payload)) as decoded:
            decoded.load()
            frames.append(decoded.convert("RGB").copy())
        cursor = end + 2
    if not frames:
        raise RuntimeError("No video frames could be decoded")
    return frames


def pil_to_model_tensor(image: Image.Image, size: int = 224) -> torch.Tensor:
    image = ImageOps.fit(image.convert("RGB"), (size, size), method=Image.Resampling.BILINEAR)
    array = np.asarray(image, dtype=np.float32).copy() / 255.0
    return (torch.from_numpy(array).permute(2, 0, 1) - 0.5) / 0.5


def read_wav_mono(path: str | Path, target_rate: int = 16_000) -> tuple[torch.Tensor, int]:
    """Load PCM WAV through scipy; average channels and resample if necessary."""
    try:
        from scipy.io import wavfile
        from scipy.signal import resample_poly
    except ImportError as exc:
        raise RuntimeError("scipy is required to read WAV audio") from exc
    sample_rate, audio = wavfile.read(str(path))
    if audio.ndim == 2:
        audio = audio.astype(np.float32).mean(axis=1)
    elif audio.ndim != 1:
        raise ValueError("Expected mono or multichannel PCM WAV")
    if np.issubdtype(audio.dtype, np.integer):
        info = np.iinfo(audio.dtype)
        audio = audio.astype(np.float32) / max(abs(info.min), info.max)
    else:
        audio = audio.astype(np.float32)
    if sample_rate != target_rate:
        from math import gcd
        divisor = gcd(int(sample_rate), target_rate)
        audio = resample_poly(audio, target_rate // divisor, int(sample_rate) // divisor).astype(np.float32)
        sample_rate = target_rate
    audio = np.nan_to_num(audio, copy=False)
    if not len(audio):
        raise ValueError("WAV contains no audio samples")
    return torch.from_numpy(np.ascontiguousarray(audio)), int(sample_rate)


def image_resize_tensor(tensor: torch.Tensor, size: int) -> torch.Tensor:
    """Resize normalized [C,H,W] model input using bilinear interpolation."""
    return F.interpolate(tensor.unsqueeze(0), size=(size, size), mode="bilinear", align_corners=False, antialias=True)[0]