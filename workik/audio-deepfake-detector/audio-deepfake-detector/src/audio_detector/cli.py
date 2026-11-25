"""Command-line interface for the audio authenticity baseline."""
from __future__ import annotations

import argparse
import json
import sys

from .model import evaluate, load_model, predict, train_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audio-deepfake", description="Train/evaluate a research audio spoofing classifier")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="Train from a labeled audio manifest CSV")
    train.add_argument("--manifest", required=True)
    train.add_argument("--model", required=True)
    train.add_argument("--max-duration", type=float, default=10.0)
    infer = commands.add_parser("predict", help="Score one audio clip")
    infer.add_argument("--model", required=True)
    infer.add_argument("--audio", required=True)
    infer.add_argument("--max-duration", type=float)
    test = commands.add_parser("evaluate", help="Evaluate on a separate manifest")
    test.add_argument("--model", required=True)
    test.add_argument("--manifest", required=True)
    test.add_argument("--max-duration", type=float)
    args = parser.parse_args(argv)
    try:
        if args.command == "train":
            if args.max_duration <= 0:
                raise ValueError("--max-duration must be positive")
            result = train_model(args.manifest, args.model, args.max_duration)
        elif args.command == "predict":
            result = predict(load_model(args.model), args.audio, args.max_duration)
        else:
            result = evaluate(load_model(args.model), args.manifest, args.max_duration)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
