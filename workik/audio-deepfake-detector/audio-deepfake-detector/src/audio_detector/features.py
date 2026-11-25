"""Audio loading and hand-crafted speech/audio forensic feature extraction."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy import signal
from scipy.fft import dct
from scipy.io import wavfile

FEATURE_VERSION = 1
DEFAULT_SAMPLE_RATE = 16_000
DEFAULT_DURATION = 10.0


def _names_per_frame() -> list[str]:
    names: list[str] = []
    names.extend(f"mfcc_{i}" for i in range(1, 14))
    names.extend(f"logmel_{i}" for i in range(20))
    names.extend(["spectral_centroid", "spectral_bandwidth", "spectral_rolloff", "spectral_flatness",
                  "zero_crossing_rate", "rms_energy", "spectral_flux", "harmonic_ratio"])
    names.extend(f"mfcc_delta_{i}" for i in range(1, 14))
    return names


def feature_names() -> list[str]:
    frame = _names_per_frame()
    summary = ["audio_duration", "silence_ratio", "clipping_ratio", "waveform_crest_factor",
               "channel_count", "sample_rate_log2", "segment_count"]
    names = [f"mean_{name}" for name in frame] + [f"std_{name}" for name in frame]
    names.extend(summary)
    return names


def extract_audio_features(path: str | Path, target_rate: int = DEFAULT_SAMPLE_RATE,
                           max_duration: float = DEFAULT_DURATION) -> dict[str, float]:
    """Read audio via FFmpeg or WAV fallback and summarize spectral/temporal cues."""
    source = Path(path)
    if not source.is_file():
        raise ValueError(f"Audio file does not exist: {source}")
    if target_rate < 8_000 or max_duration <= 0:
        raise ValueError("target_rate must be at least 8000 Hz and max_duration must be positive")
    audio, source_rate, channels = _load_audio(source, target_rate, max_duration)
    if audio.size < 256:
        raise ValueError(f"Audio is too short or empty: {source}")
    frame_features = _frame_features(audio, target_rate)
    matrix = np.asarray(frame_features, dtype=np.float64)
    if matrix.shape[0] == 0:
        raise ValueError(f"Audio has no analyzable frames: {source}")
    audio_duration = len(audio) / target_rate
    abs_audio = np.abs(audio)
    peak = float(abs_audio.max(initial=0.0))
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    segment_count = _voiced_segments(audio, target_rate)
    summary = [
        audio_duration,
        float(np.mean(abs_audio < 1e-3)),
        float(np.mean(abs_audio >= 0.999)),
        peak / max(rms, 1e-9),
        float(channels),
        float(np.log2(max(1, source_rate))),
        float(segment_count),
    ]
    values = np.concatenate([matrix.mean(axis=0), matrix.std(axis=0), summary])
    if len(values) != len(feature_names()):
        raise RuntimeError(f"Feature schema mismatch: got {len(values)}, expected {len(feature_names())}")
    return dict(zip(feature_names(), map(float, values)))


def _load_audio(path: Path, target_rate: int, max_duration: float) -> tuple[np.ndarray, int, int]:
    """Use FFmpeg for common formats; fall back to scipy for PCM WAV files."""
    import shutil
    import subprocess

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        command = [ffmpeg, "-nostdin", "-v", "error", "-i", str(path), "-t", str(max_duration),
                   "-ac", "1", "-ar", str(target_rate), "-f", "f32le", "pipe:1"]
        try:
            result = subprocess.run(command, capture_output=True, check=True, timeout=120)
            audio = np.frombuffer(result.stdout, dtype="<f4").astype(np.float32, copy=True)
            if audio.size:
                return np.clip(audio, -1, 1), target_rate, 1
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            detail = exc.stderr.decode("utf-8", errors="replace")[:240] if getattr(exc, "stderr", None) else str(exc)
            if path.suffix.lower() not in {".wav", ".wave"}:
                raise ValueError(f"FFmpeg could not decode {path}: {detail}") from exc
    try:
        sample_rate, raw = wavfile.read(path, mmap=False)
    except Exception as exc:
        raise ValueError(f"Could not decode audio {path}; install FFmpeg for compressed formats: {exc}") from exc
    channel_count = 1 if raw.ndim == 1 else int(raw.shape[1])
    if raw.ndim == 2:
        raw = raw.astype(np.float64).mean(axis=1)
    audio = _normalize_pcm(raw)
    audio = audio[:int(sample_rate * max_duration)]
    if sample_rate != target_rate:
        divisor = int(np.gcd(sample_rate, target_rate))
        audio = signal.resample_poly(audio, target_rate // divisor, sample_rate // divisor).astype(np.float32)
    return audio, int(sample_rate), channel_count


def _normalize_pcm(raw: np.ndarray) -> np.ndarray:
    if np.issubdtype(raw.dtype, np.integer):
        info = np.iinfo(raw.dtype)
        scale = float(max(abs(info.min), info.max))
        result = raw.astype(np.float32) / scale
    else:
        result = raw.astype(np.float32)
    return np.clip(result, -1.0, 1.0)


def _frame_features(audio: np.ndarray, rate: int) -> list[list[float]]:
    frame_length = 400  # 25 ms at 16 kHz
    hop_length = 160  # 10 ms
    if len(audio) < frame_length:
        audio = np.pad(audio, (0, frame_length - len(audio)))
    _, _, spectrum = signal.stft(audio, fs=rate, window="hann", nperseg=frame_length,
                                 noverlap=frame_length - hop_length, nfft=512,
                                 boundary=None, padded=False)
    magnitude = np.abs(spectrum).astype(np.float64)
    power = magnitude ** 2
    mel_filters = _mel_filterbank(rate, 512, 32)
    mel_energy = np.maximum(mel_filters @ power, 1e-10)
    logmel = np.log(mel_energy)
    cepstra = dct(logmel, type=2, axis=0, norm="ortho")[:14]
    mfcc = cepstra[1:14]
    mfcc_delta = np.gradient(mfcc, axis=1) if mfcc.shape[1] > 1 else np.zeros_like(mfcc)
    frequencies = np.fft.rfftfreq(512, d=1.0 / rate)
    frame_energy = magnitude.sum(axis=0) + 1e-12
    centroid = (frequencies[:, None] * magnitude).sum(axis=0) / frame_energy
    bandwidth = np.sqrt((np.square(frequencies[:, None] - centroid) * magnitude).sum(axis=0) / frame_energy)
    cumulative = np.cumsum(power, axis=0)
    rolloff_indices = np.argmax(cumulative >= (0.85 * cumulative[-1:]), axis=0)
    rolloff = frequencies[rolloff_indices]
    flatness = np.exp(np.mean(np.log(power + 1e-12), axis=0)) / (np.mean(power, axis=0) + 1e-12)
    frames = np.lib.stride_tricks.sliding_window_view(audio, frame_length)[::hop_length]
    zero_crossing = np.mean(np.diff(np.signbit(frames), axis=1), axis=1)
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    spectral_flux = np.zeros(magnitude.shape[1], dtype=np.float64)
    if magnitude.shape[1] > 1:
        normalized = magnitude / (np.linalg.norm(magnitude, axis=0, keepdims=True) + 1e-12)
        spectral_flux[1:] = np.sqrt(np.sum(np.maximum(0.0, np.diff(normalized, axis=1)) ** 2, axis=0))
    # Approximate harmonic-to-noise ratio via periodic/autocorrelation peak.
    harmonic = np.zeros(len(rms), dtype=np.float64)
    for index, frame in enumerate(frames[:len(harmonic)]):
        centered = frame.astype(np.float64) - frame.mean()
        corr = signal.correlate(centered, centered, mode="full", method="fft")[len(centered) - 1:]
        min_lag, max_lag = max(1, rate // 500), min(len(corr) - 1, rate // 60)
        harmonic[index] = float(np.max(corr[min_lag:max_lag + 1]) / max(corr[0], 1e-12)) if max_lag > min_lag else 0.0
    parts = [mfcc.T, logmel[:20].T, np.column_stack([centroid, bandwidth, rolloff, flatness,
             zero_crossing[:len(rms)], rms, spectral_flux[:len(rms)], harmonic]), mfcc_delta.T]
    return np.column_stack(parts).astype(np.float32).tolist()


def _mel_filterbank(rate: int, n_fft: int, n_filters: int) -> np.ndarray:
    def hz_to_mel(hz: float) -> float:
        return 2595.0 * np.log10(1.0 + hz / 700.0)
    def mel_to_hz(mel: float) -> float:
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)
    mel_points = np.linspace(hz_to_mel(0), hz_to_mel(rate / 2), n_filters + 2)
    hz_points = mel_to_hz(mel_points)
    bins = np.floor((n_fft + 1) * hz_points / rate).astype(int)
    filters = np.zeros((n_filters, n_fft // 2 + 1), dtype=np.float64)
    for index in range(n_filters):
        left, center, right = bins[index:index + 3]
        center = max(center, left + 1)
        right = max(right, center + 1)
        for bin_index in range(left, min(center, filters.shape[1])):
            filters[index, bin_index] = (bin_index - left) / (center - left)
        for bin_index in range(center, min(right, filters.shape[1])):
            filters[index, bin_index] = (right - bin_index) / (right - center)
    return filters


def _voiced_segments(audio: np.ndarray, rate: int) -> int:
    frame = max(1, rate // 20)  # 50 ms
    count = max(1, len(audio) // frame)
    energies = np.asarray([np.sqrt(np.mean(audio[i * frame:min(len(audio), (i + 1) * frame)] ** 2))
                           for i in range(count)])
    threshold = max(0.008, float(np.percentile(energies, 65)) * 0.25)
    active = energies > threshold
    starts = active & ~np.r_[False, active[:-1]]
    return int(starts.sum())
