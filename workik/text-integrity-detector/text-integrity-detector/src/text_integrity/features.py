"""Language-independent writing features used by the AI-text classifier."""
from __future__ import annotations

import math
import re
from collections import Counter

WORD_RE = re.compile(r"\b[\w]+(?:['’][\w]+)?\b", re.UNICODE)
SENTENCE_RE = re.compile(r"[^.!?\n]+(?:[.!?]+|$)")


def style_features(text: str) -> dict[str, float]:
    words = WORD_RE.findall(text.lower())
    lines = text.splitlines() or [""]
    sentences = [part.strip() for part in SENTENCE_RE.findall(text) if part.strip()]
    word_counts = Counter(words)
    word_total = len(words)
    sentence_lengths = [len(WORD_RE.findall(sentence)) for sentence in sentences]
    word_lengths = [len(word) for word in words]
    punctuation = sum(not char.isalnum() and not char.isspace() for char in text)
    entropy = 0.0
    if word_total:
        entropy = -sum((count / word_total) * math.log2(count / word_total) for count in word_counts.values())
    return {
        "log_chars": math.log1p(len(text)),
        "log_words": math.log1p(word_total),
        "log_sentences": math.log1p(len(sentences)),
        "avg_word_length": sum(word_lengths) / max(1, word_total),
        "word_length_std": _std(word_lengths),
        "avg_sentence_length": sum(sentence_lengths) / max(1, len(sentence_lengths)),
        "sentence_length_std": _std(sentence_lengths),
        "sentence_length_cv": _std(sentence_lengths) / max(1.0, sum(sentence_lengths) / max(1, len(sentence_lengths))),
        "unique_word_ratio": len(word_counts) / max(1, word_total),
        "word_entropy": entropy,
        "hapax_ratio": sum(count == 1 for count in word_counts.values()) / max(1, word_total),
        "repeated_word_ratio": sum(count > 1 for count in word_counts.values()) / max(1, len(word_counts)),
        "paragraph_count": float(sum(bool(line.strip()) for line in lines) - sum(bool(lines[i - 1].strip()) and bool(line.strip()) for i, line in enumerate(lines) if i > 0) + 1 if text.strip() else 0),
        "blank_line_ratio": sum(not line.strip() for line in lines) / max(1, len(lines)),
        "punctuation_ratio": punctuation / max(1, len(text)),
        "comma_ratio": text.count(",") / max(1, len(sentences)),
        "semicolon_ratio": text.count(";") / max(1, len(sentences)),
        "exclamation_ratio": text.count("!") / max(1, len(sentences)),
        "question_ratio": text.count("?") / max(1, len(sentences)),
        "parenthesis_ratio": (text.count("(") + text.count(")")) / max(1, word_total),
        "uppercase_ratio": sum(char.isupper() for char in text) / max(1, len(text)),
        "digit_ratio": sum(char.isdigit() for char in text) / max(1, len(text)),
        "contraction_ratio": len(re.findall(r"\b\w+['’](?:t|s|re|ve|ll|d|m)\b", text.lower())) / max(1, word_total),
        "transition_ratio": sum(words.count(word) for word in ("however", "therefore", "moreover", "furthermore", "additionally", "consequently", "thus", "nevertheless")) / max(1, word_total),
        "first_person_ratio": sum(words.count(word) for word in ("i", "we", "my", "our", "me", "us")) / max(1, word_total),
        "hedge_ratio": sum(words.count(word) for word in ("perhaps", "possibly", "likely", "might", "could", "may", "seem", "suggest")) / max(1, word_total),
        "very_short_sentence_ratio": sum(length <= 5 for length in sentence_lengths) / max(1, len(sentence_lengths)),
        "long_sentence_ratio": sum(length >= 30 for length in sentence_lengths) / max(1, len(sentence_lengths)),
    }


def _std(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))
