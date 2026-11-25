import math

import numpy as np
from PIL import Image

from image_detector.features import extract_image_features, feature_names


def test_extract_features_for_realistic_image(tmp_path):
    rng = np.random.default_rng(17)
    pixels = rng.integers(0, 256, size=(128, 160, 3), dtype=np.uint8)
    path = tmp_path / "sample.png"
    Image.fromarray(pixels, "RGB").save(path)
    features = extract_image_features(path)
    assert list(features) == feature_names()
    assert all(math.isfinite(value) for value in features.values())
    assert features["image_width_log"] > features["image_height_log"]
    assert features["file_size_log"] > 0


def test_constant_image_features_are_finite(tmp_path):
    path = tmp_path / "constant.jpg"
    Image.fromarray(np.full((80, 80, 3), 128, dtype=np.uint8)).save(path)
    features = extract_image_features(path)
    assert all(math.isfinite(value) for value in features.values())
    assert features["gray_std"] == 0


def test_missing_image():
    try:
        extract_image_features("missing.png")
        assert False, "Expected missing-file error"
    except ValueError as error:
        assert "does not exist" in str(error)
