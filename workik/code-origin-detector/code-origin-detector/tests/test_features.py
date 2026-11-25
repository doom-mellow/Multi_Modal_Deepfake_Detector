from pathlib import Path
import pytest

from code_origin_detector.features import detect_language, language_from_path, normalize_language, style_features


def test_languages_and_aliases():
    assert [normalize_language(x) for x in ("python", "java", "c", "cpp", "javascript", "c++", "js")] == [
        "python", "java", "c", "cpp", "javascript", "cpp", "javascript"
    ]


@pytest.mark.parametrize(("filename", "expected"), [
    ("main.py", "python"), ("Main.java", "java"), ("main.c", "c"),
    ("main.cpp", "cpp"), ("app.js", "javascript"),
])
def test_language_from_path(filename, expected):
    assert language_from_path(filename) == expected


def test_unknown_extension_requires_override():
    with pytest.raises(ValueError):
        language_from_path("source.txt")


def test_detection_and_features_are_finite():
    samples = [
        ("def greet(name):\n    return f'Hi {name}'\n", "python"),
        ("public class Hello { public static void main(String[] a) {} }", "java"),
        ("#include <stdio.h>\nint main(void) { return 0; }", "c"),
        ("#include <iostream>\nint main() { std::cout << 1; }", "cpp"),
        ("const greet = (name) => console.log(name);", "javascript"),
    ]
    for code, language in samples:
        assert detect_language(code) == language
        features = style_features({"code": code, "language": language})
        assert features[f"lang_{language}"] == 1.0
        assert all(value == value and abs(value) != float("inf") for value in features.values())
