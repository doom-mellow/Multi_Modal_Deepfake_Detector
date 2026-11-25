import asyncio
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.detectors.watermark.analyzer import analyze_watermark_file
from app.detectors.watermark.extra_checks import run_extra_checks
from app.services.detector_registry import detector_registry


async def detect_watermark(
    content: str | None = None,
    url: str | None = None,
    file: UploadFile | None = None,
    file_metadata: dict | None = None,
    language_hint: str | None = None,
):
    if file is None:
        raise HTTPException(
            status_code=501,
            detail="Watermark inspection currently requires an uploaded file. URL inspection is not implemented.",
        )

    data = await file.read()
    filename = file.filename or "uploaded_file"

    try:
        analysis = analyze_watermark_file(data, filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    extension = Path(filename).suffix.lower()
    try:
        extra = await asyncio.to_thread(run_extra_checks, data, extension)
    except Exception:  # extra checks must never break the base inspection
        extra = {"findings": [], "strong": False,
                 "c2pa": {"status": "error"}, "invisible": {"status": "error"}}

    c2pa, invisible = extra["c2pa"], extra["invisible"]
    c2pa_ran = c2pa["status"] in ("verified", "invalid", "no_manifest")
    invisible_ran = invisible["status"] in ("found", "not_found")

    findings = list(analysis["inspection"].get("findings", [])) + extra["findings"]
    watermark_detected = bool(findings)
    c2pa_status = "not_performed" if c2pa["status"] in ("not_installed", "not_performed") else c2pa["status"]

    breakdown = {
        "watermarkDetected": watermark_detected,
        "watermarkType": "; ".join(findings) if findings else None,
        "c2paMarkersFound": analysis["c2paMarkersFound"] or c2pa["status"] in ("verified", "invalid"),
        "c2paSignatureVerification": c2pa_status,
        "issuerOrg": c2pa.get("issuer") or analysis["issuerOrg"],
        "tamperingVerification": (
            "failed" if c2pa["status"] == "invalid"
            else "passed" if c2pa["status"] == "verified"
            else "not_performed"
        ),
        "provenanceChain": c2pa.get("provenance") or analysis["provenanceChain"],
    }

    # Drop limitations that are no longer true because a check actually ran.
    limitations = [
        item for item in analysis["limitations"]
        if not (c2pa_ran and "C2PA cryptographic" in item)
        and not (invisible_ran and "Invisible watermark decoding" in item)
        and not (c2pa["status"] == "verified" and "File tampering is not verified" in item)
    ]
    if invisible_ran:
        limitations.append(
            "Invisible watermark check covers only the Stable Diffusion scheme; other "
            "vendors' marks (e.g. SynthID) cannot be checked without their own detectors."
        )
    if c2pa["status"] == "verified":
        limitations.append("C2PA signer trust list was not evaluated; a valid signature does not mean the signer is trusted.")

    indicators = []
    if extra["strong"]:
        indicators.append("Strong evidence that this content was AI-generated (provenance or watermark data).")
    indicators += [
        f"File format: {analysis['format']}",
        f"File size: {analysis['file_size_bytes']} bytes",
        f"Watermark-related signals found: {watermark_detected}",
        f"C2PA manifest check: {c2pa_status}",
        f"Stable Diffusion invisible watermark: "
        f"{'not checked' if not invisible_ran else invisible['status'].replace('_', ' ')}",
    ]
    indicators += findings
    indicators += limitations

    return {
        "result": "analysis-complete",
        "explanation": (
            "Watermark and provenance inspection completed. A found watermark or "
            "provenance record is strong evidence about how a file was made, but "
            "the absence of one does not show that content is authentic or "
            "human-created: marks are easily stripped and many generators never add one."
        ),
        "indicators": indicators,
        "metadata": {
            "filename": analysis["filename"],
            "format": analysis["format"],
            "file_size_bytes": analysis["file_size_bytes"],
            "inspection": analysis["inspection"],
            "analysis_stage": "metadata_c2pa_and_invisible_watermark_inspection",
            "limitations": limitations,
            "aiEvidenceFound": extra["strong"],
            "c2pa": c2pa,
            "invisibleWatermark": invisible,
        },
        "watermarkBreakdown": breakdown,
    }


def register_watermark_detector():
    detector_registry.register("watermark", detect_watermark)
    return True