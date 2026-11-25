import asyncio

from fastapi import HTTPException

from app.core.scoring import verdict_fields
from app.detectors.text import classifier
from app.detectors.text.analyzer import analyze_text_features
from app.services.detector_registry import detector_registry


async def detect_text(
    content: str | None = None,
    url: str | None = None,
    file=None,
    file_metadata: dict | None = None,
    language_hint: str | None = None,
) -> dict:
    """
    Text detector.

    Always returns the linguistic measurements. If a trained classifier is
    installed (see classifier.py) it also returns an AI-generated likelihood.
    """

    if not content or not content.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide text to analyze.",
        )

    try:
        analysis = analyze_text_features(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    repeated_words = analysis["frequently_repeated_words"]

    indicators = [
        f"Character count: {analysis['character_count']}",
        f"Word count: {analysis['word_count']}",
        f"Sentence count: {analysis['sentence_count']}",
        f"Unique words: {analysis['unique_word_count']}",
        f"Lexical diversity: {analysis['lexical_diversity']}",
        f"Average sentence length: {analysis['average_sentence_length']} words",
        f"Sentence length variation: {analysis['sentence_length_variation']} words",
        f"Frequently repeated words: {len(repeated_words)}",
    ]

    response: dict = {
        "result": "analysis-complete",
        "explanation": (
            "Text analysis completed. The submitted text was inspected for "
            "lexical diversity, sentence structure, word repetition, and basic "
            "linguistic characteristics. These measurements do not establish "
            "whether the text was written by AI or a human."
        ),
        "indicators": indicators,
        "metadata": dict(analysis),
    }

    # ---- AI classifier (optional) ----
    if not classifier.is_available():
        indicators.insert(0, "AI classifier not installed: showing linguistic measurements only.")
        return response

    try:
        result = await asyncio.to_thread(classifier.classify_text, content)
    except Exception as exc:  # model/library problems must not break the endpoint
        indicators.insert(0, f"AI classifier unavailable: {exc}")
        return response

    p = result["ai_probability"]
    response["metadata"]["aiClassifier"] = result

    if not result["reliable"]:
        indicators.insert(
            0,
            f"AI-generated likelihood: {p:.0%} (text under "
            f"{classifier.MIN_WORDS_RELIABLE} words, too short to rely on)",
        )
        return response

    response.update(verdict_fields(p))
    indicators.insert(0, f"AI-generated likelihood: {p:.0%}")
    response["explanation"] = (
        f"A trained classifier estimates a {p:.0%} likelihood that this text is "
        "AI-generated. This is a statistical estimate, not proof of authorship: "
        "AI-text detectors can produce false positives (for example on "
        "non-native English writing) and false negatives (for example on "
        "paraphrased or edited AI text)."
    )
    return response


def register_text_detector() -> bool:
    detector_registry.register("text", detect_text)
    return True