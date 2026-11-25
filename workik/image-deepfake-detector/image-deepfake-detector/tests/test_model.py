import pytest

from image_detector.model import LABELS, read_manifest


def test_label_aliases():
    assert LABELS["real"] == LABELS["authentic"] == LABELS["0"] == 0
    assert LABELS["fake"] == LABELS["deepfake"] == LABELS["generated"] == LABELS["1"] == 1


def test_manifest_validation(tmp_path):
    manifest = tmp_path / "images.csv"
    manifest.write_text("image,label\nmissing.png,real\n", encoding="utf-8")
    with pytest.raises(ValueError, match="image not found"):
        read_manifest(manifest)
