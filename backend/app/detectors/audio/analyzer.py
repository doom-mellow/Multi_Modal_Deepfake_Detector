
import io
import wave
from pathlib import Path

import miniaudio
import numpy as np


MAX_ANALYSIS_SAMPLES = 1_000_000
FFT_SIZE = 2048
MAX_SPECTRAL_FRAMES = 128


def _decode_pcm(raw: bytes, sample_width: int) -> np.ndarray:
    """Decode WAV PCM samples into normalized float32 values."""

    if sample_width == 1:
        samples = np.frombuffer(raw, dtype=np.uint8)
        return (samples.astype(np.float32) - 128.0) / 128.0

    if sample_width == 2:
        samples = np.frombuffer(raw, dtype="<i2")
        return samples.astype(np.float32) / 32768.0

    if sample_width == 3:
        data = np.frombuffer(raw, dtype=np.uint8)

        if len(data) % 3 != 0:
            raise ValueError("Invalid 24-bit PCM audio data.")

        data = data.reshape(-1, 3)

        samples = (
            data[:, 0].astype(np.int32)
            | (data[:, 1].astype(np.int32) << 8)
            | (data[:, 2].astype(np.int32) << 16)
        )

        samples = np.where(
            samples & 0x800000 != 0,
            samples - 0x1000000,
            samples,
        )

        return samples.astype(np.float32) / 8388608.0

    if sample_width == 4:
        samples = np.frombuffer(raw, dtype="<i4")
        return samples.astype(np.float32) / 2147483648.0

    raise ValueError(
        f"Unsupported PCM bit depth: {sample_width * 8} bits."
    )


def _decode_audio(audio_bytes: bytes, filename: str):
    """Decode WAV or MP3 into normalized float32 samples."""

    extension = Path(filename).suffix.lower()

    if extension == ".wav":
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as audio:
                channels = audio.getnchannels()
                sample_rate = audio.getframerate()
                sample_width = audio.getsampwidth()
                total_frames = audio.getnframes()
                compression = audio.getcomptype()

                if compression != "NONE":
                    raise ValueError(
                        "Only uncompressed PCM WAV audio is supported."
                    )

                if channels < 1 or sample_rate < 1:
                    raise ValueError(
                        "Invalid audio channel or sample rate."
                    )

                if total_frames < 1:
                    raise ValueError(
                        "The WAV file contains no audio frames."
                    )

                raw = audio.readframes(total_frames)

        except wave.Error as exc:
            raise ValueError(
                "Unable to read this file as a valid WAV file. "
                "Please upload an uncompressed PCM WAV file."
            ) from exc

        except EOFError as exc:
            raise ValueError(
                "The WAV file appears to be incomplete or corrupted."
            ) from exc

        expected_bytes = total_frames * channels * sample_width

        if len(raw) != expected_bytes:
            raise ValueError(
                "The audio data is incomplete or corrupted."
            )

        samples = _decode_pcm(raw, sample_width)
        samples = samples.reshape(-1, channels)

        metadata = {
            "format": "WAV",
            "encoding": "PCM",
            "bit_depth": sample_width * 8,
            "sample_rate_hz": sample_rate,
            "channels": channels,
            "total_frames": total_frames,
        }

    elif extension == ".mp3":
        try:
            decoded = miniaudio.decode(
                audio_bytes,
                output_format=miniaudio.SampleFormat.FLOAT32,
            )

            sample_rate = decoded.sample_rate
            channels = decoded.nchannels

            samples = np.asarray(
                decoded.samples,
                dtype=np.float32,
            )

            if channels < 1 or sample_rate < 1 or samples.size == 0:
                raise ValueError("The MP3 file contains invalid audio data.")

            samples = samples.reshape(-1, channels)

        except Exception as exc:
            if isinstance(exc, ValueError):
                raise

            raise ValueError(
                "Unable to decode this MP3 file. "
                "Please upload a valid MP3 audio file."
            ) from exc

        total_frames = len(samples)

        metadata = {
            "format": "MP3",
            "encoding": "MPEG audio decoded to float32",
            "bit_depth": None,
            "sample_rate_hz": sample_rate,
            "channels": channels,
            "total_frames": total_frames,
        }

    else:
        raise ValueError(
            "Unsupported audio format. Currently supported formats: WAV and MP3."
        )

    return samples, metadata


def _spectral_features(
    mono: np.ndarray,
    sample_rate: int,
) -> dict:
    """Calculate spectral centroid and flatness from sampled windows."""

    if len(mono) < FFT_SIZE:
        return {
            "spectral_centroid_hz": None,
            "spectral_flatness": None,
        }

    window = np.hanning(FFT_SIZE).astype(np.float32)

    frequencies = np.fft.rfftfreq(
        FFT_SIZE,
        d=1.0 / sample_rate,
    )

    max_start = len(mono) - FFT_SIZE

    frame_count = min(
        MAX_SPECTRAL_FRAMES,
        max(1, max_start // FFT_SIZE + 1),
    )

    starts = np.linspace(
        0,
        max_start,
        num=frame_count,
        dtype=int,
    )

    centroids = []
    flatness_values = []

    for start in starts:
        frame = mono[start:start + FFT_SIZE]

        spectrum = np.abs(
            np.fft.rfft(frame * window)
        ).astype(np.float64)

        power = spectrum ** 2
        total_power = float(np.sum(power))

        if total_power <= 1e-12:
            continue

        centroid = float(
            np.sum(frequencies * power) / total_power
        )

        positive_power = power[1:] + 1e-12

        geometric_mean = float(
            np.exp(np.mean(np.log(positive_power)))
        )

        arithmetic_mean = float(
            np.mean(positive_power)
        )

        flatness = geometric_mean / max(
            arithmetic_mean,
            1e-12,
        )

        centroids.append(centroid)
        flatness_values.append(flatness)

    if not centroids:
        return {
            "spectral_centroid_hz": None,
            "spectral_flatness": None,
        }

    return {
        "spectral_centroid_hz": round(
            float(np.mean(centroids)), 2
        ),
        "spectral_flatness": round(
            float(np.mean(flatness_values)), 6
        ),
    }


def analyze_audio(
    audio_bytes: bytes,
    filename: str = "audio.wav",
) -> dict:
    """
    Inspect WAV and MP3 audio files.

    Measures technical audio characteristics.
    Does not classify audio as AI-generated or authentic.
    """

    if not audio_bytes:
        raise ValueError("The uploaded audio file is empty.")

    samples, metadata = _decode_audio(
        audio_bytes,
        filename,
    )

    original_sample_count = len(samples)

    duration = original_sample_count / metadata["sample_rate_hz"]

    if original_sample_count > MAX_ANALYSIS_SAMPLES:
        stride = int(
            np.ceil(original_sample_count / MAX_ANALYSIS_SAMPLES)
        )
        samples = samples[::stride]

    samples = samples.astype(np.float32)

    mono = np.mean(samples, axis=1)

    rms = float(np.sqrt(np.mean(samples ** 2)))
    peak = float(np.max(np.abs(samples)))

    silence_ratio = float(
        np.mean(np.abs(mono) < 0.001)
    )

    clipping_ratio = float(
        np.mean(np.abs(samples) >= 0.999)
    )

    if len(mono) > 1:
        zero_crossing_rate = float(
            np.mean(
                np.signbit(mono[1:]) != np.signbit(mono[:-1])
            )
        )
    else:
        zero_crossing_rate = 0.0

    spectral = _spectral_features(
        mono,
        metadata["sample_rate_hz"],
    )

    return {
        "filename": Path(filename).name,
        **metadata,
        "duration_seconds": round(duration, 3),
        "file_size_bytes": len(audio_bytes),
        "analysis_samples": len(samples),
        "rms_energy": round(rms, 6),
        "peak_amplitude": round(peak, 6),
        "silence_ratio": round(silence_ratio, 6),
        "clipping_ratio": round(clipping_ratio, 6),
        "zero_crossing_rate": round(
            zero_crossing_rate, 6
        ),
        **spectral,
        "analysis_stage": "audio_signal_and_spectral_analysis",
    }
