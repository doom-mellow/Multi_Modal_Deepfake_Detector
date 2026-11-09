
import re
from collections import Counter


def analyze_text_features(content: str) -> dict:
    text = content.strip()

    if not text:
        raise ValueError("Text content cannot be empty.")

    words = re.findall(r"\b[\w']+\b", text.lower())
    sentences = [
        sentence.strip()
        for sentence in re.split(r"[.!?]+", text)
        if sentence.strip()
    ]

    if not words:
        raise ValueError("No readable words were found.")

    word_counts = Counter(words)

    sentence_lengths = [
        len(re.findall(r"\b[\w']+\b", sentence))
        for sentence in sentences
    ]

    average_sentence_length = (
        sum(sentence_lengths) / len(sentence_lengths)
        if sentence_lengths else 0
    )

    sentence_length_variation = (
        max(sentence_lengths) - min(sentence_lengths)
        if sentence_lengths else 0
    )

    repeated_words = {
        word: count
        for word, count in word_counts.items()
        if count > 3
    }

    return {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "unique_word_count": len(word_counts),
        "lexical_diversity": round(
            len(word_counts) / len(words), 4
        ),
        "average_sentence_length": round(
            average_sentence_length, 2
        ),
        "sentence_length_variation": sentence_length_variation,
        "frequently_repeated_words": repeated_words,
    }
