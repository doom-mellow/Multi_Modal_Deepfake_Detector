"""Turns an AI probability (0..1) into the API's `result` / `confidence` fields."""

AI_THRESHOLD = 0.70
HUMAN_THRESHOLD = 0.30

# CONFIRM THIS against your frontend. How is `confidence` expected to arrive?
#   1.0   -> 0..1    (what the filename demo override in detection.py returns)
#   100.0 -> 0..100  (what the DetectionResponse schema declares)
CONFIDENCE_SCALE = 1.0


def verdict_fields(ai_probability: float) -> dict:
    """Return {"result", "confidence"}.

    Scores in the middle band return result="analysis-complete" (the value your
    detectors already use) with no confidence, instead of forcing a guess.
    """
    p = max(0.0, min(1.0, float(ai_probability)))
    if p >= AI_THRESHOLD:
        return {"result": "ai-generated", "confidence": round(p * CONFIDENCE_SCALE, 4)}
    if p <= HUMAN_THRESHOLD:
        return {"result": "real", "confidence": round((1 - p) * CONFIDENCE_SCALE, 4)}
    return {"result": "analysis-complete"}
