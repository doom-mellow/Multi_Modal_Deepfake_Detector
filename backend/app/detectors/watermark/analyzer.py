
import io
from pathlib import Path

from PIL import Image


C2PA_MARKERS = (
    b"c2pa",
    b"jumbf",
    b"content credentials",
    b"contentcredentials",
    b"manifest",
)

WATERMARK_METADATA_KEYS = {
    "watermark",
    "watermarking",
    "digital watermark",
    "digital_watermark",
    "c2pa",
    "content credentials",
    "content_credentials",
}


def _inspect_image(data: bytes) -> dict:
    findings = []

    with Image.open(io.BytesIO(data)) as image:
        metadata = {
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "metadata_keys": list(image.info.keys()),
        }

        for key, value in image.info.items():
            normalized_key = str(key).lower().replace("-", "_")

            if any(
                marker in normalized_key
                for marker in WATERMARK_METADATA_KEYS
            ):
                findings.append(
                    f"Watermark-related metadata key: {key}"
                )

            if isinstance(value, bytes):
                searchable = value.lower()
            else:
                searchable = str(value).lower().encode(
                    "utf-8", errors="ignore"
                )

            if b"c2pa" in searchable or b"jumbf" in searchable:
                detected_markers = []

                if b"c2pa" in searchable:
                    detected_markers.append("C2PA")

                if b"jumbf" in searchable:
                    detected_markers.append("JUMBF")

                findings.append(
                    f"Content credential marker "
                    f"({', '.join(detected_markers)}) "
                    f"found in metadata: {key}"
                )

    return {
        "format": metadata["format"],
        "width": metadata["width"],
        "height": metadata["height"],
        "mode": metadata["mode"],
        "metadata_keys": metadata["metadata_keys"],
        "findings": findings,
    }


def _inspect_pdf(data: bytes) -> dict:
    text = data.decode("latin-1", errors="ignore")

    markers = [
        marker
        for marker in ("c2pa", "jumbf", "ContentCredentials")
        if marker.lower() in text.lower()
    ]

    return {
        "format": "PDF",
        "pdf_header_valid": data.startswith(b"%PDF-"),
        "page_marker_count": text.count("/Type /Page"),
        "credential_markers": markers,
        "findings": [
            f"PDF credential marker found: {marker}"
            for marker in markers
        ],
    }


def _inspect_media_container(data: bytes, extension: str) -> dict:
    findings = []

    searchable = data.lower()

    markers = [
        marker.decode("ascii")
        for marker in C2PA_MARKERS
        if marker in searchable
    ]

    for marker in markers:
        findings.append(
            f"Embedded content credential marker: {marker}"
        )

    if extension in {".mp4", ".mov"}:
        media_format = "MP4/MOV container"
        valid_header = (
            len(data) >= 12 and data[4:8] == b"ftyp"
        )

    elif extension == ".wav":
        media_format = "WAV"
        valid_header = (
            data.startswith(b"RIFF")
            and data[8:12] == b"WAVE"
        )

    elif extension == ".mp3":
        media_format = "MP3"
        valid_header = (
            data.startswith(b"ID3")
            or (
                len(data) >= 2
                and data[0] == 0xFF
                and (data[1] & 0xE0) == 0xE0
            )
        )

    else:
        media_format = extension.lstrip(".").upper()
        valid_header = None

    return {
        "format": media_format,
        "container_header_valid": valid_header,
        "credential_markers": markers,
        "findings": findings,
    }


def analyze_watermark_file(data: bytes, filename: str) -> dict:
    if not data:
        raise ValueError("Uploaded file is empty.")

    extension = Path(filename).suffix.lower()

    if extension in {".jpg", ".jpeg", ".png", ".webp"}:
        try:
            inspection = _inspect_image(data)
        except Exception as exc:
            raise ValueError(
                f"Unable to inspect image metadata: {exc}"
            ) from exc

    elif extension == ".pdf":
        inspection = _inspect_pdf(data)

    elif extension in {".mp4", ".mov", ".wav", ".mp3"}:
        inspection = _inspect_media_container(data, extension)

    else:
        raise ValueError(
            f"Unsupported watermark inspection format: {extension}"
        )

    findings = inspection.get("findings", [])
    markers = inspection.get("credential_markers", [])

    watermark_detected = bool(findings)

    c2pa_markers_found = bool(
        markers
        or any(
            "c2pa" in item.lower() or "jumbf" in item.lower()
            for item in findings
        )
    )

    return {
        "filename": filename,
        "format": inspection["format"],
        "file_size_bytes": len(data),
        "inspection": inspection,
        "watermarkDetected": watermark_detected,
        "watermarkType": "; ".join(findings) if findings else None,
        "c2paMarkersFound": c2pa_markers_found,
        "c2paSignatureVerification": "not_performed",
        "issuerOrg": None,
        "tamperingVerification": "not_performed",
        "provenanceChain": [],
        "analysis_stage": "metadata_and_container_marker_inspection",
        "limitations": [
            "Only supported metadata fields and known marker strings are inspected.",
            "Invisible watermark decoding is not implemented.",
            "C2PA cryptographic signature verification is not performed.",
            "Marker presence does not establish that a complete or valid C2PA manifest exists.",
            "Absence of supported markers does not prove that a watermark is absent.",
            "File tampering is not verified.",
        ],
    }
