"""Additional watermark / provenance checks. Every check is optional and fails soft.

1. C2PA verification   needs the `c2patool` CLI on PATH (or $C2PATOOL_PATH)
2. AI metadata         PIL only (already installed)
3. SD invisible mark   needs: pip install invisible-watermark   (see notes in reply)
"""
import io
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
C2PA_EXT = IMAGE_EXT | {".mp4", ".mov", ".wav", ".mp3"}

# IPTC digital source type, also matches "compositeWithTrainedAlgorithmicMedia"
STRONG_AI_MARKER = b"trainedalgorithmicmedia"
GENERATOR_MARKERS = (b"stable diffusion", b"midjourney", b"dall-e", b"adobe firefly", b"comfyui")
SD_V1_MSG = b"StableDiffusionV1"
SDXL_BITS = [int(b) for b in bin(0b101100111110110010010000011110111011000110011110)[2:]]


# ------------------------------ C2PA ------------------------------
def _check_c2pa(data: bytes, extension: str) -> dict:
    if extension not in C2PA_EXT:
        return {"status": "not_performed"}
    exe = os.getenv("C2PATOOL_PATH") or shutil.which("c2patool")
    if not exe:
        return {"status": "not_installed"}

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"file{extension}"
        path.write_bytes(data)
        try:
            proc = subprocess.run([exe, str(path)], capture_output=True, text=True, timeout=60)
        except Exception as exc:
            return {"status": "error", "detail": str(exc)[:200]}

    out, err = (proc.stdout or "").strip(), (proc.stderr or "").strip()
    if proc.returncode != 0 or not out:
        combined = f"{out} {err}".lower()
        if not combined.strip() or "no claim" in combined or "no manifest" in combined:
            return {"status": "no_manifest"}
        return {"status": "error", "detail": (err or out)[:200]}

    try:
        report = json.loads(out)
    except ValueError:
        return {"status": "error", "detail": "could not parse c2patool output"}

    active = report.get("active_manifest")
    manifest = (report.get("manifests") or {}).get(active, {})
    state = report.get("validation_state")
    invalid = (str(state).lower() == "invalid") if state else bool(report.get("validation_status"))

    generator = manifest.get("claim_generator")
    if not generator:
        info = manifest.get("claim_generator_info") or []
        generator = info[0].get("name") if info and isinstance(info[0], dict) else None

    return {
        "status": "invalid" if invalid else "verified",
        "issuer": (manifest.get("signature_info") or {}).get("issuer"),
        "claim_generator": generator,
        "ai_declared": STRONG_AI_MARKER in out.lower().encode("utf-8", "ignore"),
        "provenance": [
            i.get("title") for i in (manifest.get("ingredients") or []) if isinstance(i, dict) and i.get("title")
        ],
    }


# --------------------------- AI metadata ---------------------------
def _check_ai_metadata(data: bytes, extension: str) -> tuple[list[str], bool]:
    findings: list[str] = []
    strong = False
    if extension not in IMAGE_EXT | {".mp4", ".mov"}:
        return findings, strong

    raw = data.lower()
    if STRONG_AI_MARKER in raw:
        findings.append("Metadata declares AI-generated media (IPTC trainedAlgorithmicMedia)")
        strong = True
    names = [m.decode() for m in GENERATOR_MARKERS if m in raw]
    if names:
        findings.append("AI tool named in metadata: " + ", ".join(names))

    if extension in IMAGE_EXT:
        try:
            from PIL import Image

            with Image.open(io.BytesIO(data)) as img:
                for key in ("parameters", "prompt", "workflow"):  # A1111 / ComfyUI PNG chunks
                    if key in img.info:
                        findings.append(f"Generation settings embedded in PNG metadata: '{key}'")
                        strong = True
        except Exception:
            pass
    return findings, strong


# ----------------------- Stable Diffusion mark -----------------------
def _check_sd_invisible(data: bytes, extension: str) -> dict:
    if extension not in IMAGE_EXT:
        return {"status": "not_performed"}
    try:
        import cv2
        import numpy as np
        from imwatermark import WatermarkDecoder
    except ImportError:
        return {"status": "not_installed"}

    try:
        bgr = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if bgr is None:
            return {"status": "error", "detail": "could not decode image"}
        if min(bgr.shape[:2]) < 256:
            return {"status": "not_performed", "detail": "image smaller than 256x256"}

        wm = bytes(WatermarkDecoder("bytes", 136).decode(bgr, "dwtDct")).ljust(17, b"\0")[:17]
        got = np.unpackbits(np.frombuffer(wm, dtype=np.uint8))
        exp = np.unpackbits(np.frombuffer(SD_V1_MSG, dtype=np.uint8))
        sim_v1 = float((got == exp).mean())

        bits = np.array(WatermarkDecoder("bits", 48).decode(bgr, "dwtDct"))[:48]
        sim_xl = float((bits == np.array(SDXL_BITS)).mean())
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:200]}

    # random data matches ~50% of bits, so require a clear margin
    if sim_v1 >= 0.9 or sim_xl >= 0.9:
        return {"status": "found", "scheme": "SD v1" if sim_v1 >= sim_xl else "SDXL"}
    return {"status": "not_found"}


# ----------------------------- entry point -----------------------------
def run_extra_checks(data: bytes, extension: str) -> dict:
    findings: list[str] = []
    strong = False

    c2pa = _check_c2pa(data, extension)
    if c2pa["status"] in ("verified", "invalid"):
        label = "Valid" if c2pa["status"] == "verified" else "INVALID"
        findings.append(
            f"{label} C2PA manifest (generator: {c2pa.get('claim_generator') or 'unknown'}, "
            f"issuer: {c2pa.get('issuer') or 'unknown'})"
        )
        if c2pa.get("ai_declared"):
            findings.append("C2PA manifest declares AI-generated content")
            strong = True

    meta_findings, meta_strong = _check_ai_metadata(data, extension)
    findings += meta_findings
    strong = strong or meta_strong

    invisible = _check_sd_invisible(data, extension)
    if invisible["status"] == "found":
        findings.append(f"Stable Diffusion invisible watermark detected ({invisible['scheme']})")
        strong = True

    return {"findings": findings, "strong": strong, "c2pa": c2pa, "invisible": invisible}
