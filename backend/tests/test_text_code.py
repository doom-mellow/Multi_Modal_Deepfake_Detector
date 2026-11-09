
import pytest

from app.detectors.text.analyzer import analyze_text_features
from app.detectors.code.analyzer import analyze_code_features


def test_text_feature_extraction():
    result = analyze_text_features(
        "Python is useful. Python is versatile."
    )

    assert result["word_count"] == 6
    assert result["sentence_count"] == 2
    assert result["unique_word_count"] > 0


def test_empty_text_rejected():
    with pytest.raises(ValueError):
        analyze_text_features("   ")


def test_code_feature_extraction():
    source = """
def greet():
    print("Hello")

greet()
"""

    result = analyze_code_features(source, "python")

    assert result["line_count"] > 0
    assert result["token_count"] > 0
    assert result["language_hint"] == "python"


def test_empty_code_rejected():
    with pytest.raises(ValueError):
        analyze_code_features("")
