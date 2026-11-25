import csv

import pytest

from video_detector.model import LABELS, read_manifest


def test_label_aliases():
    assert LABELS["real"] == LABELS["authentic"] == LABELS["0"] == 0
    assert LABELS["fake"] == LABELS["deepfake"] == LABELS["1"] == 1


def test_manifest_validation(tmp_path):
    path = tmp_path / "manifest.csv"
    path.write_text("video,label\nclip.avi,real\n", encoding="utf-8")
    with pytest.raises(ValueError, match="video not found"):
        read_manifest(path)
