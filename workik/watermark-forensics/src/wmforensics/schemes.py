"""Lazy scheme-specific forensic adapters; scores are never fused."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch

from .custom_model import load_custom_checkpoint
from .media import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, decode_video_frames, load_image_tensor, pil_to_model_tensor, read_wav_mono
from .types import ForensicResult


def _result(scheme: str, status: str, path: str | Path, summary: str, **evidence: Any) -> ForensicResult:
    return ForensicResult(scheme=scheme, status=status, asset=str(path), summary=summary, evidence=evidence)  # type: ignore[arg-type]


def detect_c2pa(path: str | Path) -> ForensicResult:
    """Inspect and cryptographically validate an embedded C2PA manifest.

    The upstream C2PA Reader integration is limited to image containers here;
    unsupported video/audio containers are rejected by the CLI before dispatch.
    """
    try:
        from c2pa import Reader
    except ImportError:
        return _result("c2pa", "unavailable", path, "Install the optional C2PA integration with watermark-forensics[c2pa].")
    try:
        with Reader(str(path)) as reader:
            manifest_json = reader.json()
            manifest = json.loads(manifest_json) if manifest_json else {}
            active = reader.get_active_manifest() or {}
            state = reader.get_validation_state()
            validation = reader.get_validation_results()
            present = bool(manifest.get("manifests") or active or manifest.get("active_manifest"))
            status = "detected" if present else "not_detected"
            assertions = active.get("assertions", []) if isinstance(active, dict) else []
            return _result(
                "c2pa", status, path,
                "Embedded C2PA manifest found; inspect validation state and assertions." if present else "No embedded C2PA manifest was found; this says nothing about authenticity.",
                manifest_present=present,
                validation_state=state,
                validation_results=validation,
                active_manifest_label=active.get("label") if isinstance(active, dict) else None,
                assertions=[a.get("label") for a in assertions if isinstance(a, dict)],
                c2pa_manifest=manifest,
            )
    except Exception as exc:
        try:
            from c2pa import C2paError
            if isinstance(exc, C2paError.ManifestNotFound):
                return _result("c2pa", "not_detected", path, "No embedded C2PA manifest was found; this says nothing about authenticity.", manifest_present=False)
        except (ImportError, AttributeError):
            pass
        return _result("c2pa", "error", path, "C2PA inspection failed; verify the asset type and C2PA library installation.", error=str(exc))


def detect_audioseal(path: str | Path, device: torch.device, model_card: str = "audioseal_detector_16bits") -> ForensicResult:
    try:
        from audioseal import AudioSeal
    except ImportError:
        return _result("audioseal", "unavailable", path, "Install the optional AudioSeal integration with watermark-forensics[audio].")
    try:
        audio, rate = read_wav_mono(path, target_rate=16_000)
        model = AudioSeal.load_detector(model_card, device=device)
        model.eval()
        with torch.inference_mode():
            probability, message = model.detect_watermark(audio.unsqueeze(0).to(device), sample_rate=rate)
        score = float(probability[0].detach().cpu().item())
        bits = message[0].detach().cpu().to(torch.int32).tolist()
        status = "detected" if score >= 0.5 else "not_detected"
        return _result("audioseal", status, path, "AudioSeal watermark detected." if status == "detected" else "AudioSeal watermark was not detected; this does not establish audio authenticity.", detection_probability=score, threshold=0.5, decoded_message_bits=bits, sample_rate=rate, model_card=model_card)
    except Exception as exc:
        return _result("audioseal", "error", path, "AudioSeal analysis failed; check WAV format, checkpoint availability, and device compatibility.", error=str(exc))


def detect_videoseal(path: str | Path, device: torch.device, model_card: str = "videoseal", frame_count: int = 8) -> ForensicResult:
    try:
        import videoseal
    except ImportError:
        return _result("videoseal", "unavailable", path, "Install the optional VideoSeal integration with watermark-forensics[video].")
    try:
        frames = decode_video_frames(path, count=frame_count)
        model = videoseal.load(model_card).to(device).eval()
        # VideoSeal's official detector accepts batches of RGB frames in [0,1].
        images = torch.stack([pil_to_model_tensor(frame, size=model.img_size) * 0.5 + 0.5 for frame in frames]).to(device)
        with torch.inference_mode():
            prediction = model.detect(images)["preds"]
        # For the official v1.0 card, channel 0 is a spatially constant
        # detection logit (pixelwise=False, sigmoid_output=False). Average its
        # logits per frame, then apply sigmoid for a calibrated probability.
        frame_logits = prediction[:, 0].float()
        if frame_logits.ndim > 1:
            frame_logits = frame_logits.mean(dim=tuple(range(1, frame_logits.ndim)))
        frame_logits = frame_logits.detach().cpu()
        frame_scores = frame_logits.sigmoid()
        scores = [float(value) for value in frame_scores.tolist()]
        average = sum(scores) / len(scores)
        threshold = 0.5
        positive = sum(score >= threshold for score in scores)
        status = "detected" if positive > 0 else "not_detected"
        return _result("videoseal", status, path, "VideoSeal mask exceeded threshold on at least one sampled frame." if status == "detected" else "VideoSeal watermark was not detected in sampled frames; this does not establish video authenticity.", mean_mask_score=average, max_frame_score=max(scores), frame_scores=scores, frames_examined=len(scores), frame_threshold=threshold, model_card=model_card)
    except Exception as exc:
        return _result("videoseal", "error", path, "VideoSeal analysis failed; check ffmpeg, checkpoint availability, and device compatibility.", error=str(exc))


def detect_custom(path: str | Path, checkpoint_path: str | Path, device: torch.device) -> ForensicResult:
    try:
        from PIL import Image
        model, checkpoint = load_custom_checkpoint(str(checkpoint_path), device)
        config = checkpoint["config"]
        size = int(config["image_size"])
        images = [load_image_tensor(path, size=size)] if Path(path).suffix.lower() in IMAGE_EXTENSIONS else [pil_to_model_tensor(frame, size=size) for frame in decode_video_frames(path)]
        batch = torch.stack(images).to(device)
        with torch.inference_mode():
            probabilities = model(batch).sigmoid().detach().cpu()
        frame_scores = [float(p) for p in probabilities.tolist()]
        score = sum(frame_scores) / len(frame_scores)
        threshold = float(checkpoint.get("threshold", 0.5))
        status = "detected" if score >= threshold else "not_detected"
        return _result("custom", status, path, "Custom watermark detector score exceeded its saved validation threshold." if status == "detected" else "Custom watermark detector score stayed below its saved validation threshold; this is not an authenticity determination.", detection_probability=score, threshold=threshold, frame_scores=frame_scores, frames_examined=len(frame_scores), checkpoint=str(checkpoint_path), target=config.get("target", "custom_image_watermark"))
    except Exception as exc:
        return _result("custom", "error", path, "Custom detector analysis failed; check the checkpoint and image/video decoding support.", error=str(exc))


def selected_schemes(path: str | Path, requested: list[str] | None, has_custom: bool) -> list[str]:
    """Choose useful independent pipelines from an asset extension."""
    if requested:
        return list(dict.fromkeys(requested))
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        schemes = ["c2pa"]
        if has_custom:
            schemes.append("custom")
        return schemes
    if ext in VIDEO_EXTENSIONS:
        schemes = ["video"]
        if has_custom:
            schemes.append("custom")
        return schemes
    if ext in AUDIO_EXTENSIONS:
        return ["audio"]
    return []


def analyze(path: str | Path, schemes: list[str], device: torch.device, custom_checkpoint: str | None = None, audio_card: str = "audioseal_detector_16bits", video_card: str = "videoseal", frames: int = 8) -> list[ForensicResult]:
    """Run each requested detector separately and retain per-scheme outcomes."""
    path = Path(path)
    outcomes: list[ForensicResult] = []
    for scheme in schemes:
        if scheme == "c2pa":
            outcomes.append(detect_c2pa(path))
        elif scheme == "audio":
            outcomes.append(detect_audioseal(path, device, audio_card))
        elif scheme == "video":
            outcomes.append(detect_videoseal(path, device, video_card, frames))
        elif scheme == "custom":
            if not custom_checkpoint:
                outcomes.append(_result("custom", "unavailable", path, "Pass --custom-checkpoint with a separately trained custom detector."))
            else:
                outcomes.append(detect_custom(path, custom_checkpoint, device))
        else:
            outcomes.append(_result(scheme, "error", path, "Unknown scheme. Choose c2pa, audio, video, or custom.", allowed_schemes=["c2pa", "audio", "video", "custom"]))
    return outcomes