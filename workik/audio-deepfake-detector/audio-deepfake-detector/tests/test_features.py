import math

import numpy as np
from scipy.io import wavfile

from audio_detector.features import extract_audio_features, feature_names


def test_audio_feature_extraction(tmp_path):
    rate = 16_000
    seconds = 1.2
    time = np.arange(int(rate * seconds)) / rate
    signal = (0.35 * np.sin(2 * np.pi * 220 * time) + 0.02 * np.sin(2 * np.pi * 1300 * time))
    path = tmp_path / "tone.wav"
    wavfile.write(path, rate, np.int16(signal * 32767))
    features = extract_audio_features(path, max_duration=1.0)
    assert list(features) == feature_names()
    assert all(math.isfinite(value) for value in features.values())
    assert 0.99 <= features["audio_duration"] <= 1.01
    assert features["mean_rms_energy"] > 0


def test_invalid_file():
    try:
        extract_audio_features("missing.wav")
        assert False, "Expected invalid-file error"
    except ValueError as error:
        assert "does not exist" in str(error)
