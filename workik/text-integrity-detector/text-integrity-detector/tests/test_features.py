import math

from text_integrity.features import style_features


def test_features_are_finite_for_empty_and_normal_text():
    for text in ("", "Short words. Longer sentence follows here!"):
        assert all(math.isfinite(value) for value in style_features(text).values())
