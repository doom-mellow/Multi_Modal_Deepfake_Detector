"""Command-line interface for independent forensic checks and custom training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

from .media import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from .schemes import analyze, selected_schemes
from .train import train_custom


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wmforensics", description="Run independent watermark/provenance forensic pipelines; no fused authenticity score is produced.")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Inspect one image, video, or audio asset")
    inspect.add_argument("asset", type=Path)
    inspect.add_argument("--schemes", nargs="+", choices=("c2pa", "audio", "video", "custom"), help="Independent checks to run (extension-aware defaults if omitted)")
    inspect.add_argument("--custom-checkpoint")
    inspect.add_argument("--audio-card", default="audioseal_detector_16bits")
    inspect.add_argument("--video-card", default="videoseal")
    inspect.add_argument("--frames", type=int, default=8, help="Maximum sampled frames for video analysis")
    inspect.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    inspect.add_argument("--json", action="store_true", help="Emit JSON results only")

    train = commands.add_parser("train-custom", help="Train only the custom binary image watermark detector")
    source = train.add_mutually_exclusive_group(required=True)
    source.add_argument("--train-dir")
    source.add_argument("--train-manifest")
    validation = train.add_mutually_exclusive_group(required=True)
    validation.add_argument("--val-dir")
    validation.add_argument("--val-manifest")
    train.add_argument("--output", default="checkpoints/custom_image.pt")
    train.add_argument("--epochs", type=int, default=15)
    train.add_argument("--batch-size", type=int, default=16)
    train.add_argument("--learning-rate", type=float, default=3e-4)
    train.add_argument("--image-size", type=int, default=224)
    train.add_argument("--width", type=int, default=32)
    train.add_argument("--blocks", type=int, default=3)
    train.add_argument("--workers", type=int, default=0)
    train.add_argument("--seed", type=int, default=17)
    train.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    train.add_argument("--target", default="custom_image_watermark", help="Human-readable target watermark label stored in checkpoint")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "train-custom":
        try:
            metrics = train_custom(
                train_dir=args.train_dir, val_dir=args.val_dir,
                train_manifest=args.train_manifest, val_manifest=args.val_manifest,
                output=args.output, epochs=args.epochs, batch_size=args.batch_size,
                learning_rate=args.learning_rate, image_size=args.image_size,
                width=args.width, blocks=args.blocks, workers=args.workers,
                seed=args.seed, device_name=args.device, target=args.target,
            )
        except Exception as exc:
            print(f"Training failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(metrics, indent=2))
        return 0

    if not args.asset.is_file():
        print(f"Asset does not exist or is not a file: {args.asset}", file=sys.stderr)
        return 2
    if args.frames < 1:
        print("--frames must be positive", file=sys.stderr)
        return 2
    if args.schemes and "audio" in args.schemes and args.asset.suffix.lower() not in AUDIO_EXTENSIONS:
        print("AudioSeal expects a WAV audio asset (PCM WAV is supported by this CLI).", file=sys.stderr)
        return 2
    if args.schemes and "video" in args.schemes and args.asset.suffix.lower() not in VIDEO_EXTENSIONS:
        print("VideoSeal expects a video asset supported by ffmpeg.", file=sys.stderr)
        return 2
    if args.schemes and "custom" in args.schemes and args.asset.suffix.lower() not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
        print("The custom detector supports images and sampled video frames.", file=sys.stderr)
        return 2
    schemes = selected_schemes(args.asset, args.schemes, bool(args.custom_checkpoint))
    results = analyze(args.asset, schemes, torch.device(args.device), args.custom_checkpoint, args.audio_card, args.video_card, args.frames)
    payload = [result.to_dict() for result in results]
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Asset: {args.asset}")
        for result in results:
            print(f"\n[{result.scheme}] {result.status}: {result.summary}")
            for key, value in result.evidence.items():
                print(f"  {key}: {value}")
        print("\nInterpret each scheme's evidence independently; no authenticity verdict is computed.")
    # A detector error is represented in the report but doesn't hide other schemes.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())