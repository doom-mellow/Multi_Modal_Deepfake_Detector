# Watermark Forensics

A PyTorch-centered, **scheme-separated** forensic pipeline for investigating watermark signals in media. It combines the official AudioSeal and VideoSeal detectors, C2PA manifest verification, and an independently trainable custom image forensic model. Each detector reports its own evidence; there is deliberately no fused score, since these signals have different meanings, calibration, and failure modes.

> **Scope and limitations.** A watermark detector is not a deepfake detector and cannot prove that content is authentic. A missing watermark is not evidence of manipulation; an embedded or detected watermark is not proof of authorship. C2PA verifies provenance manifests and signatures, not whether depicted events are real. Custom-model scores are experimental, and need representative labeled data, validation, calibration, and human review before operational use. This project does not train official AudioSeal/VideoSeal weights; it provides independent per-scheme scoring and a separate custom-model training/evaluation pipeline.

## Install

Python 3.10+ is recommended. Install the scheme integrations you intend to use:

```bash
python -m pip install -e '.[all,test]'
```

Or install only selected extras, e.g. `-e '.[audio,c2pa]'`. The upstream AudioSeal/VideoSeal detector checkpoints may download on first use; set up network access and review their respective licenses/model cards before use. The C2PA integration uses the official `c2pa-python` reader. The custom training and tests only need core dependencies.

## Run forensic analysis

```bash
wmforensics inspect ./photo.jpg --schemes custom c2pa --json
wmforensics inspect ./clip.mp4 --schemes video --frames 8 --json
wmforensics inspect ./voice.wav --schemes audio --json
```

Omit `--schemes` to select by extension. An unavailable optional integration is reported as unavailable, not silently treated as a negative detection. Override model card names with `--audio-card`, `--video-card`; point `--custom-checkpoint` at your separately trained custom checkpoint. Use `--device cpu` or `--device cuda` as appropriate. C2PA verification is independent of the AudioSeal/VideoSeal scores and can be requested alongside supported images, videos, or audio assets; unsupported containers are reported as a C2PA error.

`custom` accepts images, and video frames when decoded by ffmpeg. Video frame decoding uses the local `ffmpeg` executable. Audio input uses SciPy's WAV reader; supported input should be mono or multichannel PCM WAV (channels are averaged for analysis). AudioSeal's expected sample rate is passed as 16 kHz; WAV audio is resampled when necessary.

Each JSON result includes `scheme`, `status`, and scheme-specific evidence. `detected` means a detector crossed its model threshold; `not_detected` only means it did not. `error` and `unavailable` are intentionally distinct.

## Train the custom forensic model (independently)

Prepare **separate training and validation directories** with the same class subfolders, for example:

```text
data/custom/
  train/
    clean/       # unwatermarked / reference images
    marked/      # images carrying the custom target watermark
  val/
    clean/
    marked/
```

The target is detection of the chosen custom image watermark—not a general deepfake classification task. Include realistic post-processing and diverse clean negatives in your own labeled dataset. Keep sources/groups disjoint across train and validation to reduce leakage. Do not put near-duplicate frames in both splits.

```bash
wmforensics train-custom \
  --train-dir data/custom/train --val-dir data/custom/val \
  --output checkpoints/custom_image.pt --epochs 15 --batch-size 16
```

`train-custom` trains only `CustomImageDetector`, writes the best validation-loss checkpoint, and reports validation loss/accuracy. A checkpoint records the architecture, input resolution, normalization, and selected validation threshold. After training, run `wmforensics inspect image.jpg --schemes custom --custom-checkpoint checkpoints/custom_image.pt`.

The built-in dataset augmentation simulates JPEG re-encoding, blur, resizing, and horizontal flips. Validation images are not augmented. Tune the operating threshold on a held-out set for the costs of false positives and false negatives before deployment; validation accuracy alone is insufficient.

## Custom image dataset manifest (optional)

Alternatively, use JSONL records of the form `{"path":"images/a.jpg","label":1}` and `{"path":"images/b.jpg","label":0}`. Paths are resolved relative to the manifest. Pass one manifest per split to `wmforensics train-custom --train-manifest ... --val-manifest ...`.

## Architecture

- **C2PA:** metadata/provenance only; currently reads images through the official C2PA Reader and reports manifest presence, validation state, and active-manifest assertion summary. No neural training. An absent manifest is `not_detected`, not a forgery conclusion.
- **AudioSeal:** official pretrained scheme-specific audio watermark detector, loaded lazily, returning detection probability and decoded bits when available. It is not merged into another model.
- **VideoSeal:** official pretrained scheme-specific video watermark detector, evaluated frame-by-frame with sampled-frame counts and frame-level mask scores. It is not merged into another model.
- **Custom:** a small independent residual CNN for binary detection of a *specific, defined image watermark*. Train it independently with `train-custom`; it is not a substitute for AudioSeal/VideoSeal and does not detect arbitrary generated-media artifacts.

## Development

```bash
python -m pip install -e '.[test]'
pytest
```

For a quick local smoke test without optional integration installs, train on a small synthetic image folder or call `wmforensics inspect ... --schemes custom` to see the explicit dependency-unavailable result. No pretrained scheme weights are bundled.
