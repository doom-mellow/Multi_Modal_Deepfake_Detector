import csv

import pytest
from scipy.io import wavfile
import numpy as np

from audio_detector.model import LABELS, read_manifest


def test_label_aliases():
    assert LABELS["real"] == LABELS["bonafide"] == LABELS["0"] == 0
    assert LABELS["fake"] == LABELS["spoof"] == LABELS["1"] == 1


def test_manifest_checks_files_and_minimums(tmp_path):
    rate = 16_000
    wave = tmp_path / "clip.wav"
    wavfile.write(wave, rate, np.zeros(rate, dtype=np.int16))
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("audio,label\nclip.wav,real\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least 20"):
        read_manifest(manifest)
