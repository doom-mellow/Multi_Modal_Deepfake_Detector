import asyncio
import os
from pathlib import Path

from fastapi import HTTPException

from app.core.scoring import verdict_fields
from app.detectors.code.ai_likelihood import analyze as analyze_ai_likelihood
from app.detectors.code.analyzer import analyze_code_features
from app.services.detector_registry import detector_registry

# Optional trained model (made with: python ai_likelihood.py train ...).
# Without it, the built-in heuristic is used.
_MODEL_ENV = os.getenv("CODE_MODEL_PATH")
CODE_MODEL_PATH = _MODEL_ENV if _MODEL_ENV and Path(_MODEL_ENV).exists() else None


async def detect_code(
    content: str | None = None,
    url: str | None = None,
    file=None,
    file_metadata: dict | None = None,
    language_hint: str | None = None,
) -> dict:
    """
    Code detector.

    Always returns the structural measurements (codeBreakdown is unchanged).
    Also returns an AI-generated likelihood with the signals behind it.
    """

    if not content or not content.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide source code to analyze.",
        )

    try:
        analysis = analyze_code_features(
            content=content,
            language_hint=language_hint or "auto",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    indicators = [
        f"Language hint: {analysis['language_hint']}",
        f"Line count: {analysis['line_count']}",
        f"Nonempty lines: {analysis['nonempty_line_count']}",
        f"Token count: {analysis['token_count']}",
        f"Unique tokens: {analysis['unique_token_count']}",
        f"Token diversity: {analysis['token_diversity']}",
        f"Comment lines: {analysis['comment_line_count']}",
        f"Comment-line ratio: {analysis['comment_line_ratio']}",
        f"Average line length: {analysis['average_line_length']}",
        f"Repeated lines: {len(analysis['repeated_lines'])}",
    ]

    response: dict = {
        "result": "analysis-complete",
        "explanation": (
            "Code analysis completed. The submitted source code was inspected "
            "for token diversity, line structure, comments, and repeated lines."
        ),
        "indicators": indicators,
        "metadata": dict(analysis),
        "codeBreakdown": analysis,
    }

    # ---- AI-likelihood (heuristic, or trained model if configured) ----
    try:
        ai = await asyncio.to_thread(analyze_ai_likelihood, content, CODE_MODEL_PATH)
    except (Exception, SystemExit) as exc:  # never let the scorer break the endpoint
        indicators.insert(0, f"AI-likelihood scoring unavailable: {exc}")
        return response

    p = ai["ai_likelihood"]
    signals = [
        {"name": name, "score": round(score, 2), "note": note}
        for name, score, note in ai["signals"]
        if abs(score) >= 0.05
    ]
    response["metadata"]["aiLikelihood"] = {
        "probability": p,
        "label": ai["label"],
        "mode": ai["mode"],
        "confidence": ai["confidence"],
        "signals": signals,
    }

    top = [
        f"{'Leans AI' if s['score'] > 0 else 'Leans human'}: {s['name']} ({s['note']})"
        for s in signals[:4]
    ]
    indicators[0:0] = [f"AI-generated likelihood: {p:.0%} ({ai['mode']})"] + top

    if ai["confidence"] == "low":
        indicators.insert(1, "Snippet is very short; the likelihood is not meaningful.")
        return response

    response.update(verdict_fields(p))
    response["explanation"] = (
        f"Style analysis estimates a {p:.0%} likelihood that this code is "
        f"AI-generated ({ai['mode']}). This is a statistical estimate, not proof "
        "of authorship: auto-formatters, linters, and light human edits can all "
        "change these signals."
    )
    return response


def register_code_detector() -> bool:
    detector_registry.register("code", detect_code)
    return True